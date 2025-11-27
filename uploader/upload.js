import "dotenv/config";
import { stat, readFile } from "node:fs/promises";
import path from "node:path";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import {
  convertMarkdownToPost,
  createWpClient,
  upsertPostToWordpress,
} from "./src/lib.js";

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

async function uploadFile(client, filePath) {
  try {
    const raw = await readFile(filePath, "utf8");
    const { payload } = await convertMarkdownToPost(raw, {
      sourcePath: filePath,
    });
    const response = await upsertPostToWordpress(client, payload); // Use upsert function
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

  for (const filePath of filePaths) {
    await uploadFile(client, filePath);
  }
}

main().catch((error) => {
  console.error("An unexpected error occurred:", error.message);
  process.exit(1);
});
