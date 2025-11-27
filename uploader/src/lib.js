import path from "node:path";
import matter from "gray-matter";
import { remark } from "remark";
import remarkGfm from "remark-gfm";
import remarkHtml from "remark-html";
import WPAPI from "wpapi";

const REQUIRED_FIELDS = ["title"];

function assertFrontmatter(frontmatter) {
  const missing = REQUIRED_FIELDS.filter((field) => !frontmatter[field]);
  if (missing.length > 0) {
    throw new Error(
      `Missing required front matter fields: ${missing.join(", ")}`,
    );
  }
}

export function normalizeTags(raw) {
  if (!raw) return undefined;
  if (Array.isArray(raw)) {
    const values = raw
      .map((value) => (typeof value === "string" ? value.trim() : value))
      .filter(Boolean);
    return values.length > 0 ? values : undefined;
  }
  if (typeof raw === "string") {
    const value = raw.trim();
    return value ? [value] : undefined;
  }
  return undefined;
}

export async function convertMarkdownToPost(markdownInput, options = {}) {
  if (typeof markdownInput !== "string" && !Buffer.isBuffer(markdownInput)) {
    throw new Error(
      "convertMarkdownToPost expects a string or Buffer of markdown content.",
    );
  }

  const raw =
    typeof markdownInput === "string"
      ? markdownInput
      : markdownInput.toString("utf8");
  const sourcePath = options.sourcePath
    ? path.resolve(options.sourcePath)
    : undefined;
  const { data: frontmatter, content } = matter(raw);
  assertFrontmatter(frontmatter);

  const processed = await remark()
    .use(remarkGfm)
    .use(remarkHtml)
    .process(content);
  const htmlContent = String(processed).trim();

  // Derive slug from filename if not provided in frontmatter
  const slug =
    frontmatter.slug ||
    (sourcePath
      ? path.basename(sourcePath, path.extname(sourcePath))
      : undefined);

  if (!slug) {
    throw new Error(
      "Slug must be provided in front matter or via options.sourcePath.",
    );
  }

  const metaFromFrontmatter =
    frontmatter.meta && typeof frontmatter.meta === "object"
      ? frontmatter.meta
      : undefined;

  const payload = {
    title: frontmatter.title,
    content: htmlContent,
    status: frontmatter.status || "draft",
    slug: slug, // Always include slug in payload for idempotent uploads
    meta: {
      ...(metaFromFrontmatter || {}),
      raw_markdown: raw,
    },
  };

  if (frontmatter.date) payload.date = frontmatter.date;
  if (frontmatter.excerpt) payload.excerpt = frontmatter.excerpt;
  const tags = normalizeTags(frontmatter.tags);
  if (tags) payload.tags = tags;

  return {
    payload,
    frontmatter,
    htmlContent,
  };
}

function sanitizeBaseUrl(url) {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export function createWpClient({ baseUrl, username, appPassword }) {
  if (!baseUrl || !username || !appPassword) {
    throw new Error(
      "Missing WordPress credentials (WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD).",
    );
  }

  const endpoint = `${sanitizeBaseUrl(baseUrl)}/wp-json`;
  return new WPAPI({
    endpoint,
    username,
    password: appPassword,
  });
}

export async function findPostBySlug(client, slug) {
  const response = await client.posts().slug(slug).get();
  return response.length > 0 ? response[0] : null;
}

export async function upsertPostToWordpress(client, payload) {
  if (!client) throw new Error("A configured WPAPI client is required.");
  if (!payload) throw new Error("No payload provided to upload.");
  if (!payload.slug)
    throw new Error("Payload must contain a slug for idempotent upload.");

  const existingPost = await findPostBySlug(client, payload.slug);

  if (existingPost) {
    // Update existing post
    // Make sure to include the ID for updates
    return client.posts().id(existingPost.id).update(payload);
  } else {
    // Create new post, ensuring slug is explicitly set
    return client.posts().create(payload);
  }
}
