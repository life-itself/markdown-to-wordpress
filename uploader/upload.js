import "dotenv/config";
import { stat, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
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
      const files = await glob("**/*.md", { cwd: p, realpath: true });
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
