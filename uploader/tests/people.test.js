import { describe, it, expect } from "vitest";
import path from "node:path";
import { readFileSync } from "node:fs";
import {
  convertMarkdownToTeamMember,
  upsertTeamMember,
  updateAuthorsRecord,
} from "../src/people.js";

function createMockTeamClient(initialEntries = []) {
  const store = initialEntries.map((entry, index) => ({
    id: entry.id ?? index + 1,
    slug: entry.slug,
    title: { rendered: entry.title },
    ...entry,
  }));

  const routeFactory = () => {
    const state = {
      slug: null,
      search: null,
      page: 1,
      per_page: null,
      id: null,
    };

    return {
      slug(value) {
        state.slug = value;
        return this;
      },
      param(key, value) {
        state[key] = value;
        return this;
      },
      id(value) {
        state.id = value;
        return this;
      },
      async get() {
        let results = [...store];
        if (state.slug) {
          results = results.filter((entry) => entry.slug === state.slug);
        }
        if (state.search) {
          const term = state.search.toLowerCase();
          results = results.filter((entry) =>
            (entry.title?.rendered || "").toLowerCase().includes(term),
          );
        }

        const perPage = state.per_page || results.length;
        const start = ((state.page || 1) - 1) * perPage;
        return results.slice(start, start + perPage);
      },
      async create(payload) {
        const entry = {
          id: payload.id || store.length + 1,
          slug: payload.slug,
          title: { rendered: payload.title },
          ...payload,
        };
        store.push(entry);
        return entry;
      },
      async update(payload) {
        const index = store.findIndex((entry) => entry.id === state.id);
        if (index === -1) throw new Error(`Entry ${state.id} not found`);
        const updated = {
          ...store[index],
          ...payload,
          title: { rendered: payload.title ?? store[index].title?.rendered },
        };
        store[index] = updated;
        return updated;
      },
      async delete() {
        return null;
      },
    };
  };

  return {
    team: routeFactory,
  };
}

describe("convertMarkdownToTeamMember", () => {
  const mediaMap = JSON.parse(
    readFileSync(
      path.join(process.cwd(), "tests", "fixtures", "uploadMediaMap.json"),
      "utf8",
    ),
  );

  it("converts people markdown to a team payload with slug from id", async () => {
    const md = `---\nid: alexia\nname: Alexia Netcu\n---\nHello **team**!`;
    const { payload, slug } = await convertMarkdownToTeamMember(md, {
      sourcePath: "/tmp/people/alexia.md",
    });

    expect(slug).toBe("alexia");
    expect(payload.title).toBe("Alexia Netcu");
    expect(payload.status).toBe("publish");
    expect(payload.content).toContain("<strong>team</strong>");
  });

  it("derives slug from filename when not provided", async () => {
    const md = `---\nname: Jane Doe\n---\nBio`;
    const { payload } = await convertMarkdownToTeamMember(md, {
      sourcePath: "/tmp/people/jane-doe.md",
    });

    expect(payload.slug).toBe("jane-doe");
  });

  it("throws if name is missing", async () => {
    const md = `---\nid: missing-name\n---\nNo name`;
    await expect(convertMarkdownToTeamMember(md)).rejects.toThrow(/name/);
  });

  it("sets featured_media and avatar meta using media map", async () => {
    const md = `---\nid: avatar-person\nname: Avatar Person\navatar: /images/featured-hero.jpg\n---\nBio`;
    const { payload } = await convertMarkdownToTeamMember(md, {
      sourcePath: "/tmp/people/avatar-person.md",
      mediaMap,
    });

    expect(payload.featured_media).toBe(101);
    expect(payload.meta.avatar_url).toBe("/wp-content/uploads/featured-hero.jpg");
    expect(payload.meta.featured_image_url).toBe("/wp-content/uploads/featured-hero.jpg");
  });
});

describe("updateAuthorsRecord", () => {
  it("adds wordpress info to authors map", () => {
    const authors = {};
    const payload = { slug: "new-person", title: "New Person" };
    const result = { id: 999, title: { rendered: "New Person" } };

    const updated = updateAuthorsRecord(authors, payload, result);

    expect(updated["new-person"].wordpress_id).toBe(999);
    expect(updated["new-person"].wordpress_name).toBe("New Person");
    expect(updated["new-person"].name).toBe("New Person");
    expect(updated["new-person"].exists_local).toBe(true);
  });

  it("preserves existing fields when updating authors map", () => {
    const authors = {
      "new-person": { posts_count: 3, pages_count: 1 },
    };
    const payload = { slug: "new-person", title: "New Person" };
    const result = { id: 1000, title: { rendered: "New Person" } };

    const updated = updateAuthorsRecord(authors, payload, result);
    expect(updated["new-person"].posts_count).toBe(3);
    expect(updated["new-person"].wordpress_id).toBe(1000);
  });
});

describe("upsertTeamMember", () => {
  it("creates a new team member when slug not present", async () => {
    const client = createMockTeamClient();
    const payload = {
      title: "New Person",
      slug: "new-person",
      content: "<p>hello</p>",
      status: "publish",
    };

    const { result, action } = await upsertTeamMember(client, payload, {
      override: false,
    });

    expect(action).toBe("created");
    expect(result.slug).toBe("new-person");
  });

  it("skips duplicate names unless override is true", async () => {
    const client = createMockTeamClient([
      { id: 2, slug: "alexia", title: "Alexia Netcu" },
    ]);
    const payload = {
      title: "Alexia Netcu",
      slug: "alexia",
      content: "<p>hi</p>",
      status: "publish",
    };

    const skipped = await upsertTeamMember(client, payload, { override: false });
    expect(skipped.action).toBe("skipped");
    expect(skipped.result.id).toBe(2);

    const { action, result } = await upsertTeamMember(client, payload, {
      override: true,
    });
    expect(action).toBe("updated");
    expect(result.id).toBe(2);
  });
});
