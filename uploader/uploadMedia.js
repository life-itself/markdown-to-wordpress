import "dotenv/config";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readFile, writeFile, stat } from "node:fs/promises";
import crypto from "node:crypto";
import { Blob } from "node:buffer";
import { glob } from "glob";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

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

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DEFAULT_MAPPING_PATH = path.join(__dirname, "uploadMediaMap.json");
const DEFAULT_CONCURRENCY = 5;

function sanitizeBaseUrl(url) {
  if (!url) return url;
  return url.endsWith("/") ? url.slice(0, -1) : url;
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

function formatPercent(numerator, denominator) {
  if (!denominator) return 100;
  return Math.round((numerator / denominator) * 100);
}

function renderStatus({
  processed,
  total,
  uploads,
  skipped,
  failures,
  active,
  last,
}) {
  const percent = formatPercent(processed, total);
  const activeList = active.size > 0 ? Array.from(active).join(", ") : "-";
  const line = `Progress ${processed}/${total} (${percent}%) | uploads:${uploads} skipped:${skipped} failed:${failures} | active: ${activeList} | last: ${last || "-"}`;
  renderStatus.lastLength = Math.max(renderStatus.lastLength || 0, line.length);
  const padded = line.padEnd(renderStatus.lastLength, " ");
  process.stdout.write(`\r${padded}`);
}

function finishStatusLine() {
  if (renderStatus.lastLength) {
    process.stdout.write("\n");
  }
}

async function main() {
  const argv = await yargs(hideBin(process.argv))
    .usage("Usage: $0 <files-or-directories...>")
    .option("mapping", {
      alias: "m",
      type: "string",
      describe: "Path to uploadMediaMap.json",
      default: DEFAULT_MAPPING_PATH,
    })
    .option("concurrency", {
      alias: "c",
      type: "number",
      describe: "How many uploads to run in parallel",
      default: DEFAULT_CONCURRENCY,
    })
    .demandCommand(1, "Provide at least one file or directory path.")
    .help().argv;

  const config = getWordpressConfig();
  const mappingPath = path.resolve(argv.mapping);
  const mediaFiles = await collectMediaFiles(argv._);
  const concurrency = Math.max(1, Math.floor(argv.concurrency || 1));

  if (mediaFiles.length === 0) {
    console.log("No media files found to upload.");
    return;
  }

  const mapping = await loadMapping(mappingPath);
  const saveMappingSafely = createSerializedSaver(mappingPath, mapping);
  const active = new Set();
  let uploads = 0;
  let skipped = 0;
  let failures = 0;
  let processed = 0;
  let lastMessage = "-";

  console.log(
    `Found ${mediaFiles.length} media file(s) to process. Running with concurrency ${concurrency}.`,
  );

  const updateStatus = () => {
    renderStatus({
      processed,
      total: mediaFiles.length,
      uploads,
      skipped,
      failures,
      active,
      last: lastMessage,
    });
  };

  const processFile = async (filePath) => {
    const absPath = path.resolve(filePath);
    const key = path.basename(absPath);
    active.add(path.basename(absPath));
    updateStatus();
    let buffer;
    let hash;
    try {
      ({ buffer, hash } = await readFileBufferAndHash(absPath));
    } catch (error) {
      failures += 1;
      lastMessage = `[fail] ${absPath}: ${error.message}`;
      active.delete(path.basename(absPath));
      processed += 1;
      updateStatus();
      return;
    }

    const existing = mapping[key];
    if (existing && existing.hash === hash && existing.url) {
      skipped += 1;
      lastMessage = `[skip] ${absPath} -> ${existing.url}`;
      active.delete(path.basename(absPath));
      processed += 1;
      updateStatus();
      return;
    }

    if (existing && existing.hash !== hash) {
      lastMessage = `[reupload] ${absPath} (hash changed)`;
    }

    try {
      const media = await uploadMediaFile({ buffer, filePath: absPath, hash, config });
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
      uploads += 1;
      lastMessage = `[upload] ${absPath} -> ${destinationUrl ?? media.id}`;
    } catch (error) {
      failures += 1;
      lastMessage = `[fail] ${absPath}: ${error.message}`;
      console.error(`Failed to upload ${absPath}: ${error.message}`);
    } finally {
      active.delete(path.basename(absPath));
      processed += 1;
      updateStatus();
    }
  };

  const finalSaveOnExit = async () => {
    await saveMappingSafely();
  };

  process.on("SIGINT", async () => {
    console.warn("\nReceived SIGINT, saving mapping before exit...");
    await finalSaveOnExit();
    finishStatusLine();
    process.exit(1);
  });
  process.on("uncaughtException", async (error) => {
    console.error("\nUncaught exception:", error);
    await finalSaveOnExit();
    finishStatusLine();
    process.exit(1);
  });
  process.on("unhandledRejection", async (reason) => {
    console.error("\nUnhandled rejection:", reason);
    await finalSaveOnExit();
    finishStatusLine();
    process.exit(1);
  });

  await runWithConcurrency(mediaFiles, concurrency, processFile);
  await finalSaveOnExit();
  finishStatusLine();

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
