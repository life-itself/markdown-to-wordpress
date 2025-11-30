import { describe, it, expect, beforeAll } from "vitest";
import path from "path";
import { promises as fs, existsSync, readFileSync, readdirSync } from "fs";
import matter from "gray-matter";
import dotenv from "dotenv";
import {
  convertMarkdownToPost,
  createWpClient,
  findPostBySlug,
  upsertPostToWordpress,
} from "../src/lib.js";

// Load test-specific environment variables
const testEnv = dotenv.parse(readFileSync(".env.test"));

const FIXTURE_BLOG_DIR = path.join(process.cwd(), "tests", "fixtures", "e2e-blog");
const fixturePostPaths = existsSync(FIXTURE_BLOG_DIR)
  ? readdirSync(FIXTURE_BLOG_DIR)
      .filter((entry) => entry.endsWith(".md"))
      .map((entry) => path.join(FIXTURE_BLOG_DIR, entry))
  : [];

async function deriveSlug(filePath) {
  const raw = await fs.readFile(filePath, "utf8");
  const { data: frontmatter } = matter(raw);
  return (
    frontmatter.slug ||
    path.basename(filePath, path.extname(filePath))
  );
}

async function removeExistingPosts(client, filePaths) {
  for (const filePath of filePaths) {
    const slug = await deriveSlug(filePath);
    try {
      const existing = await findPostBySlug(client, slug);
      if (existing?.id) {
        await client.posts().id(existing.id).delete({ force: true });
        console.log(`Deleted pre-existing post for slug "${slug}" before test run.`);
      }
    } catch (error) {
      console.warn(`Could not delete pre-existing post for slug "${slug}": ${error.message}`);
    }
  }
}

// Integration tests for uploading to WordPress using the library functions
describe("WordPress Upload Integration", () => {
  let client;

  beforeAll(async () => {
    // Check for environment variables from .env.test
    const { WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD } = testEnv;
    if (!WP_BASE_URL || !WP_USERNAME || !WP_APP_PASSWORD) {
      throw new Error("Missing WordPress environment variables in .env.test.");
    }
    // Create a single client for all tests
    client = createWpClient({
      baseUrl: WP_BASE_URL,
      username: WP_USERNAME,
      appPassword: WP_APP_PASSWORD,
    });

    await removeExistingPosts(client, fixturePostPaths);
  });

  // If no test files were found, create a dummy test to avoid "No tests found" error
  if (fixturePostPaths.length === 0) {
    it("skips tests as no valid test files were found", () => {
      console.warn(
        `No test fixtures found in ${FIXTURE_BLOG_DIR}.`,
      );
      expect(true).toBe(true);
    });
    return;
  }

  it.each(fixturePostPaths)(
    'should upload %s as "publish" and be accessible online',
    async (filePath) => {
      // Read original file, set status to 'publish'
      const originalContent = await fs.readFile(filePath, "utf8");
      const { data: frontmatter, content } = matter(originalContent);
      frontmatter.status = "publish";
      const newContent = matter.stringify(content, frontmatter);

      // Upload using the library functions
      let uploadResponse;
      try {
        const { payload } = await convertMarkdownToPost(newContent, {
          sourcePath: filePath,
        });
        uploadResponse = await upsertPostToWordpress(client, payload);
      } catch (error) {
        console.error("Error during upload:", error);
        throw error;
      }

      expect(uploadResponse).toBeDefined();
      expect(uploadResponse.link).toBeDefined();
      const postUrl = uploadResponse.link;

      // Verify the URL is accessible
      let response;
      try {
        // Add a small delay to allow permalinks to update on the server if needed
        await new Promise((resolve) => setTimeout(resolve, 1000));
        response = await fetch(postUrl);
      } catch (error) {
        throw new Error(
          `Failed to fetch the uploaded post URL (${postUrl}): ${error.message}`,
        );
      }

      expect(
        response.ok,
        `Expected a 2xx response, but got ${response.status} from ${postUrl}`,
      ).toBe(true);
      expect(response.status).toBe(200);
    },
    { timeout: 30000 },
  );
});
