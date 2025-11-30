import "dotenv/config";
import { stat, readFile, writeFile, appendFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import matter from "gray-matter";
import crypto from "node:crypto";
import { Blob } from "node:buffer";
import {
  convertMarkdownToPost,
  createWpClient,
  prepareWordpressPayload,
  upsertPostToWordpress,
} from "./src/lib.js";
import {
  convertMarkdownToTeamMember,
  listTeamMembers,
  updateAuthorsRecord,
  upsertTeamMember,
} from "./src/people.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_MAPPING_FILENAME = "mediamap.json";
const DEFAULT_AUTHORS_PATH = path.join(__dirname, "authors.json");
const DEFAULT_PEOPLE_AUTHORS_PATH = path.join(
  __dirname,
  "research",
  "authors.json",
);
const DEFAULT_CONTENT_ROOT = path.join(__dirname, "next.lifeitself.org");
const DEFAULT_MEDIA_CONCURRENCY = 5;
function defaultMappingPath() {
  return path.resolve(process.cwd(), DEFAULT_MAPPING_FILENAME);
}
const SUPPORTED_MEDIA_EXTENSIONS = [
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
];
const MEDIA_EXTENSION_SET = new Set(
  SUPPORTED_MEDIA_EXTENSIONS.map((ext) => `.${ext}`),
);
const MIME_TYPES = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  gif: "image/gif",
  svg: "image/svg+xml",
  webp: "image/webp",
  bmp: "image/bmp",
  tif: "image/tiff",
  tiff: "image/tiff",
  avif: "image/avif",
  heic: "image/heic",
  heif: "image/heif",
  pdf: "application/pdf",
};
const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const IS_TTY = Boolean(process.stdout && process.stdout.isTTY);
let spinnerTimer = null;
let spinnerIndex = 0;
let lastRenderLength = 0;

async function fileExists(candidate) {
  try {
    const stats = await stat(candidate);
    return stats.isFile();
  } catch {
    return false;
  }
}

async function getMarkdownFiles(paths = []) {
  const filePaths = new Set();

  for (const p of paths) {
    const stats = await stat(p);
    if (stats.isDirectory()) {
      const files = await glob("**/*.md", {
        cwd: p,
        absolute: true,
        nodir: true,
      });
      files.forEach((file) => filePaths.add(file));
    } else if (p.endsWith(".md")) {
      filePaths.add(path.resolve(p));
    }
  }

  return Array.from(filePaths);
}

function parseJsonObject(raw, label) {
  const parsed = JSON.parse(raw);
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error(`${label} must be a JSON object.`);
  }
  return parsed;
}

function normalizeUrlForComparison(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url, "http://placeholder");
    return parsed.pathname || parsed.toString();
  } catch {
    return url;
  }
}

async function loadJsonStrict(targetPath, label) {
  const absPath = path.resolve(targetPath);
  const raw = await readFile(absPath, "utf8");
  return { data: parseJsonObject(raw, label), path: absPath };
}

async function loadJsonOptional(targetPath, label) {
  const absPath = path.resolve(targetPath);
  try {
    const raw = await readFile(absPath, "utf8");
    return parseJsonObject(raw, label);
  } catch (error) {
    const message =
      error.code === "ENOENT"
        ? `${label} not found at ${absPath}.`
        : `Could not read ${label} at ${absPath}: ${error.message}`;
    console.warn(message);
    return {};
  }
}

function normalizeAuthorValues(value) {
  const result = [];
  const add = (candidate) => {
    if (candidate === null || candidate === undefined) return;
    if (Array.isArray(candidate)) {
      candidate.forEach(add);
      return;
    }
    const raw =
      typeof candidate === "string" || typeof candidate === "number"
        ? String(candidate)
        : "";
    raw
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean)
      .forEach((part) => result.push(part));
  };
  add(value);
  return result;
}

function sanitizeBaseUrl(url) {
  return url?.endsWith("/") ? url.slice(0, -1) : url;
}

function isSupportedMediaFile(filePath) {
  return MEDIA_EXTENSION_SET.has(path.extname(filePath).toLowerCase());
}

async function collectMediaFiles(inputs) {
  const files = new Set();
  const pattern = `**/*.{${SUPPORTED_MEDIA_EXTENSIONS.join(",")}}`;

  for (const rawInput of inputs) {
    const targetPath = path.resolve(String(rawInput));
    let stats;
    try {
      stats = await stat(targetPath);
    } catch (error) {
      console.warn(`Skipping ${rawInput}: ${error.message}`);
      continue;
    }

    if (stats.isDirectory()) {
      const matches = await glob(pattern, {
        cwd: targetPath,
        absolute: true,
        nodir: true,
        nocase: true,
      });
      matches.forEach((match) => files.add(path.resolve(match)));
    } else if (stats.isFile()) {
      if (!isSupportedMediaFile(targetPath)) {
        console.warn(`Skipping ${targetPath}: not a supported media type.`);
        continue;
      }
      files.add(targetPath);
    }
  }

  return Array.from(files);
}

