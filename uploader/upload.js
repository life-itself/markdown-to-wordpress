import "dotenv/config";
import { stat, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import {
  convertMarkdownToPost,
  createWpClient,
  upsertPostToWordpress,
  prepareWordpressPayload,
} from "./src/lib.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_MAPPING_PATH = path.join(__dirname, "uploadMediaMap.json");
const DEFAULT_AUTHORS_PATH = path.join(__dirname, "authors.json");

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

async function loadMediaMap(mappingPath) {
  try {
    const raw = await readFile(mappingPath, "utf8");
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed;
    }
  } catch (error) {
    const message =
      error.code === "ENOENT"
        ? `Media mapping not found at ${mappingPath}. Skipping image rewriting.`
        : `Could not read media mapping at ${mappingPath}: ${error.message}`;
    console.warn(message);
  }
  return {};
}

async function loadAuthorsMap(authorsPath) {
  try {
    const raw = await readFile(authorsPath, "utf8");
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed;
    }
  } catch (error) {
    const message =
      error.code === "ENOENT"
        ? `Author mapping not found at ${authorsPath}. Skipping author assignment.`
        : `Could not read author mapping at ${authorsPath}: ${error.message}`;
    console.warn(message);
  }
  return {};
}

async function uploadFile(
  client,
  filePath,
  mediaMap,
  authorsMap,
  useRelativeUrls = true,
) {
  try {
    const raw = await readFile(filePath, "utf8");
    const { payload } = await convertMarkdownToPost(raw, {
      sourcePath: filePath,
      mediaMap,
      useRelativeUrls,
    });
    const preparedPayload = prepareWordpressPayload(payload, {
      authorsMap,
      logger: console,
    });
    const response = await upsertPostToWordpress(client, preparedPayload); // Use upsert function
    const action = response.id === payload.id ? "Updated" : "Uploaded"; // Differentiate update/create
    console.log(`${action} ${path.basename(filePath)}: ${response.link}`);
  } catch (error) {
    console.error(
      `Failed to upload ${path.basename(filePath)}: ${error.message}`,
    );
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage("Usage: $0 <paths...>")
    .option("mapping", {
      alias: "m",
      type: "string",
      describe: "Path to uploadMediaMap.json for rewriting image links",
      default: DEFAULT_MAPPING_PATH,
    })
    .option("authors", {
      alias: "a",
      type: "string",
      describe:
        "Path to authors.json mapping file (defaults to authors.json in this directory)",
      default: DEFAULT_AUTHORS_PATH,
    })
    .option("absolute-media-urls", {
      type: "boolean",
      default: false,
      describe: "Use absolute media URLs instead of relative paths when rewriting content.",
    })
    .demandCommand(1, "You must provide at least one file or directory path.")
    .help().argv;

  const filePaths = await getMarkdownFiles(argv._);

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

  const mappingPath = path.resolve(argv.mapping);
  const mediaMap = await loadMediaMap(mappingPath);
  if (mediaMap && Object.keys(mediaMap).length > 0) {
    console.log(
      `Loaded ${Object.keys(mediaMap).length} media mapping entries from ${mappingPath}.`,
    );
  }

  const authorsPath = path.resolve(argv.authors);
  const authorsMap = await loadAuthorsMap(authorsPath);
  if (authorsMap && Object.keys(authorsMap).length > 0) {
    console.log(
      `Loaded ${Object.keys(authorsMap).length} author mapping entries from ${authorsPath}.`,
    );
  }

  for (const filePath of filePaths) {
    await uploadFile(
      client,
      filePath,
      mediaMap,
      authorsMap,
      !argv["absolute-media-urls"],
    );
  }
}

main().catch((error) => {
  console.error("An unexpected error occurred:", error.message);
  process.exit(1);
});
