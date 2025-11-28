import path from "node:path";
import matter from "gray-matter";
import { remark } from "remark";
import remarkGfm from "remark-gfm";
import remarkHtml from "remark-html";
import WPAPI from "wpapi";

const REQUIRED_FIELDS = ["title"];
const SUPPORTED_MEDIA_EXTENSIONS = new Set([
  "jpg",
  "jpeg",
  "png",
  "gif",
  "svg",
  "webp",
  "bmp",
  "tif",
  "tiff",
  "avif",
  "heic",
  "heif",
  "pdf",
]);

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

function isRemoteUrl(value) {
  return /^https?:\/\//i.test(value) || value.startsWith("//");
}

function stripQueryAndHash(value) {
  return value.split("#")[0].split("?")[0];
}

function hasSupportedMediaExtension(value) {
  if (!value) return false;
  const clean = stripQueryAndHash(value);
  const ext = path.extname(clean).toLowerCase().replace(/^\./, "");
  return SUPPORTED_MEDIA_EXTENSIONS.has(ext);
}

function normalizeUrlForOutput(url, useRelativeUrls) {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return useRelativeUrls ? parsed.pathname : parsed.toString();
  } catch {
    return url;
  }
}

function resolveMediaReference(reference, mediaMap, useRelativeUrls) {
  if (!mediaMap || !reference || isRemoteUrl(reference)) return null;
  if (!hasSupportedMediaExtension(reference)) return null;
  const key = path.basename(stripQueryAndHash(reference));
  const mapping = mediaMap[key];
  if (!mapping || !mapping.url) return null;
  return {
    url: normalizeUrlForOutput(mapping.url, useRelativeUrls),
    id: mapping.id,
  };
}

function rewriteFrontmatterImage(frontmatter, mediaMap, useRelativeUrls) {
  if (!frontmatter || typeof frontmatter.image !== "string") return null;
  const resolved = resolveMediaReference(
    frontmatter.image,
    mediaMap,
    useRelativeUrls,
  );
  if (resolved?.url) {
    frontmatter.image = resolved.url;
    return resolved;
  }
  return null;
}

function rewriteMarkdownAndObsidianMedia(
  markdown,
  mediaMap,
  useRelativeUrls,
  featuredRef,
) {
  if (!mediaMap) return markdown;
  let content = markdown;

  content = content.replace(/!\[\[([^\]]+)\]\]/g, (match, inner) => {
    const [targetRaw, altRaw] = inner.split("|");
    const target = targetRaw?.trim();
    if (!target) return match;
    const resolved = resolveMediaReference(target, mediaMap, useRelativeUrls);
    if (!resolved) return match;
    if (!featuredRef.value) featuredRef.value = resolved;
    const alt = altRaw ? altRaw.trim() : "";
    return `![${alt}](${resolved.url})`;
  });

  content = content.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (match, alt, target) => {
      const resolved = resolveMediaReference(target, mediaMap, useRelativeUrls);
      if (!resolved) return match;
      if (!featuredRef.value) featuredRef.value = resolved;
      return `![${alt}](${resolved.url})`;
    },
  );

  content = content.replace(
    /(?<!!)\[([^\]]+)\]\(([^)]+)\)/g,
    (match, label, target) => {
      const resolved = resolveMediaReference(target, mediaMap, useRelativeUrls);
      if (!resolved) return match;
      return `[${label}](${resolved.url})`;
    },
  );

  return content;
}

function rewriteHtmlMedia(html, mediaMap, useRelativeUrls, featuredRef) {
  if (!mediaMap) return html;
  return html.replace(
    /<(img|a)\b[^>]*?\s(src|href)\s*=\s*("([^"]+)"|'([^']+)')[^>]*?>/gi,
    (match, tag, attr, _full, doubleQuoted, singleQuoted) => {
      const original = doubleQuoted || singleQuoted;
      const resolved = resolveMediaReference(
        original,
        mediaMap,
        useRelativeUrls,
      );
      if (!resolved) return match;
      if (!featuredRef.value && tag.toLowerCase() === "img") {
        featuredRef.value = resolved;
      }
      return match.replace(original, resolved.url);
    },
  );
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
  const mediaMap = options.mediaMap;
  const useRelativeUrls =
    options.useRelativeUrls === undefined ? true : options.useRelativeUrls;

  const featuredRef = { value: null };

  const frontmatterFeatured = rewriteFrontmatterImage(
    frontmatter,
    mediaMap,
    useRelativeUrls,
  );
  if (frontmatterFeatured) {
    featuredRef.value = frontmatterFeatured;
  }

  const rewrittenContent = rewriteMarkdownAndObsidianMedia(
    content,
    mediaMap,
    useRelativeUrls,
    featuredRef,
  );

  const processed = await remark()
    .use(remarkGfm)
    .use(remarkHtml, { sanitize: false })
    .process(rewrittenContent);
  const htmlContent = rewriteHtmlMedia(
    String(processed).trim(),
    mediaMap,
    useRelativeUrls,
    featuredRef,
  );

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

  const meta = {
    ...(metaFromFrontmatter || {}),
    raw_markdown: raw,
  };
  if (featuredRef.value?.url) {
    meta.featured_image_url = featuredRef.value.url;
  }

  const payload = {
    title: frontmatter.title,
    content: htmlContent,
    status: frontmatter.status || "draft",
    slug: slug, // Always include slug in payload for idempotent uploads
    meta,
  };

  const postDate = frontmatter.date || frontmatter.created;
  if (postDate) payload.date = postDate;
  if (frontmatter.excerpt) payload.excerpt = frontmatter.excerpt;
  const tags = normalizeTags(frontmatter.tags);
  if (tags) payload.tags = tags;
  if (featuredRef.value?.id) payload.featured_media = featuredRef.value.id;

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

  const payloadWithDate = payload.date
    ? payload
    : { ...payload, date: new Date().toISOString() };

  const existingPost = await findPostBySlug(client, payload.slug);

  if (existingPost) {
    // Update existing post
    // Make sure to include the ID for updates
    return client.posts().id(existingPost.id).update(payloadWithDate);
  } else {
    // Create new post, ensuring slug is explicitly set
    return client.posts().create(payloadWithDate);
  }
}