async function loadMapping(mappingPath) {
  try {
    const data = await readFile(mappingPath, "utf8");
    const parsed = JSON.parse(data);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed;
    }
  } catch (error) {
    if (error.code !== "ENOENT") {
      console.warn(
        `Unable to read existing mapping at ${mappingPath}: ${error.message}`,
      );
    }
  }
  return {};
}

async function saveMapping(mappingPath, mapping) {
  const sortedEntries = Object.entries(mapping).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  const sorted = Object.fromEntries(sortedEntries);
  await writeFile(mappingPath, `${JSON.stringify(sorted, null, 2)}\n`, "utf8");
}

function createSerializedSaver(mappingPath, mapping) {
  let chain = Promise.resolve();
  return function scheduleSave() {
    chain = chain
      .then(() => saveMapping(mappingPath, mapping))
      .catch((error) => {
        console.error(`Failed to persist mapping: ${error.message}`);
      });
    return chain;
  };
}

function createErrorLogger(errorPath) {
  let chain = Promise.resolve();
  return function logErrorLine(line) {
    chain = chain
      .then(() => appendFile(errorPath, `${line}\n`, "utf8"))
      .catch((err) =>
        console.error(`Failed to append to error log: ${err.message}`),
      );
    return chain;
  };
}

async function readFileBufferAndHash(filePath) {
  const buffer = await readFile(filePath);
  const hash = crypto.createHash("sha256").update(buffer).digest("hex");
  return { buffer, hash };
}

function clearSpinnerLines() {
  if (!IS_TTY) return;
  const maxLen = lastRenderLength;
  const blank = " ".repeat(maxLen || 0);
  process.stdout.write(`\r${blank}\r`);
  process.stdout.write("\r");
  lastRenderLength = 0;
}

function renderSpinner(state) {
  if (!IS_TTY) return;
  const frame = SPINNER_FRAMES[spinnerIndex % SPINNER_FRAMES.length];
  spinnerIndex += 1;
  const percent =
    state.total > 0 ? Math.round((state.processed / state.total) * 100) : 0;
  const line1 = `${frame} uploading ${state.processed}/${state.total} (${percent}%) | uploaded:${state.uploaded} skipped:${state.skipped} failed:${state.failed}`;

  const pad1 =
    lastRenderLength > line1.length ? lastRenderLength - line1.length : 0;

  process.stdout.write(`\r${line1}${" ".repeat(pad1)}`);

  lastRenderLength = line1.length;
}

function startSpinner(state) {
  if (!IS_TTY) return;
  spinnerTimer = setInterval(() => renderSpinner(state), 80);
}

function stopSpinner(state) {
  if (!IS_TTY) return;
  if (spinnerTimer) clearInterval(spinnerTimer);
  renderSpinner(state);
  process.stdout.write("\n");
  spinnerTimer = null;
  lastRenderLength = 0;
}

function logWithSpinnerPause(state, message) {
  if (!IS_TTY) return;
  clearSpinnerLines();
  console.log(message);
  renderSpinner(state);
}

async function prefillMediaMapping(config, mapping, mediaFiles, hashCache) {
  let remoteMedia = [];
  try {
    remoteMedia = await fetchRemoteMedia(config);
  } catch (error) {
    console.warn(`Could not fetch remote media list: ${error.message}`);
  }

  const remoteByFile = new Map(
    remoteMedia
      .filter((item) => item.file)
      .map((item) => [item.file.toLowerCase(), item]),
  );

  // Build set for pruning by URL
  const remoteUrls = new Set();
  remoteMedia.forEach((item) => {
    if (item.url) remoteUrls.add(item.url);
  });

  let matched = 0;
  let added = 0;
  let removed = 0;
  for (const filePath of mediaFiles) {
    const fileName = path.basename(filePath);
    const remote = remoteByFile.get(fileName.toLowerCase());
    if (!remote) continue;
    matched += 1;
    if (!mapping[fileName] || !mapping[fileName].url) {
      const { hash } = await readFileBufferAndHash(filePath);
      hashCache.set(path.resolve(filePath), hash);
      mapping[fileName] = {
        hash,
        url: remote.url,
        id: remote.id,
        fileName,
        originalPath: path.resolve(filePath),
        uploadedAt: new Date().toISOString(),
        source: "prefill",
      };
      added += 1;
    }
  }

  // Remove mapping entries for files no longer present remotely
  for (const key of Object.keys(mapping)) {
    const entry = mapping[key];
    const urlMissing =
      entry?.url &&
      !remoteUrls.has(entry.url) &&
      !remoteUrls.has(normalizeUrlForComparison(entry.url));

    if (urlMissing) {
      delete mapping[key];
      removed += 1;
    }
  }

  return {
    remoteCount: remoteMedia.length,
    matched,
    added,
    removed,
  };
}

