import { describe, it, expect, vi, beforeEach } from "vitest";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import {
  convertMarkdownToPage,
  upsertPageToWordpress,
} from "../src/lib.js";
import {
  getMarkdownFiles,
  loadExcludePatterns,
} from "../src/fileDiscovery.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const fixturesDir = path.join(__dirname, "fixtures");
const pagesDir = path.join(fixturesDir, "pages");

describe("convertMarkdownToPage", () => {
  it("uses filename stem for slug even when front matter slug is present", async () => {
    const sourcePath = path.join(pagesDir, "about.md");
    const raw = await readFile(sourcePath, "utf8");

    const { payload } = await convertMarkdownToPage(raw, {
      sourcePath,
    });

    expect(payload.slug).toBe("about");
  });
});

describe("getMarkdownFiles with excludes and recursion", () => {
  it("applies exclude globs to discovered markdown files", async () => {
    const excludeFile = path.join(fixturesDir, "exclude-patterns.txt");
    const excludes = await loadExcludePatterns(excludeFile);

    const files = await getMarkdownFiles([pagesDir], {
      recurse: false,
      excludeGlobs: excludes,
    });

    const basenames = files.map((f) => path.basename(f)).sort();
    expect(basenames).toEqual(["about.md"]);
  });

  it("honors recurse flag when walking directories", async () => {
    const files = await getMarkdownFiles([pagesDir], {
      recurse: true,
      excludeGlobs: [],
    });

    const basenames = files.map((f) => path.relative(pagesDir, f)).sort();
    expect(basenames).toEqual(["about.md", "index.md", "nested/contact.md"]);
  });
});

describe("upsertPageToWordpress", () => {
  let mockPagesChain;
  let mockClient;

  beforeEach(() => {
    mockPagesChain = {
      slug: vi.fn(() => mockPagesChain),
      get: vi.fn(),
      create: vi.fn(),
      id: vi.fn(() => mockPagesChain),
      update: vi.fn(),
    };
    mockClient = {
      pages: vi.fn(() => mockPagesChain),
    };
  });

  it("creates a page when no existing page matches the slug", async () => {
    mockPagesChain.get.mockResolvedValue([]);
    mockPagesChain.create.mockResolvedValue({ id: 99, link: "new-page-link" });

    const payload = { title: "New Page", content: "...", slug: "new-page" };
    const result = await upsertPageToWordpress(mockClient, payload);

    expect(mockPagesChain.slug).toHaveBeenCalledWith("new-page");
    expect(mockPagesChain.create).toHaveBeenCalledWith(
      expect.objectContaining({ slug: "new-page" }),
    );
    expect(result).toEqual({ action: "created", page: { id: 99, link: "new-page-link" } });
  });

  it("skips upload when a page with the slug already exists", async () => {
    const existing = { id: 5, slug: "existing-page", link: "existing-link" };
    mockPagesChain.get.mockResolvedValue([existing]);

    const payload = { title: "Existing Page", content: "...", slug: "existing-page" };
    const result = await upsertPageToWordpress(mockClient, payload);

    expect(mockPagesChain.create).not.toHaveBeenCalled();
    expect(result).toEqual({ action: "skipped", page: existing });
  });
});
