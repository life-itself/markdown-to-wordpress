import { stat, readFile } from "node:fs/promises";
import path from "node:path";
import { glob } from "glob";
import { Minimatch } from "minimatch";

function buildExcludeMatchers(patterns = []) {
  return patterns
    .filter(Boolean)
    .map((pattern) => new Minimatch(pattern, { matchBase: true, dot: true }));
}

export async function loadExcludePatterns(filePath) {
  if (!filePath) return [];
  const absPath = path.resolve(filePath);
  try {
    const raw = await readFile(absPath, "utf8");
    return raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  } catch (error) {
    if (error.code !== "ENOENT") {
      console.warn(
        `Could not read exclude patterns from ${absPath}: ${error.message}`,
      );
    }
    return [];
  }
}

export async function getMarkdownFiles(
  paths = [],
  { recurse = true, excludeGlobs = [] } = {},
) {
  const filePaths = new Set();

  for (const p of paths) {
    let stats;
    try {
      stats = await stat(p);
    } catch (error) {
      console.warn(`Skipping ${p}: ${error.message}`);
      continue;
    }

    if (stats.isDirectory()) {
      const pattern = recurse ? "**/*.md" : "*.md";
      const files = await glob(pattern, {
        cwd: p,
        absolute: true,
        nodir: true,
      });
      files.forEach((file) => filePaths.add(path.resolve(file)));
    } else if (p.endsWith(".md")) {
      filePaths.add(path.resolve(p));
    }
  }

  const matchers = buildExcludeMatchers(excludeGlobs);
  const filtered = Array.from(filePaths).filter((file) => {
    if (matchers.length === 0) return true;
    const basename = path.basename(file);
    return !matchers.some(
      (matcher) => matcher.match(file) || matcher.match(basename),
    );
  });

  return filtered.sort((a, b) => a.localeCompare(b));
}
