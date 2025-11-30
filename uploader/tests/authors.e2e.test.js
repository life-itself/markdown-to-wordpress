import { describe, it, expect, beforeAll } from "vitest";
import path from "node:path";
import { readFileSync } from "node:fs";
import dotenv from "dotenv";
import {
  createWpClient,
  findPostBySlug,
  upsertPostToWordpress,
  prepareWordpressPayload,
} from "../src/lib.js";

// Borrow the same env-loading approach as other e2e tests
const testEnv = dotenv.parse(readFileSync(".env.test"));

const authorsFixturePath = path.join(
  process.cwd(),
  "tests",
  "fixtures",
  "authors.json",
);
const AUTHORS_MAP = JSON.parse(readFileSync(authorsFixturePath, "utf8"));

// Snapshot of known author IDs from investigate-api-for-pods.js output
const MOCK_AUTHORS = [
  { id: 103, name: "Rufus Pollock" },
  { id: 107, name: "Sylvie Barbier" },
];

describe("WordPress author relationship", () => {
  let client;

  beforeAll(() => {
    const { WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD } = testEnv;
    if (!WP_BASE_URL || !WP_USERNAME || !WP_APP_PASSWORD) {
      throw new Error("Missing WordPress environment variables in .env.test.");
    }

    client = createWpClient({
      baseUrl: WP_BASE_URL,
      username: WP_USERNAME,
      appPassword: WP_APP_PASSWORD,
    });
  });

  it("creates or updates a post with the custom authors array set", async () => {
    const slug = "wpapi-author-e2e-test";
    const basePayload = {
      title: "Author E2E test post",
      content: "<p>Testing the Pods-driven authors relationship via REST.</p>",
      status: "publish",
      slug,
      // Pass names and rely on the mapping layer to resolve IDs.
      authors: ["rufuspollock", "sylvieshiweibarbier"],
      // Keep meta present so the post mirrors our usual upload shape.
      meta: {
        raw_markdown:
          "Author test placeholder content; real markdown lives elsewhere.",
      },
    };

    const payload = prepareWordpressPayload(basePayload, {
      authorsMap: AUTHORS_MAP,
      logger: console,
    });

    const created = await upsertPostToWordpress(client, payload);
    expect(created).toBeDefined();
    expect(created.slug).toBe(slug);

    const fetched = await findPostBySlug(client, slug);
    expect(fetched).toBeTruthy();

    const authorIds =
      Array.isArray(fetched.authors) && fetched.authors.length > 0
        ? fetched.authors
            .map((author) =>
              typeof author === "number"
                ? author
                : Number(author?.id ?? author?.ID),
            )
            .filter(Boolean)
        : [];

    expect(authorIds).toEqual(
      expect.arrayContaining(MOCK_AUTHORS.map((author) => author.id)),
    );
  }, 30000);
});
