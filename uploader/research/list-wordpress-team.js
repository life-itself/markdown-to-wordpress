import "dotenv/config";
import fs from "node:fs/promises";
import path from "node:path";

function sanitizeBaseUrl(url) {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

const baseUrl = process.env.WP_BASE_URL;
const username = process.env.WP_USERNAME;
const appPassword = process.env.WP_APP_PASSWORD;

if (!baseUrl || !username || !appPassword) {
  throw new Error("Missing WP_BASE_URL, WP_USERNAME or WP_APP_PASSWORD");
}

const apiBase = `${sanitizeBaseUrl(baseUrl)}/wp-json/wp/v2`;
const authHeader = `Basic ${Buffer.from(`${username}:${appPassword}`).toString("base64")}`;

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: {
      Authorization: authHeader,
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed ${response.status} ${response.statusText}: ${text}`);
  }
  return response.json();
}

async function listTypes() {
  const types = await fetchJson(`${apiBase}/types?context=edit`);
  return Object.values(types);
}

async function fetchEntriesForType(restBase) {
  const entries = [];
  let page = 1;
  while (true) {
    const url = `${apiBase}/${restBase}?per_page=100&page=${page}&context=edit`;
    const batch = await fetchJson(url);
    entries.push(...batch);
    if (batch.length < 100) break;
    page += 1;
  }
  return entries;
}

function formatEntry(entry, type) {
  const title = entry.title?.rendered || entry.name || "";
  const jobTitle =
    entry.job_title ||
    entry.meta?.job_title ||
    entry.pods?.job_title ||
    null;
  return {
    id: entry.id,
    slug: entry.slug || entry.post_name || null,
    title: title.trim(),
    job_title: jobTitle || null,
    type: type.slug || type.name || type.rest_base,
  };
}

async function main() {
  const types = await listTypes();

  const ignored = new Set([
    "posts",
    "pages",
    "media",
    "wp_block",
    "wp_template_part",
    "wp_template",
    "wp_navigation",
    "wp_global_styles",
    "attachment",
    "nav_menu_item",
    "revision",
  ]);

  const candidates = types.filter((type) => {
    if (!type.rest_base) return false;
    if (ignored.has(type.rest_base)) return false;
    const marker = `${type.slug || ""} ${type.rest_base || ""} ${type.name || ""}`.toLowerCase();
    return (
      marker.includes("team") ||
      marker.includes("people") ||
      marker.includes("author") ||
      marker.includes("pod")
    );
  });

  const collected = [];
  for (const type of candidates) {
    try {
      const entries = await fetchEntriesForType(type.rest_base);
      entries.forEach((entry) => collected.push(formatEntry(entry, type)));
    } catch (error) {
      console.warn(`Failed to fetch type ${type.rest_base}: ${error.message}`);
    }
  }

  // De-duplicate by id
  const byId = new Map();
  for (const entry of collected) {
    const existing = byId.get(entry.id);
    if (!existing) {
      byId.set(entry.id, entry);
    } else {
      byId.set(entry.id, { ...existing, ...entry });
    }
  }

  const results = Array.from(byId.values()).sort((a, b) => {
    return (a.title || "").localeCompare(b.title || "") ||
      String(a.id).localeCompare(String(b.id));
  });

  const txtLines = results.map((entry) =>
    [entry.id, entry.title, entry.slug, entry.job_title, entry.type]
      .filter((v) => v !== null && v !== undefined && String(v).trim() !== "")
      .join("\t"),
  );

  await fs.writeFile(
    path.join(process.cwd(), "research", "wordpress-team-authors.txt"),
    txtLines.join("\n"),
  );
  await fs.writeFile(
    path.join(process.cwd(), "research", "wordpress-team-authors.json"),
    JSON.stringify({ types: candidates, entries: results }, null, 2),
  );

  console.log(
    `Fetched ${results.length} entries across ${candidates.length} candidate types.`,
  );
}

main().catch((error) => {
  console.error("Failed to list team authors:", error);
  process.exit(1);
});
