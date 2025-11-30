import "dotenv/config";
import { stat, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import { createWpClient } from "./src/lib.js";
import {
  convertMarkdownToTeamMember,
  listTeamMembers,
  upsertTeamMember,
} from "./src/people.js";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_MAPPING_PATH = path.join(__dirname, "uploadMediaMap.json");
const DEFAULT_AUTHORS_PATH = path.join(__dirname, "research", "authors.json");

function updateAuthorsRecord(authorsMap, payload, wpEntry) {
  if (!payload?.slug) return authorsMap;
  const key = payload.slug;
  const current = authorsMap[key] && typeof authorsMap[key] === "object"
    ? authorsMap[key]
    : {};
  const wordpressName = wpEntry?.title?.rendered || payload.title;
  authorsMap[key] = {
    ...current,
    slug: current.slug || key,
    name: current.name || payload.title,
    wordpress_id: wpEntry?.id,
    wordpress_name: wordpressName,
    exists_local: true,
  };
  return authorsMap;
}

async function loadJsonFile(requiredPath, label) {
  const absPath = path.resolve(requiredPath);
  try {
    const raw = await readFile(absPath, "utf8");
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      throw new Error(`${label} must be a JSON object.`);
    }
    return { data: parsed, path: absPath };
  } catch (error) {
    throw new Error(
      `Failed to load ${label} at ${absPath}: ${error.message}`,
    );
  }
}

async function getMarkdownFiles(paths) {
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

function formatTeamEntry(entry) {
  const title = entry?.title?.rendered || entry?.name || "";
  const jobTitle =
    entry.job_title ||
    entry.meta?.job_title ||
    entry.pods?.job_title ||
    "";
  const slug = entry.slug || entry.post_name || "";
  return [entry.id, title.trim(), slug, jobTitle].filter(Boolean).join(" | ");
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage(
      "Upload one or more people markdown files to the WordPress `team` post type.\n\nUsage: $0 [options] <paths...>\n\nExamples:\n  $0 --list\n  $0 next.lifeitself.org/people/alexia.md\n  $0 next.lifeitself.org/people/  # uploads all people files in the folder\n\nSlug comes from front matter id/slug or the filename; name is required. Status defaults to publish. By default the script aborts if a matching name/slug exists; pass --override to update instead.",
    )
    .option("override", {
      alias: "o",
      type: "boolean",
      default: false,
      describe: "Update an existing team entry if it already exists.",
    })
    .option("list", {
      type: "boolean",
      default: false,
      describe:
        "List existing team members instead of uploading (ignores paths).",
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
      describe:
        "Path to authors mapping JSON to update with new WordPress IDs.",
    })
    .epilogue(
      "Markdown expectations: front matter must include name; optional id/slug sets the slug (otherwise filename is used); status defaults to publish.\n\nUploads will create the WordPress `team` CPT entry; use --override to update when a matching slug/name exists. Avatar is resolved through the media map and set as featured image. Authors mapping is updated with the WordPress ID for the uploaded person.",
    )
    .help()
    .alias("h", "help")
    .strict()
    .wrap(null)
    .argv;

  if (!argv.list && argv._.length === 0) {
    yargs(hideBin(process.argv)).showHelp();
    return;
  }

  let mediaMap = {};
  let authors = {};
  let authorsPath;
  if (!argv.list) {
    const mapping = await loadJsonFile(argv.mapping, "media mapping");
    mediaMap = mapping.data;
    const authorsLoaded = await loadJsonFile(argv.authors, "authors mapping");
    authors = authorsLoaded.data;
    authorsPath = authorsLoaded.path;
  }

  const client = createWpClient({
    baseUrl: process.env.WP_BASE_URL,
    username: process.env.WP_USERNAME,
    appPassword: process.env.WP_APP_PASSWORD,
  });

  if (argv.list) {
    const members = await listTeamMembers(client);
    members.forEach((entry) => console.log(formatTeamEntry(entry)));
    return;
  }

  const filePaths = await getMarkdownFiles(argv._);
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
      const { result, action } = await upsertTeamMember(client, payload, {
        override: argv.override,
      });
      const verb = action === "updated" ? "Updated" : "Created";
      console.log(
        `${verb} ${path.basename(filePath)} -> ${result.slug} (id ${result.id})`,
      );
      authors = updateAuthorsRecord(authors, payload, result);
      authorsDirty = true;
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

if (process.argv[1] && path.resolve(process.argv[1]) === __filename) {
  main().catch((error) => {
    console.error("An unexpected error occurred:", error.message);
    process.exit(1);
  });
}

export { updateAuthorsRecord };