async function fetchRemoteMedia(config) {
  const results = [];
  let page = 1;
  let totalPages = Infinity;
  while (page <= totalPages) {
    const response = await fetch(
      `${config.baseUrl}/wp-json/wp/v2/media?per_page=100&page=${page}&context=edit`,
      {
        headers: {
          Authorization: `Basic ${config.authHeader}`,
        },
      },
    );

    // WP returns 400 when page exceeds total_pages; stop gracefully
    if (response.status === 400 && page > 1) break;

    const text = await response.text();
    if (!response.ok) {
      throw new Error(
        `Failed to fetch remote media (status ${response.status}): ${text}`,
      );
    }
    const batch = JSON.parse(text);
    if (!Array.isArray(batch) || batch.length === 0) break;
    results.push(
      ...batch.map((item) => ({
        id: item.id,
        date: item.date_gmt || item.date || null,
        url: item.source_url || item.link || item.guid?.rendered || null,
        file: path.basename(item.source_url || item.guid?.rendered || ""),
      })),
    );

    const headerPages = Number(response.headers.get("x-wp-totalpages"));
    if (!Number.isNaN(headerPages) && headerPages > 0) {
      totalPages = headerPages;
    }
    page += 1;
  }
  return results;
}

function reportDuplicateMedia(remoteMedia) {
  const byFile = new Map();
  remoteMedia.forEach((item) => {
    if (!item.file) return;
    const key = item.file.toLowerCase();
    if (!byFile.has(key)) byFile.set(key, []);
    byFile.get(key).push(item);
  });

  const dupes = Array.from(byFile.entries())
    .filter(([, items]) => items.length > 1)
    .map(([file, items]) => {
      const sorted = [...items].sort((a, b) => {
        const da = a.date ? Date.parse(a.date) : 0;
        const db = b.date ? Date.parse(b.date) : 0;
        if (db !== da) return db - da;
        return (b.id || 0) - (a.id || 0);
      });
      return { file, items: sorted };
    })
    .sort((a, b) => b.items.length - a.items.length || a.file.localeCompare(b.file));

  console.log(`Found ${dupes.length} duplicate filename group(s).`);
  dupes.forEach(({ file, items }) => {
    const summary = items
      .map((item) => `${item.id || "?"}${item.date ? `@${item.date}` : ""}`)
      .join(", ");
    console.log(`${file} (${items.length}): ${summary}`);
  });
}

function getWordpressConfig() {
  const baseUrl = sanitizeBaseUrl(process.env.WP_BASE_URL);
  const username = process.env.WP_USERNAME;
  const appPassword = process.env.WP_APP_PASSWORD;

  if (!baseUrl || !username || !appPassword) {
    throw new Error(
      "Missing WordPress credentials (WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD).",
    );
  }

  return {
    baseUrl,
    username,
    appPassword,
    authHeader: Buffer.from(`${username}:${appPassword}`).toString("base64"),
  };
}

