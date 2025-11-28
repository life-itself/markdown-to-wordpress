import "dotenv/config";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readFile, writeFile, stat } from "node:fs/promises";
import crypto from "node:crypto";
import { Blob } from "node:buffer";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

const SUPPORTED_IMAGE_EXTENSIONS = [
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
];
const IMAGE_EXTENSION_SET = new Set(
  SUPPORTED_IMAGE_EXTENSIONS.map((ext) => `.${ext}`),
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
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_MAPPING_PATH = path.join(__dirname, "media-mapping.json");

function sanitizeBaseUrl(url) {
  if (!url) return url;
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

function isImageFile(filePath) {
  return IMAGE_EXTENSION_SET.has(path.extname(filePath).toLowerCase());
}

async function collectImageFiles(inputs) {
  const files = new Set();
  const pattern = `**/*.{${SUPPORTED_IMAGE_EXTENSIONS.join(",")}}`;

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
      if (!isImageFile(targetPath)) {
        console.warn(`Skipping ${targetPath}: not a supported image type.`);
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

async function readFileBufferAndHash(filePath) {
  const buffer = await readFile(filePath);
  const hash = crypto.createHash("sha256").update(buffer).digest("hex");
  return { buffer, hash };
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
    throw new Error(
      `Failed to upload ${fileName} (status ${response.status}): ${bodyText}`,
    );
  }

  return JSON.parse(bodyText);
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage("Usage: $0 <files-or-directories...>")
    .option("mapping", {
      alias: "m",
      type: "string",
      describe: "Path to media-mapping.json",
      default: DEFAULT_MAPPING_PATH,
    })
    .demandCommand(1, "Provide at least one file or directory path.")
    .help().argv;

  const config = getWordpressConfig();
  const mappingPath = path.resolve(argv.mapping);
  const imageFiles = await collectImageFiles(argv._);

  if (imageFiles.length === 0) {
    console.log("No image files found to upload.");
    return;
  }

  const mapping = await loadMapping(mappingPath);
  let uploads = 0;
  let skipped = 0;
  let failures = 0;

  console.log(`Found ${imageFiles.length} image file(s) to process.`);

  for (const filePath of imageFiles) {
    const absPath = path.resolve(filePath);
    let buffer;
    let hash;
    try {
      ({ buffer, hash } = await readFileBufferAndHash(absPath));
    } catch (error) {
      console.error(`Failed to read ${absPath}: ${error.message}`);
      failures += 1;
      continue;
    }

    const existing = mapping[absPath];
    if (existing && existing.hash === hash && existing.url) {
      console.log(`[skip] ${absPath} already uploaded -> ${existing.url}`);
      skipped += 1;
      continue;
    }

    if (existing && existing.hash !== hash) {
      console.log(
        `[reupload] ${absPath} changed since last upload (hash mismatch).`,
      );
    }

    try {
      const media = await uploadMediaFile({ buffer, filePath: absPath, hash, config });
      const destinationUrl =
        media?.source_url || media?.guid?.rendered || media?.link || null;
      mapping[absPath] = {
        hash,
        url: destinationUrl,
        id: media.id,
        fileName: path.basename(absPath),
        uploadedAt: new Date().toISOString(),
      };
      console.log(`[upload] ${absPath} -> ${destinationUrl ?? media.id}`);
      uploads += 1;
    } catch (error) {
      console.error(`Failed to upload ${absPath}: ${error.message}`);
      failures += 1;
    }
  }

  await saveMapping(mappingPath, mapping);

  console.log(
    `Done. Uploaded: ${uploads}, Skipped: ${skipped}, Failed: ${failures}. Mapping saved to ${mappingPath}.`,
  );

  if (failures > 0) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error("Fatal error:", error.message);
  process.exit(1);
});
