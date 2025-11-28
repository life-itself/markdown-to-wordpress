import "dotenv/config";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readFile, writeFile, stat, appendFile } from "node:fs/promises";
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
const SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const IS_TTY = Boolean(process.stdout && process.stdout.isTTY);
let spinnerTimer = null;
let spinnerIndex = 0;
let lastRenderLength = 0;
let lastLine2Length = 0;
let lastLine3Length = 0;

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
  const maxLen = Math.max(lastRenderLength, lastLine2Length, lastLine3Length);
  const blank = " ".repeat(maxLen || 0);
  process.stdout.write(`\r${blank}\r`);
  process.stdout.write(`\n${blank}\r`);
  process.stdout.write(`\n${blank}\r`);
  process.stdout.write("\x1b[3A"); // move cursor up 3 lines
  lastRenderLength = 0;
  lastLine2Length = 0;
  lastLine3Length = 0;
}

function renderSpinner(state) {
  if (!IS_TTY) return;
  const frame = SPINNER_FRAMES[spinnerIndex % SPINNER_FRAMES.length];
  spinnerIndex += 1;
  const percent =
    state.total > 0 ? Math.round((state.processed / state.total) * 100) : 0;
  const activeList =
    state.active.size > 0
      ? Array.from(state.active).slice(0, 3).join(", ")
      : "-";

  const line1 = `${frame} uploading ${state.processed}/${state.total} (${percent}%) | uploaded:${state.uploaded} skipped:${state.skipped} failed:${state.failed}`;
  const line2 = `current: ${activeList}`;
  const line3 = `last: ${state.last || "-"}`;

  const pad1 =
    lastRenderLength > line1.length ? lastRenderLength - line1.length : 0;
  const pad2 =
    lastLine2Length > line2.length ? lastLine2Length - line2.length : 0;
  const pad3 =
    lastLine3Length > line3.length ? lastLine3Length - line3.length : 0;

  process.stdout.write(`\r${line1}${" ".repeat(pad1)}\n`);
  process.stdout.write(`${line2}${" ".repeat(pad2)}\n`);
  process.stdout.write(`${line3}${" ".repeat(pad3)}`);
  process.stdout.write("\x1b[3A"); // move cursor back up

  lastRenderLength = line1.length;
  lastLine2Length = line2.length;
  lastLine3Length = line3.length;
}

function startSpinner(state) {
  if (!IS_TTY) return;
  spinnerTimer = setInterval(() => renderSpinner(state), 80);
}

function stopSpinner(state) {
  if (!IS_TTY) return;
  if (spinnerTimer) clearInterval(spinnerTimer);
  renderSpinner(state);
  process.stdout.write("\n\n\n");
  spinnerTimer = null;
  lastRenderLength = 0;
  lastLine2Length = 0;
  lastLine3Length = 0;
}

function logWithSpinnerPause(state, message) {
  if (!IS_TTY) {
    console.log(message);
    return;
  }
  clearSpinnerLines();
  console.log(message);
  renderSpinner(state);
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
  const errorLogPath = `${mappingPath}.errors.txt`;
  const logErrorLine = createErrorLogger(errorLogPath);
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
      ({ buffer, hash } = await readFileBufferAndHash(absPath));
    } catch (error) {
      state.failed += 1;
      logWithSpinnerPause(
        state,
        `[fail] ${absPath}: ${error.message}`,
      );
      await logErrorLine(`${absPath} 0`);
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
      state.uploaded += 1;
      state.last = `[upload] ${path.basename(absPath)}`;
    } catch (error) {
      state.failed += 1;
      logWithSpinnerPause(
        state,
        `[fail] ${absPath}: ${error.message}`,
      );
      state.last = `[fail] ${path.basename(absPath)}`;
      const statusCode =
        typeof error.status === "number" ? error.status : "0";
      await logErrorLine(`${absPath} ${statusCode}`);
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

main().catch((error) => {
  console.error("Fatal error:", error.message);
  process.exit(1);
});
