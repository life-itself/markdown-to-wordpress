import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import matter from "gray-matter";
import { glob } from "glob";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CONTENT_ROOT = path.join(__dirname, "next.lifeitself.org");
const PEOPLE_DIR = path.join(CONTENT_ROOT, "people");

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
    const parts = raw.split(",").map((part) => part.trim());
    parts.forEach((part) => {
      if (part) result.push(part);
    });
  };
  add(value);
  return result;
}

function extractAuthorIds(frontmatter) {
  if (!frontmatter || typeof frontmatter !== "object") return [];
  const ids = [];
  ids.push(...normalizeAuthorValues(frontmatter.author));
  ids.push(...normalizeAuthorValues(frontmatter.authors));
  return ids;
}

async function collectAuthorIds(baseDir) {
  const files = await glob("**/*.md", {
    cwd: baseDir,
    absolute: true,
    ignore: ["people/**", "node_modules/**"],
  });

  const ids = new Set();

  for (const filePath of files) {
    const raw = await readFile(filePath, "utf8");
    const { data } = matter(raw);
    const authorIds = extractAuthorIds(data);
    authorIds.forEach((id) => ids.add(id));
  }

  return Array.from(ids);
}

async function resolvePeople(authorIds, peopleDir) {
  const results = [];
  for (const id of authorIds) {
    const personPath = path.join(peopleDir, `${id}.md`);
    try {
      const raw = await readFile(personPath, "utf8");
      const { data } = matter(raw);
      const name = data.name || data.title || data.full_name || data.fullName;
      results.push({
        id,
        name: name ? String(name).trim() : null,
        missing: false,
      });
    } catch (error) {
      if (error.code === "ENOENT") {
        results.push({ id, name: null, missing: true });
      } else {
        throw error;
      }
    }
  }
  return results;
}

function printResults(authorIds, resolved) {
  console.log(`Unique author IDs (${authorIds.length}):`);
  authorIds.forEach((id) => console.log(`- ${id}`));

  console.log("\nResolved names:");
  resolved.forEach(({ id, name, missing }) => {
    if (missing) {
      console.log(`${id} (missing people file)`);
    } else if (!name) {
      console.log(`${id} (name missing in people file)`);
    } else {
      console.log(`${id} ${name}`);
    }
  });
}

async function main() {
  const authorIds = await collectAuthorIds(CONTENT_ROOT);
  const sortedIds = authorIds.sort((a, b) => a.localeCompare(b));
  const resolved = await resolvePeople(sortedIds, PEOPLE_DIR);
  printResults(sortedIds, resolved);
}

main().catch((error) => {
  console.error("Failed to list authors:", error);
  process.exit(1);
});
