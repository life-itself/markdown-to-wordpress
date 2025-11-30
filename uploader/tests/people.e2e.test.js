import { describe, it, expect, beforeAll, afterAll } from "vitest";
import path from "node:path";
import { readFileSync, promises as fs } from "node:fs";
import dotenv from "dotenv";
import matter from "gray-matter";
import { createWpClient } from "../src/lib.js";
import {
  convertMarkdownToTeamMember,
  deleteTeamMember,
  findTeamMemberBySlug,
  upsertTeamMember,
} from "../src/people.js";

const testEnv = dotenv.parse(readFileSync(".env.test"));
const fixturePath = path.join(process.cwd(), "tests", "fixtures", "person.md");

describe("Team upload integration", () => {
  let client;
  let createdId = null;
  let slug = null;

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

  afterAll(async () => {
    if (client && createdId) {
      try {
        await deleteTeamMember(client, createdId);
      } catch (error) {
        console.warn(
          `Failed to delete test team member ${createdId}: ${error.message}`,
        );
      }
    }
  });

  it(
    "uploads and updates a team member entry",
    async () => {
      const raw = await fs.readFile(fixturePath, "utf8");
      const parsed = matter(raw);
      parsed.data.status = "publish";
      const updatedRaw = matter.stringify(parsed.content, parsed.data);

      const { payload } = await convertMarkdownToTeamMember(updatedRaw, {
        sourcePath: fixturePath,
      });
      slug = payload.slug;

      const firstUpload = await upsertTeamMember(client, payload, {
        override: true,
      });
      expect(firstUpload.result).toBeDefined();
      expect(firstUpload.result.slug).toBe(slug);
      createdId = firstUpload.result.id;

      const secondUpload = await upsertTeamMember(client, payload, {
        override: true,
      });
      expect(secondUpload.action).toBe("updated");
      expect(secondUpload.result.id).toBe(createdId);

      const fetched = await findTeamMemberBySlug(client, slug);
      expect(fetched).toBeTruthy();
      expect(fetched.id).toBe(createdId);
    },
    { timeout: 30000 },
  );
});
