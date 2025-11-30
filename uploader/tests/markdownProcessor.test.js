import { describe, expect, it, vi, beforeEach } from "vitest";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  convertMarkdownToPost,
  normalizeTags,
  findPostBySlug,
  upsertPostToWordpress,
  prepareWordpressPayload,
} from "../src/lib.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const fixturesDir = path.join(__dirname, "fixtures");
const mediaMapPath = path.join(fixturesDir, "uploadMediaMap.json");
const authorsMapPath = path.join(fixturesDir, "authors.json");

describe("convertMarkdownToPost", () => {
  it("parses front matter and converts markdown to HTML with gfm support", async () => {
    const fixturePath = path.join(fixturesDir, "post.md");
    const raw = await readFile(fixturePath, "utf8");
    const { payload, htmlContent } = await convertMarkdownToPost(raw, {
      sourcePath: fixturePath,
    });

    expect(payload).toMatchObject({
      title: "Fixture Title",
      status: "publish",
      slug: "fixture-title",
      excerpt: expect.stringContaining("Quick summary"),
    });
    expect(htmlContent).toContain("<strong>");
    expect(htmlContent).toContain("<sup");
    expect(payload.meta.raw_markdown).toBe(raw);
  });

  it("applies sensible defaults when optional fields are missing", async () => {
    const fixturePath = path.join(fixturesDir, "minimal.md");
    const raw = await readFile(fixturePath, "utf8");
    const { payload } = await convertMarkdownToPost(raw, {
      sourcePath: fixturePath,
    });

    expect(payload.status).toBe("draft");
    expect(payload.slug).toBe("minimal"); // Slug derived from filename
    expect(payload.meta.raw_markdown).toBe(raw);
  });

  it("rewrites media references and sets featured image from front matter when available", async () => {
    const fixturePath = path.join(fixturesDir, "image-frontmatter.md");
    const raw = await readFile(fixturePath, "utf8");
    const mediaMap = JSON.parse(await readFile(mediaMapPath, "utf8"));

    const { payload, htmlContent, frontmatter } = await convertMarkdownToPost(
      raw,
      {
        sourcePath: fixturePath,
        mediaMap,
      },
    );

    expect(frontmatter.image).toBe("/wp-content/uploads/featured-hero.jpg");
    expect(payload.featured_media).toBe(101);
    expect(payload.content).toContain('src="/wp-content/uploads/body-image.png"');
    expect(payload.content).toContain(
      'src="/wp-content/uploads/inline-note.jpg"',
    );
    expect(payload.content).toContain(
      'src="/wp-content/uploads/html-picture.svg"',
    );
    expect(payload.content).toContain('href="/wp-content/uploads/report.pdf"');
    expect(htmlContent).not.toContain("example.com");
  });

  it("uses the first body image as featured media when front matter is missing", async () => {
    const fixturePath = path.join(fixturesDir, "image-body.md");
    const raw = await readFile(fixturePath, "utf8");
    const mediaMap = JSON.parse(await readFile(mediaMapPath, "utf8"));

    const { payload } = await convertMarkdownToPost(raw, {
      sourcePath: fixturePath,
      mediaMap,
    });

    expect(payload.featured_media).toBe(909);
    expect(payload.content).toContain('src="/wp-content/uploads/second-body.jpg"');
    expect(payload.content).toContain('href="/wp-content/uploads/report.pdf"');
  });

  it("converts obsidian PDF embeds into download links", async () => {
    const fixturePath = path.join(fixturesDir, "obsidian-pdf.md");
    const raw = await readFile(fixturePath, "utf8");
    const mediaMap = JSON.parse(await readFile(mediaMapPath, "utf8"));

    const { payload } = await convertMarkdownToPost(raw, {
      sourcePath: fixturePath,
      mediaMap,
    });

    expect(payload.content).toContain('href="/wp-content/uploads/report.pdf"');
    expect(payload.content).toContain(">Download PDF<");
    expect(payload.content).not.toContain("<img");
  });

  it("prefers front matter date when present", async () => {
    const markdown = `---
title: Has Date
date: 2024-03-15
---

Body`;

    const { payload } = await convertMarkdownToPost(markdown, {
      sourcePath: path.join(fixturesDir, "date-primary.md"),
    });

    expect(new Date(payload.date).toISOString()).toBe(
      "2024-03-15T00:00:00.000Z",
    );
  });

  it("falls back to created when date is absent", async () => {
    const markdown = `---
title: Created Only
created: 2020-12-31
---

Body`;

    const { payload } = await convertMarkdownToPost(markdown, {
      sourcePath: path.join(fixturesDir, "created-fallback.md"),
    });

    expect(new Date(payload.date).toISOString()).toBe(
      "2020-12-31T00:00:00.000Z",
    );
  });

  it("leaves date undefined when both date and created are missing", async () => {
    const markdown = `---
title: No Date Fields
---

Body`;

    const { payload } = await convertMarkdownToPost(markdown, {
      sourcePath: path.join(fixturesDir, "no-dates.md"),
    });

    expect(payload.date).toBeUndefined();
  });

  it("collects authors from author/authors front matter", async () => {
    const markdown = `---
title: Authors Test
author: primary-author
authors:
  - co-author
  - primary-author
---

Body`;

    const { payload } = await convertMarkdownToPost(markdown, {
      sourcePath: path.join(fixturesDir, "authors-test.md"),
    });

    expect(payload.authors).toEqual(["primary-author", "co-author"]);
  });
});