async function uploadMediaFile({ buffer, filePath, hash, config }) {
  const ext = path.extname(filePath).toLowerCase().replace(/^\./, "");
  const mimeType = MIME_TYPES[ext] || "application/octet-stream";
  const fileName = path.basename(filePath);
  const formData = new FormData();
  formData.append("file", new Blob([buffer], { type: mimeType }), fileName);
  formData.append("title", path.parse(fileName).name);
  formData.append("meta[original_local_path]", filePath);
  formData.append("meta[original_local_hash]", hash);

  const response = await fetch(`${config.baseUrl}/wp-json/wp/v2/media`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${config.authHeader}`,
    },
    body: formData,
  });

  const bodyText = await response.text();
  if (!response.ok) {
    const error = new Error(
      `Failed to upload ${fileName} (status ${response.status}): ${bodyText}`,
    );
    error.status = response.status;
    throw error;
  }

  return JSON.parse(bodyText);
}

async function runWithConcurrency(items, limit, worker) {
  let index = 0;

  async function next() {
    const currentIndex = index++;
    if (currentIndex >= items.length) return;
    await worker(items[currentIndex]);
    return next();
  }

  const runners = Array.from({ length: Math.min(limit, items.length) }, () =>
    next(),
  );
  await Promise.all(runners);
}

async function handleUploadPosts(argv) {
  const filePaths = await getMarkdownFiles(argv.paths);
  if (filePaths.length === 0) {
    console.log("No markdown files found to upload.");
    return;
  }

  const client = createWpClient({
    baseUrl: process.env.WP_BASE_URL,
    username: process.env.WP_USERNAME,
    appPassword: process.env.WP_APP_PASSWORD,
  });

  console.log(`Found ${filePaths.length} markdown file(s) to upload.`);

  const mediaMap = await loadJsonOptional(argv.mapping, "Media mapping");
  if (mediaMap && Object.keys(mediaMap).length > 0) {
    console.log(
      `Loaded ${Object.keys(mediaMap).length} media mapping entries from ${path.resolve(argv.mapping)}.`,
    );
  }

  const authorsMap = await loadJsonOptional(argv.authors, "Author mapping");
  if (authorsMap && Object.keys(authorsMap).length > 0) {
    console.log(
      `Loaded ${Object.keys(authorsMap).length} author mapping entries from ${path.resolve(argv.authors)}.`,
    );
  }

  for (const filePath of filePaths) {
    try {
      const raw = await readFile(filePath, "utf8");
      const { payload } = await convertMarkdownToPost(raw, {
        sourcePath: filePath,
        mediaMap,
        useRelativeUrls: !argv["absolute-media-urls"],
      });
      const preparedPayload = prepareWordpressPayload(payload, {
        authorsMap,
        logger: console,
      });
      const response = await upsertPostToWordpress(client, preparedPayload);
      const action = response.id === payload.id ? "Updated" : "Uploaded";
      console.log(`${action} ${path.basename(filePath)}: ${response.link}`);
    } catch (error) {
      console.error(
        `Failed to upload ${path.basename(filePath)}: ${error.message}`,
      );
    }
  }
}

async function handlePeopleList() {
  const client = createWpClient({
    baseUrl: process.env.WP_BASE_URL,
    username: process.env.WP_USERNAME,
    appPassword: process.env.WP_APP_PASSWORD,
  });
  const members = await listTeamMembers(client);
  members.forEach((entry) => {
    const title = entry?.title?.rendered || entry?.name || "";
    const slug = entry.slug || entry.post_name || "";
    const jobTitle =
      entry.job_title || entry.meta?.job_title || entry.pods?.job_title || "";
    console.log(
      [entry.id, title.trim(), slug, jobTitle].filter(Boolean).join(" | "),
    );
  });
}

async function handlePeopleCreate(argv) {
  let authors = null;
  let authorsPath = null;

  const mapping = await loadJsonStrict(argv.mapping, "Media mapping");
  const mediaMap = mapping.data;

  if (argv.authors) {
    const loaded = await loadJsonStrict(argv.authors, "Authors mapping");
    authors = loaded.data;
    authorsPath = loaded.path;
  } else if (await fileExists(DEFAULT_PEOPLE_AUTHORS_PATH)) {
    try {
      const loaded = await loadJsonStrict(
        DEFAULT_PEOPLE_AUTHORS_PATH,
        "Authors mapping",
      );
      authors = loaded.data;
      authorsPath = loaded.path;
    } catch (error) {
      console.warn(`Could not load default authors mapping: ${error.message}`);
    }
  }

  const client = createWpClient({
    baseUrl: process.env.WP_BASE_URL,
    username: process.env.WP_USERNAME,
    appPassword: process.env.WP_APP_PASSWORD,
  });

  const filePaths = await getMarkdownFiles(argv.paths);
  if (filePaths.length === 0) {
    console.log("No markdown files found to upload.");
    return;
  }

  let authorsDirty = false;

  for (const filePath of filePaths) {
    try {
      const raw = await readFile(filePath, "utf8");
      const { payload } = await convertMarkdownToTeamMember(raw, {
        sourcePath: filePath,
        mediaMap,
      });

      if (
        authors &&
        !argv.override &&
        authors[payload.slug] &&
        authors[payload.slug].wordpress_id
      ) {
        console.log(
          `Skipped ${path.basename(filePath)}: authors mapping has wordpress_id ${authors[payload.slug].wordpress_id}.`,
        );
        continue;
      }

      const { result, action } = await upsertTeamMember(client, payload, {
        override: argv.override,
      });

      if (action === "skipped") {
        console.log(
          `Skipped ${path.basename(filePath)}: team member already exists (slug ${result.slug || payload.slug}).`,
        );
      } else {
        const verb = action === "updated" ? "Updated" : "Created";
        console.log(
          `${verb} ${path.basename(filePath)} -> ${result.slug} (id ${result.id})`,
        );
        if (authors) {
          authors = updateAuthorsRecord(authors, payload, result);
          authorsDirty = true;
        }
      }
    } catch (error) {
      console.error(
        `Failed to upload ${path.basename(filePath)}: ${error.message}`,
      );
      process.exitCode = 1;
      break;
    }
  }

  if (authorsDirty && authorsPath) {
    await writeFile(
      authorsPath,
      `${JSON.stringify(authors, null, 2)}\n`,
      "utf8",
    );
    console.log(`Updated authors mapping at ${authorsPath}.`);
  }
}

async function generateLocalAuthors({
  contentRoot = DEFAULT_CONTENT_ROOT,
  outputPath = DEFAULT_AUTHORS_PATH,
}) {
  const files = await glob("**/*.md", {
    cwd: contentRoot,
    absolute: true,
    ignore: ["people/**", "node_modules/**"],
  });

  const authors = {};
  const peopleDir = path.join(contentRoot, "people");

  for (const filePath of files) {
    const raw = await readFile(filePath, "utf8");
    const { data } = matter(raw);
    const ids = [
      ...normalizeAuthorValues(data.author),
      ...normalizeAuthorValues(data.authors),
    ];
    if (ids.length === 0) continue;
    const rel = path.relative(contentRoot, filePath);
    const isPost =
      rel.startsWith(`blog${path.sep}`) || rel.split(path.sep)[0] === "blog";
    ids.forEach((id) => {
      if (!authors[id]) {
        authors[id] = {
          slug: id,
          name: null,
          posts_count: 0,
          pages_count: 0,
        };
      }
      if (isPost) authors[id].posts_count += 1;
      else authors[id].pages_count += 1;
    });
  }

  for (const id of Object.keys(authors)) {
    const personPath = path.join(peopleDir, `${id}.md`);
    try {
      const raw = await readFile(personPath, "utf8");
      const { data } = matter(raw);
      const name =
        data.name || data.title || data.full_name || data.fullName || null;
      authors[id].name = name ? String(name).trim() : null;
      authors[id].exists_local = true;
    } catch (error) {
      if (error.code === "ENOENT") {
        authors[id].exists_local = false;
      } else {
        throw error;
      }
    }
  }

  await writeFile(outputPath, `${JSON.stringify(authors, null, 2)}\n`, "utf8");
  console.log(
    `Wrote ${Object.keys(authors).length} author(s) to ${path.resolve(outputPath)}.`,
  );
  return authors;
}

async function fetchJsonWithAuth(url, authHeader) {
  const response = await fetch(url, {
    headers: {
      Authorization: authHeader,
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(
      `Request failed ${response.status} ${response.statusText}: ${text}`,
    );
  }
  return response.json();
}

async function fetchWordpressTeamEntries() {
  const baseUrl = process.env.WP_BASE_URL;
  const username = process.env.WP_USERNAME;
  const appPassword = process.env.WP_APP_PASSWORD;
  if (!baseUrl || !username || !appPassword) {
    throw new Error(
      "Missing WP_BASE_URL, WP_USERNAME or WP_APP_PASSWORD for remote merge.",
    );
  }

  const apiBase = `${sanitizeBaseUrl(baseUrl)}/wp-json/wp/v2`;
  const authHeader = `Basic ${Buffer.from(`${username}:${appPassword}`).toString("base64")}`;

  const types = await fetchJsonWithAuth(
    `${apiBase}/types?context=edit`,
    authHeader,
  );
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

  const candidates = Object.values(types).filter((type) => {
    if (!type.rest_base) return false;
    if (ignored.has(type.rest_base)) return false;
    const marker =
      `${type.slug || ""} ${type.rest_base || ""} ${type.name || ""}`.toLowerCase();
    return (
      marker.includes("team") ||
      marker.includes("people") ||
      marker.includes("author") ||
      marker.includes("pod")
    );
  });

  const entries = [];
  for (const type of candidates) {
    let page = 1;
    while (true) {
      const url = `${apiBase}/${type.rest_base}?per_page=100&page=${page}&context=edit`;
      const batch = await fetchJsonWithAuth(url, authHeader);
      if (!Array.isArray(batch) || batch.length === 0) break;
      batch.forEach((entry) =>
        entries.push({
          id: entry.id,
          slug: entry.slug || entry.post_name || null,
          title: (entry.title?.rendered || entry.name || "").trim(),
          job_title:
            entry.job_title ||
            entry.meta?.job_title ||
            entry.pods?.job_title ||
            null,
          type: type.slug || type.name || type.rest_base,
        }),
      );
      if (batch.length < 100) break;
      page += 1;
    }
  }

  return entries;
}

function mergeAuthorsWithRemote(authors, remoteEntries) {
  if (!authors || typeof authors !== "object") return {};
  const remoteBySlug = new Map();
  const remoteByName = new Map();

  remoteEntries.forEach((entry) => {
    if (entry.slug) remoteBySlug.set(entry.slug.toLowerCase(), entry);
    if (entry.title) remoteByName.set(entry.title.toLowerCase(), entry);
    if (entry.slug && !remoteByName.has(entry.slug.toLowerCase())) {
      remoteByName.set(entry.slug.toLowerCase(), entry);
    }
  });

  const updated = { ...authors };
  for (const [slug, record] of Object.entries(authors)) {
    const name = record.name || record.title || record.wordpress_name || null;
    const match =
      remoteBySlug.get(slug.toLowerCase()) ||
      (name ? remoteByName.get(String(name).toLowerCase()) : null);
    if (match) {
      updated[slug] = {
        ...record,
        wordpress_id: record.wordpress_id || match.id,
        wordpress_name: record.wordpress_name || match.title,
      };
    }
  }
  return updated;
}

async function handlePeopleListLocal(argv) {
  await generateLocalAuthors({
    contentRoot: argv.content,
    outputPath: argv.output,
  });
}

async function handlePeopleMergeRemote(argv) {
  const authorsPath = path.resolve(argv.authors);
  const raw = await readFile(authorsPath, "utf8");
  const authors = parseJsonObject(raw, "authors mapping");
  const remoteEntries = await fetchWordpressTeamEntries();
  const merged = mergeAuthorsWithRemote(authors, remoteEntries);
  await writeFile(authorsPath, `${JSON.stringify(merged, null, 2)}\n`, "utf8");
  console.log(
    `Merged remote WordPress IDs into ${authorsPath} using ${remoteEntries.length} remote entries.`,
  );
}

async function handlePeopleBuild(argv) {
  const authorsPath = path.resolve(argv.authors);
  console.log("Step 1/3: building local authors map...");
  await generateLocalAuthors({
    contentRoot: argv.content,
    outputPath: authorsPath,
  });

  console.log("Step 2/3: merging remote WordPress author IDs...");
  await handlePeopleMergeRemote({ authors: authorsPath });

  console.log("Step 3/3: creating/updating people in WordPress...");
  await handlePeopleCreate({
    paths: argv.paths,
    override: argv.override,
    mapping: argv.mapping,
    authors: authorsPath,
  });
}

async function handleAll(argv) {
  const contentRoot = path.resolve(argv.contentRoot);
  const peoplePath = path.resolve(contentRoot, argv.peopleDir);
  const blogPath = path.resolve(contentRoot, argv.blogDir);
  const mappingPath = argv.mapping
    ? path.resolve(argv.mapping)
    : defaultMappingPath();
  const authorsPath = path.resolve(argv.authors);

  console.log("=== All-in-one: media upload ===");
  await handleMediaUpload({
    paths: [contentRoot],
    mapping: mappingPath,
    concurrency: argv.concurrency || DEFAULT_MEDIA_CONCURRENCY,
  });

  console.log("=== All-in-one: people build/create ===");
  await handlePeopleBuild({
    paths: [peoplePath],
    override: argv.override,
    mapping: mappingPath,
    authors: authorsPath,
    content: contentRoot,
  });

  console.log("=== All-in-one: upload posts ===");
  await handleUploadPosts({
    paths: [blogPath],
    mapping: mappingPath,
    authors: authorsPath,
    "absolute-media-urls": argv["absolute-media-urls"],
  });
}

async function handleMediaUpload(argv) {
  const config = getWordpressConfig();
  const mappingPath = path.resolve(argv.mapping);
  const mediaFiles = await collectMediaFiles(argv.paths);
  const concurrency = Math.max(1, Math.floor(argv.concurrency || 1));

  if (mediaFiles.length === 0) {
    console.log("No media files found to upload.");
    return;
  }

  const mapping = await loadMapping(mappingPath);
  const saveMappingSafely = createSerializedSaver(mappingPath, mapping);
  const errorLogPath = `${mappingPath}.errors.txt`;
  const logErrorLine = createErrorLogger(errorLogPath);
  const hashCache = new Map();

  // Prefill mapping from remote media by filename
  const prefill = await prefillMediaMapping(
    config,
    mapping,
    mediaFiles,
    hashCache,
  );
  if (prefill.remoteCount > 0) {
    console.log(
      `Prefill: fetched ${prefill.remoteCount} remote media items; matched ${prefill.matched} local files; added ${prefill.added} new mapping entries.`,
    );
    if (prefill.added > 0) {
      await saveMappingSafely();
    }
  }
  const active = new Set();
  const state = {
    total: mediaFiles.length,
    processed: 0,
    uploaded: 0,
    skipped: 0,
    failed: 0,
    active,
    last: "",
  };

  console.log(
    `Found ${mediaFiles.length} media file(s) to process. Running with concurrency ${concurrency}.`,
  );

  startSpinner(state);

  const processFile = async (filePath) => {
    const absPath = path.resolve(filePath);
    const key = path.basename(absPath);
    const activeLabel = path.basename(absPath);
    active.add(activeLabel);
    renderSpinner(state);
    let buffer;
    let hash;
    try {
      if (hashCache.has(absPath)) {
        hash = hashCache.get(absPath);
        buffer = await readFile(absPath);
      } else {
        ({ buffer, hash } = await readFileBufferAndHash(absPath));
        hashCache.set(absPath, hash);
      }
    } catch (error) {
      state.failed += 1;
      const msg = error?.message || "Unknown error";
      await logErrorLine(`${absPath}\t${msg}`);
      active.delete(activeLabel);
      state.processed += 1;
      return;
    }

    const existing = mapping[key];
    if (existing && existing.hash === hash && existing.url) {
      state.skipped += 1;
      state.last = `[skip] ${path.basename(absPath)}`;
      active.delete(activeLabel);
      state.processed += 1;
      renderSpinner(state);
      return;
    }

    if (existing && existing.hash !== hash) {
      state.last = `[reupload] ${path.basename(absPath)} (hash changed)`;
      renderSpinner(state);
    }

    try {
      const media = await uploadMediaFile({
        buffer,
        filePath: absPath,
        hash,
        config,
      });
      const destinationUrl =
        media?.source_url || media?.guid?.rendered || media?.link || null;
      mapping[key] = {
        hash,
        url: destinationUrl,
        id: media.id,
        fileName: path.basename(absPath),
        originalPath: absPath,
        uploadedAt: new Date().toISOString(),
      };
      await saveMappingSafely();
      state.uploaded += 1;
      state.last = `[upload] ${path.basename(absPath)}`;
    } catch (error) {
      state.failed += 1;
      const msg = error?.message || "Unknown error";
      state.last = `[fail] ${path.basename(absPath)}`;
      await logErrorLine(`${absPath}\t${msg}`);
    } finally {
      active.delete(activeLabel);
      state.processed += 1;
      renderSpinner(state);
    }
  };

  const finalSaveOnExit = async () => {
    await saveMappingSafely();
  };

  process.on("SIGINT", async () => {
    console.warn("\nReceived SIGINT, saving mapping before exit...");
    await finalSaveOnExit();
    stopSpinner(state);
    process.exit(1);
  });
  process.on("uncaughtException", async (error) => {
    console.error("\nUncaught exception:", error);
    await finalSaveOnExit();
    stopSpinner(state);
    process.exit(1);
  });
  process.on("unhandledRejection", async (reason) => {
    console.error("\nUnhandled rejection:", reason);
    await finalSaveOnExit();
    stopSpinner(state);
    process.exit(1);
  });

  await runWithConcurrency(mediaFiles, concurrency, processFile);
  await finalSaveOnExit();
  stopSpinner(state);

  console.log(
    `Done. Uploaded: ${state.uploaded}, Skipped: ${state.skipped}, Failed: ${state.failed}. Mapping saved to ${mappingPath}.`,
  );

  if (state.failed > 0) {
    process.exitCode = 1;
  }
}

async function main() {
  const parser = yargs(hideBin(process.argv))
    .scriptName("upload")
    .usage("Usage: $0 <command> [options]")
    .command(
      "posts <paths...>",
      "Upload markdown posts/pages to WordPress.",
      (y) =>
        y
          .positional("paths", {
            describe: "Markdown file(s) or directories.",
            type: "string",
            array: true,
          })
          .option("mapping", {
            alias: "m",
            type: "string",
            describe:
              "Path to mediamap.json for rewriting image links (optional).",
            default: () => defaultMappingPath(),
          })
          .option("authors", {
            alias: "a",
            type: "string",
            describe:
              "Path to authors.json mapping file (defaults to authors.json in this directory).",
            default: DEFAULT_AUTHORS_PATH,
          })
          .option("absolute-media-urls", {
            type: "boolean",
            default: false,
            describe:
              "Use absolute media URLs instead of relative paths when rewriting content.",
          }),
      (argv) => handleUploadPosts(argv),
    )
    .command(
      "mediasync <paths...>",
      "Prefill mediamap.json by matching local media files against remote WordPress media (no uploads).",
      (y) =>
        y
          .positional("paths", {
            describe: "Media file(s) or directories to scan locally.",
            type: "string",
            array: true,
          })
          .option("mapping", {
            alias: "m",
            type: "string",
            default: () => defaultMappingPath(),
            describe: "Path to mediamap.json to update.",
          }),
      async (argv) => {
        const config = getWordpressConfig();
        const mappingPath = path.resolve(argv.mapping);
        const mediaFiles = await collectMediaFiles(argv.paths);
        const mapping = await loadMapping(mappingPath);
        const hashCache = new Map();
        const prefill = await prefillMediaMapping(
          config,
          mapping,
          mediaFiles,
          hashCache,
        );
        console.log(
          `Mediasync: fetched ${prefill.remoteCount} remote media items; matched ${prefill.matched} local files; added ${prefill.added} new mapping entries.`,
        );
        if (prefill.added > 0) {
          await saveMapping(mappingPath, mapping);
        }
      },
    )
    .command(
      "people <subcommand>",
      "People-related commands (list, create, listlocal, mergeremote, build).",
      (y) =>
        y
          .command(
            "list",
            "List existing WordPress team entries (id | name | slug | job title).",
            (yy) => yy,
            () => handlePeopleList(),
          )
          .command(
            "create <paths...>",
            "Create or update WordPress team entries from markdown files.",
            (yy) =>
              yy
                .positional("paths", {
                  describe:
                    "Markdown file(s) or directories of people content.",
                  type: "string",
                  array: true,
                })
                .option("override", {
                  alias: "o",
                  type: "boolean",
                  default: false,
                  describe:
                    "Update an existing team entry if it already exists.",
                })
                .option("mapping", {
                  alias: "m",
                  type: "string",
                  default: () => defaultMappingPath(),
                  describe:
                    "Path to mediamap.json for resolving avatar images (required).",
                })
                .option("authors", {
                  alias: "a",
                  type: "string",
                  describe:
                    "Optional path to authors mapping JSON to check for existing IDs and update with new WordPress IDs.",
                  default: undefined,
                }),
            (argv) => handlePeopleCreate(argv),
          )
          .command(
            "listlocal",
            "Scan local content to produce authors.json (counts + names from people/*).",
            (yy) =>
              yy
                .option("content", {
                  type: "string",
                  default: DEFAULT_CONTENT_ROOT,
                  describe:
                    "Path to local content root (defaults to next.lifeitself.org).",
                })
                .option("output", {
                  alias: "o",
                  type: "string",
                  default: DEFAULT_AUTHORS_PATH,
                  describe: "Path to write authors.json.",
                }),
            (argv) => handlePeopleListLocal(argv),
          )
          .command(
            "mergeremote",
            "Merge remote WordPress author IDs/names into an existing authors.json.",
            (yy) =>
              yy.option("authors", {
                alias: "a",
                type: "string",
                default: DEFAULT_AUTHORS_PATH,
                describe: "Path to authors.json to update.",
              }),
            (argv) => handlePeopleMergeRemote(argv),
          )
          .command(
            "build <paths...>",
            "Build authors.json (local + remote merge) then run people create.",
            (yy) =>
              yy
                .positional("paths", {
                  describe:
                    "Markdown file(s) or directories of people content.",
                  type: "string",
                  array: true,
                })
                .option("content", {
                  type: "string",
                  default: DEFAULT_CONTENT_ROOT,
                  describe:
                    "Path to local content root (defaults to next.lifeitself.org).",
                })
                .option("mapping", {
                  alias: "m",
                  type: "string",
                  default: () => defaultMappingPath(),
                  describe:
                    "Path to mediamap.json for resolving avatar images (required).",
                })
                .option("authors", {
                  alias: "a",
                  type: "string",
                  default: DEFAULT_AUTHORS_PATH,
                  describe: "Path to authors.json to build and use.",
                })
                .option("override", {
                  alias: "o",
                  type: "boolean",
                  default: false,
                  describe:
                    "Update an existing team entry if it already exists.",
                }),
            (argv) => handlePeopleBuild(argv),
          )
          .demandCommand(1, "Please specify a people subcommand."),
      (argv) => argv,
    )
    .command(
      "media <subcommand>",
      "Media commands (push uploads, pull mapping sync).",
      (y) =>
        y
          .command(
            "push <paths...>",
            "Upload media and update mediamap.json (prefills from remote by filename).",
            (yy) =>
              yy
                .positional("paths", {
                  describe: "Media file(s) or directories to upload.",
                  type: "string",
                  array: true,
                })
                .option("mapping", {
                  alias: "m",
                  type: "string",
                  default: () => defaultMappingPath(),
                  describe: "Path to mediamap.json.",
                })
                .option("concurrency", {
                  alias: "c",
                  type: "number",
                  default: DEFAULT_MEDIA_CONCURRENCY,
                  describe: "How many uploads to run in parallel.",
                }),
            (argv) => handleMediaUpload(argv),
          )
          .command(
            "pull <paths...>",
            "Prefill mediamap.json by matching local media against remote WordPress media (no uploads).",
            (yy) =>
              yy
                .positional("paths", {
                  describe: "Media file(s) or directories to scan locally.",
                  type: "string",
                  array: true,
                })
                .option("mapping", {
                  alias: "m",
                  type: "string",
                  default: () => defaultMappingPath(),
                  describe: "Path to mediamap.json to update.",
                }),
            async (argv) => {
              const config = getWordpressConfig();
              const mappingPath = path.resolve(argv.mapping);
              const mediaFiles = await collectMediaFiles(argv.paths);
              const mapping = await loadMapping(mappingPath);
              const hashCache = new Map();
              const prefill = await prefillMediaMapping(
                config,
                mapping,
                mediaFiles,
                hashCache,
              );
              console.log(
                `Media pull: fetched ${prefill.remoteCount} remote media items; matched ${prefill.matched} local files; added ${prefill.added} new mapping entries; removed ${prefill.removed} missing entries.`,
              );
              if (prefill.added > 0) {
                await saveMapping(mappingPath, mapping);
              }
            },
          )
          .command(
            "dupes",
            "List duplicate remote media by filename (most recent first).",
            (yy) => yy,
            async () => {
              const config = getWordpressConfig();
              const remoteMedia = await fetchRemoteMedia(config);
              reportDuplicateMedia(remoteMedia);
            },
          )
          .demandCommand(1, "Please specify a media subcommand."),
      (argv) => argv,
    )
    .command(
      "all <contentRoot>",
      "Run people build/create then upload posts. Expects people and blog subfolders by default.",
      (y) =>
        y
          .positional("contentRoot", {
            describe:
              "Root directory containing content (default subfolders: people/, blog/).",
            type: "string",
          })
          .option("people-dir", {
            type: "string",
            default: "people",
            describe: "Relative path under contentRoot for people markdown.",
          })
          .option("blog-dir", {
            type: "string",
            default: "blog",
            describe: "Relative path under contentRoot for blog markdown.",
          })
          .option("mapping", {
            alias: "m",
            type: "string",
            default: () => defaultMappingPath(),
            describe: "Path to mediamap.json.",
          })
          .option("authors", {
            alias: "a",
            type: "string",
            default: DEFAULT_AUTHORS_PATH,
            describe: "Path to authors.json to build/merge/use.",
          })
          .option("override", {
            alias: "o",
            type: "boolean",
            default: false,
            describe: "Update existing people entries if they exist.",
          })
          .option("concurrency", {
            alias: "c",
            type: "number",
            default: DEFAULT_MEDIA_CONCURRENCY,
            describe: "Media upload concurrency for the initial stage.",
          })
          .option("absolute-media-urls", {
            type: "boolean",
            default: false,
            describe: "Use absolute media URLs for post uploads.",
          }),
      (argv) => handleAll(argv),
    )
    .demandCommand(1, "Please specify a command.")
    .help()
    .alias("h", "help")
    .wrap(null);

  await parser.parseAsync();
}

main().catch((error) => {
  console.error("An unexpected error occurred:", error.message);
  process.exit(1);
});
