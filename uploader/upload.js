import 'dotenv/config';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import matter from 'gray-matter';
import {remark} from 'remark';
import remarkGfm from 'remark-gfm';
import remarkHtml from 'remark-html';
import WPAPI from 'wpapi';

const REQUIRED_FIELDS = ['title'];

function assertFrontmatter(frontmatter) {
  const missing = REQUIRED_FIELDS.filter((field) => !frontmatter[field]);
  if (missing.length > 0) {
    throw new Error(`Missing required front matter fields: ${missing.join(', ')}`);
  }
}

export function normalizeTags(raw) {
  if (!raw) return undefined;
  if (Array.isArray(raw)) {
    const values = raw.map((value) => (typeof value === 'string' ? value.trim() : value)).filter(Boolean);
    return values.length > 0 ? values : undefined;
  }
  if (typeof raw === 'string') {
    const value = raw.trim();
    return value ? [value] : undefined;
  }
  return undefined;
}

export async function convertMarkdownToPost(filePath) {
  const absolutePath = path.resolve(filePath);
  const raw = await readFile(absolutePath, 'utf8');
  const {data: frontmatter, content} = matter(raw);
  assertFrontmatter(frontmatter);

  const processed = await remark().use(remarkGfm).use(remarkHtml).process(content);
  const htmlContent = String(processed).trim();

  const payload = {
    title: frontmatter.title,
    content: htmlContent,
    status: frontmatter.status || 'draft'
  };

  if (frontmatter.slug) payload.slug = frontmatter.slug;
  if (frontmatter.date) payload.date = frontmatter.date;
  if (frontmatter.excerpt) payload.excerpt = frontmatter.excerpt;
  const tags = normalizeTags(frontmatter.tags);
  if (tags) payload.tags = tags;

  return {
    payload,
    frontmatter,
    htmlContent
  };
}

function sanitizeBaseUrl(url) {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

export function createWpClient({baseUrl, username, appPassword}) {
  if (!baseUrl || !username || !appPassword) {
    throw new Error('Missing WordPress credentials (WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD).');
  }

  const endpoint = `${sanitizeBaseUrl(baseUrl)}/wp-json`;
  return new WPAPI({
    endpoint,
    username,
    password: appPassword
  });
}

export async function uploadToWordpress(client, payload) {
  if (!client) throw new Error('A configured WPAPI client is required.');
  if (!payload) throw new Error('No payload provided to upload.');
  return client.posts().create(payload);
}

export async function main(markdownPath = path.resolve('sample-post.md')) {
  const {payload} = await convertMarkdownToPost(markdownPath);

  const client = createWpClient({
    baseUrl: process.env.WP_BASE_URL,
    username: process.env.WP_USERNAME,
    appPassword: process.env.WP_APP_PASSWORD
  });

  const response = await uploadToWordpress(client, payload);
  console.log('Post uploaded successfully:', {
    id: response?.id,
    link: response?.link,
    status: response?.status
  });
  return response;
}

function isDirectExecution() {
  const entry = process.argv[1];
  if (!entry) return false;
  return import.meta.url === pathToFileURL(entry).href;
}

if (isDirectExecution()) {
  main().catch((error) => {
    console.error('Failed to upload post:', error.message);
    process.exit(1);
  });
}
