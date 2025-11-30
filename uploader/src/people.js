import path from "node:path";
import matter from "gray-matter";
import { remark } from "remark";
import remarkGfm from "remark-gfm";
import remarkHtml from "remark-html";

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
  return Boolean(ext);
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

function ensureTeamRoute(client) {
  if (!client) throw new Error("A configured WPAPI client is required.");
  if (client._teamHandler) return client._teamHandler;
  if (typeof client.team === "function") {
    client._teamHandler = client.team.bind(client);
    return client._teamHandler;
  }
  if (typeof client.registerRoute !== "function") {
    throw new Error("WPAPI client is missing registerRoute; cannot access team route.");
  }
  const route = client.registerRoute("wp/v2", "/team/(?P<id>[\\d]+)");
  client.team = route;
  client._teamHandler = route.bind(client);
  return client._teamHandler;
}

function normalizeTitle(entry) {
  return (entry?.title?.rendered || "").trim();
}

export async function convertMarkdownToTeamMember(markdownInput, options = {}) {
  if (typeof markdownInput !== "string" && !Buffer.isBuffer(markdownInput)) {
    throw new Error(
      "convertMarkdownToTeamMember expects a string or Buffer of markdown content.",
    );
  }

  const raw =
    typeof markdownInput === "string"
      ? markdownInput
      : markdownInput.toString("utf8");
  const sourcePath = options.sourcePath
    ? path.resolve(options.sourcePath)
    : undefined;
  const mediaMap = options.mediaMap;
  const useRelativeUrls =
    options.useRelativeUrls === undefined ? true : options.useRelativeUrls;
  const { data: frontmatter, content } = matter(raw);

  if (!frontmatter.name || typeof frontmatter.name !== "string") {
    throw new Error('Front matter must include a "name" field for team upload.');
  }

  const slug =
    frontmatter.slug ||
    frontmatter.id ||
    (sourcePath
      ? path.basename(sourcePath, path.extname(sourcePath))
      : undefined);

  if (!slug) {
    throw new Error(
      "Slug must be provided via front matter (id or slug) or derived from the filename.",
    );
  }

  const processed = await remark()
    .use(remarkGfm)
    .use(remarkHtml, { sanitize: false })
    .process(content || "");
  const htmlContent = String(processed).trim();

  const metaFromFrontmatter =
    frontmatter.meta && typeof frontmatter.meta === "object"
      ? frontmatter.meta
      : undefined;

  const meta = {
    ...(metaFromFrontmatter || {}),
  };

  const resolvedAvatar =
    typeof frontmatter.avatar === "string"
      ? resolveMediaReference(
          frontmatter.avatar,
          mediaMap,
          useRelativeUrls,
        )
      : null;

  const payload = {
    title: frontmatter.name.trim(),
    content: htmlContent,
    slug,
    status: frontmatter.status || "publish",
  };

  if (frontmatter.excerpt) {
    payload.excerpt = frontmatter.excerpt;
  }
  if (resolvedAvatar?.id) {
    payload.featured_media = resolvedAvatar.id;
    meta.avatar_url = resolvedAvatar.url;
    meta.featured_image_url = resolvedAvatar.url;
  }
  if (Object.keys(meta).length > 0) {
    payload.meta = meta;
  }

  return {
    payload,
    frontmatter,
    htmlContent,
    slug,
  };
}

export async function listTeamMembers(client) {
  const team = ensureTeamRoute(client);
  const results = [];
  let page = 1;
  while (true) {
    const batch = await team()
      .param("per_page", 100)
      .param("page", page)
      .param("context", "edit")
      .get();
    results.push(...batch);
    if (batch.length < 100) break;
    page += 1;
  }
  return results;
}

export async function findTeamMemberBySlug(client, slug) {
  if (!slug) return null;
  const team = ensureTeamRoute(client);
  const response = await team()
    .param("slug", slug)
    .param("context", "edit")
    .get();
  return response.length > 0 ? response[0] : null;
}

export async function findTeamMemberByName(client, name) {
  if (!name) return null;
  const target = name.trim().toLowerCase();
  if (!target) return null;

  const team = ensureTeamRoute(client);
  let page = 1;
  while (true) {
    const batch = await team()
      .param("per_page", 100)
      .param("page", page)
      .param("search", name)
      .param("context", "edit")
      .get();
    const match = batch.find(
      (entry) => normalizeTitle(entry).toLowerCase() === target,
    );
    if (match) return match;
    if (batch.length < 100) break;
    page += 1;
  }
  return null;
}

export async function deleteTeamMember(client, id) {
  if (!id) return null;
  const team = ensureTeamRoute(client);
  return team().id(id).delete({ force: true });
}

export async function upsertTeamMember(client, payload, options = {}) {
  if (!payload) throw new Error("No payload provided for team upload.");
  if (!payload.slug) throw new Error("Payload must include a slug.");

  const override = Boolean(options.override);
  const team = ensureTeamRoute(client);
  const payloadWithDefaults = {
    status: payload.status || "publish",
    ...payload,
  };

  const existingBySlug = await findTeamMemberBySlug(client, payload.slug);
  if (existingBySlug) {
    if (override) {
      const result = await team().id(existingBySlug.id).update(payloadWithDefaults);
      return { result, action: "updated" };
    }
    return { result: existingBySlug, action: "skipped" };
  }

  const existingByName = await findTeamMemberByName(client, payload.title);
  if (existingByName) {
    if (override) {
      const result = await team().id(existingByName.id).update(payloadWithDefaults);
      return { result, action: "updated" };
    }
    return { result: existingByName, action: "skipped" };
  }

  const result = await team().create(payloadWithDefaults);
  return { result, action: "created" };
}

export { ensureTeamRoute };
