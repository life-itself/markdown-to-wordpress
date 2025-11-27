import {describe, it, expect, beforeAll, afterAll} from 'vitest';
import path from 'node:path';
import {promises as fs, existsSync, readFileSync} from 'node:fs';
import matter from 'gray-matter';
import dotenv from 'dotenv';
import {blogPostPaths} from '../filestotest.js';
import {
  convertMarkdownToPost,
  createWpClient,
  uploadToWordpress
} from '../src/lib.js';

const TEMP_DIR = path.resolve('tests/temp');

// Load test-specific environment variables
const testEnv = dotenv.parse(readFileSync('.env.test'));

// Filter the list of posts to only include files that actually exist.
const existingPostPaths = blogPostPaths.filter(filePath => {
  const fullPath = path.join('next.lifeitself.org', filePath);
  const exists = existsSync(fullPath);
  if (!exists) {
    console.warn(`Warning: Test file not found, skipping: ${filePath}`);
  }
  return exists;
});

// Integration tests for uploading to WordPress using the library functions
describe('WordPress Upload Integration', () => {
  let client;

  beforeAll(async () => {
    // Check for environment variables from .env.test
    const {WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD} = testEnv;
    if (!WP_BASE_URL || !WP_USERNAME || !WP_APP_PASSWORD) {
      throw new Error(
        'Missing WordPress environment variables in .env.test.'
      );
    }
    // Create a single client for all tests
    client = createWpClient({
      baseUrl: WP_BASE_URL,
      username: WP_USERNAME,
      appPassword: WP_APP_PASSWORD
    });
    // Create a temporary directory for modified test files
    await fs.mkdir(TEMP_DIR, {recursive: true});
  });

  afterAll(async () => {
    // Clean up the temporary directory
    await fs.rm(TEMP_DIR, {recursive: true, force: true});
  });

  // If no test files were found, create a dummy test to avoid "No tests found" error
  if (existingPostPaths.length === 0) {
    it('skips tests as no valid test files were found', () => {
      console.warn('All specified test files in filestotest.js were not found.');
      expect(true).toBe(true);
    });
    return;
  }

  it.each(existingPostPaths)('should upload %s as "publish" and be accessible online', async (filePath) => {
    const originalPath = path.join('next.lifeitself.org', filePath);
    const tempPath = path.join(TEMP_DIR, path.basename(filePath));

    // Read original file, set status to 'publish', and write to temp file
    const originalContent = await fs.readFile(originalPath, 'utf8');
    const {data: frontmatter, content} = matter(originalContent);
    frontmatter.status = 'publish';
    const newContent = matter.stringify(content, frontmatter);
    await fs.writeFile(tempPath, newContent);

    // Upload using the library functions
    let uploadResponse;
    try {
      const {payload} = await convertMarkdownToPost(tempPath);
      uploadResponse = await uploadToWordpress(client, payload);
    } catch (error) {
      console.error('Error during upload:', error);
      throw error;
    }

    expect(uploadResponse).toBeDefined();
    expect(uploadResponse.link).toBeDefined();
    const postUrl = uploadResponse.link;

    // Verify the URL is accessible
    let response;
    try {
      // Add a small delay to allow permalinks to update on the server if needed
      await new Promise(resolve => setTimeout(resolve, 1000));
      response = await fetch(postUrl);
    } catch (error) {
      throw new Error(`Failed to fetch the uploaded post URL (${postUrl}): ${error.message}`);
    }

    expect(response.ok, `Expected a 2xx response, but got ${response.status} from ${postUrl}`).toBe(true);
    expect(response.status).toBe(200);
  }, {timeout: 30000});
});