describe("prepareWordpressPayload", () => {
  it("maps author names to WordPress IDs and deduplicates", async () => {
    const authorsMap = JSON.parse(await readFile(authorsMapPath, "utf8"));
    const logger = { warn: vi.fn() };
    const payload = {
      title: "Mapped Authors",
      content: "...",
      slug: "mapped-authors",
      authors: ["rufuspollock", "sylvieshiweibarbier", "rufuspollock"],
    };

    const result = prepareWordpressPayload(payload, { authorsMap, logger });

    expect(result.authors).toEqual([103, 107]);
    expect(logger.warn).not.toHaveBeenCalled();
  });

  it("warns and strips authors that lack a wordpress_id", async () => {
    const authorsMap = JSON.parse(await readFile(authorsMapPath, "utf8"));
    const logger = { warn: vi.fn() };
    const payload = {
      title: "Missing Author",
      content: "...",
      slug: "missing-author",
      authors: ["unknown-on-wp"],
    };

    const result = prepareWordpressPayload(payload, { authorsMap, logger });

    expect(result.authors).toBeUndefined();
    expect(logger.warn).toHaveBeenCalledWith(
      expect.stringContaining("unknown-on-wp"),
    );
  });
});

describe("normalizeTags", () => {
  it("normalizes string inputs to arrays", () => {
    expect(normalizeTags("alpha")).toEqual(["alpha"]);
  });

  it("returns undefined when tags are missing or empty", () => {
    expect(normalizeTags(undefined)).toBeUndefined();
    expect(normalizeTags([])).toBeUndefined();
  });
});

describe("upsertPostToWordpress", () => {
  let mockWpClient;
  let mockPostsChain;

  beforeEach(() => {
    mockPostsChain = {
      slug: vi.fn(() => mockPostsChain),
      get: vi.fn(),
      id: vi.fn(() => mockPostsChain),
      update: vi.fn(),
      create: vi.fn(),
    };
    mockWpClient = {
      posts: vi.fn(() => mockPostsChain),
    };
  });

  it("should create a new post if no post with the slug exists", async () => {
    mockPostsChain.get.mockResolvedValue([]); // No existing post
    mockPostsChain.create.mockResolvedValue({ id: 1, link: "new-post-link" });

    const payload = { title: "New Post", content: "...", slug: "new-post" };
    const result = await upsertPostToWordpress(mockWpClient, payload);

    expect(mockPostsChain.get).toHaveBeenCalledWith(); // Called by slug().get()
    expect(mockPostsChain.slug).toHaveBeenCalledWith(payload.slug);
    expect(mockPostsChain.create).toHaveBeenCalled();
    expect(mockPostsChain.update).not.toHaveBeenCalled();
    expect(result).toEqual({ id: 1, link: "new-post-link" });

    const createCallPayload = mockPostsChain.create.mock.calls[0][0];
    expect(createCallPayload.date).toEqual(expect.any(String));
    expect(Date.parse(createCallPayload.date)).not.toBeNaN();
  });

  it("should update an existing post if a post with the slug is found", async () => {
    const existingPost = { id: 123, title: "Old Post", slug: "existing-post" };
    mockPostsChain.get.mockResolvedValue([existingPost]); // Existing post found
    mockPostsChain.update.mockResolvedValue({
      id: 123,
      link: "updated-post-link",
    });

    const payload = {
      title: "Updated Post",
      content: "...",
      slug: "existing-post",
    };
    const result = await upsertPostToWordpress(mockWpClient, payload);

    expect(mockPostsChain.get).toHaveBeenCalledWith();
    expect(mockPostsChain.slug).toHaveBeenCalledWith(payload.slug);
    expect(mockPostsChain.id).toHaveBeenCalledWith(existingPost.id);
    expect(mockPostsChain.update).toHaveBeenCalled();
    expect(mockPostsChain.create).not.toHaveBeenCalled();
    expect(result).toEqual({ id: 123, link: "updated-post-link" });

    const updateCallPayload = mockPostsChain.update.mock.calls[0][0];
    expect(updateCallPayload.date).toEqual(expect.any(String));
    expect(Date.parse(updateCallPayload.date)).not.toBeNaN();
  });

  it("should throw an error if payload is missing slug", async () => {
    const payload = { title: "New Post", content: "..." }; // Missing slug
    await expect(upsertPostToWordpress(mockWpClient, payload)).rejects.toThrow(
      "Payload must contain a slug for idempotent upload.",
    );
  });

  it("should respect a provided date on the payload", async () => {
    const existingPost = { id: 555, title: "Old Post", slug: "dated-post" };
    mockPostsChain.get.mockResolvedValue([existingPost]);
    const payload = {
      title: "Has Date",
      content: "...",
      slug: "dated-post",
      date: "2021-01-01T12:00:00Z",
    };

    await upsertPostToWordpress(mockWpClient, payload);

    const updateCallPayload = mockPostsChain.update.mock.calls[0][0];
    expect(updateCallPayload.date).toBe(payload.date);
  });
});
