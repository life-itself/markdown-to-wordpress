import "dotenv/config";
import { stat, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import matter from "gray-matter";
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
const DEFAULT_MAPPING_PATH = path.join(__dirname, "uploadMediaMap.json");
const DEFAULT_AUTHORS_PATH = path.join(__dirname, "authors.json");
const DEFAULT_PEOPLE_AUTHORS_PATH = path.join(
  __dirname,
  "research",
  "authors.json",
);
const DEFAULT_CONTENT_ROOT = path.join(__dirname, "next.lifeitself.org");

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
      entry.job_title ||
      entry.meta?.job_title ||
      entry.pods?.job_title ||
      "";
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
    await writeFile(authorsPath, `${JSON.stringify(authors, null, 2)}\n`, "utf8");
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

  const types = await fetchJsonWithAuth(`${apiBase}/types?context=edit`, authHeader);
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
    const marker = `${type.slug || ""} ${type.rest_base || ""} ${type.name || ""}`.toLowerCase();
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
              "Path to uploadMediaMap.json for rewriting image links (optional).",
            default: DEFAULT_MAPPING_PATH,
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
      "people list",
      "List existing WordPress team entries (id | name | slug | job title).",
      (y) => y,
      () => handlePeopleList(),
    )
    .command(
      "people create <paths...>",
      "Create or update WordPress team entries from markdown files.",
      (y) =>
        y
          .positional("paths", {
            describe: "Markdown file(s) or directories of people content.",
            type: "string",
            array: true,
          })
          .option("override", {
            alias: "o",
            type: "boolean",
            default: false,
            describe: "Update an existing team entry if it already exists.",
          })
          .option("mapping", {
            alias: "m",
            type: "string",
            default: DEFAULT_MAPPING_PATH,
            describe:
              "Path to uploadMediaMap.json for resolving avatar images (required).",
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
      "people listlocal",
      "Scan local content to produce authors.json (counts + names from people/*).",
      (y) =>
        y
          .option("content", {
            type: "string",
            default: DEFAULT_CONTENT_ROOT,
            describe: "Path to local content root (defaults to next.lifeitself.org).",
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
      "people mergeremote",
      "Merge remote WordPress author IDs/names into an existing authors.json.",
      (y) =>
        y.option("authors", {
          alias: "a",
          type: "string",
          default: DEFAULT_AUTHORS_PATH,
          describe: "Path to authors.json to update.",
        }),
      (argv) => handlePeopleMergeRemote(argv),
    )
    .command(
      "people build <paths...>",
      "Build authors.json (local + remote merge) then run people create.",
      (y) =>
        y
          .positional("paths", {
            describe: "Markdown file(s) or directories of people content.",
            type: "string",
            array: true,
          })
          .option("content", {
            type: "string",
            default: DEFAULT_CONTENT_ROOT,
            describe: "Path to local content root (defaults to next.lifeitself.org).",
          })
          .option("mapping", {
            alias: "m",
            type: "string",
            default: DEFAULT_MAPPING_PATH,
            describe:
              "Path to uploadMediaMap.json for resolving avatar images (required).",
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
            describe: "Update an existing team entry if it already exists.",
          }),
      (argv) => handlePeopleBuild(argv),
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
