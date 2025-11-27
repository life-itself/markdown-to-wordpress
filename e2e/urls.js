const oldSite = "https://lifeitself.org";
const newSite = "http://next.lifeitself.org";

// List of old URLs to test
const pagePaths = ["/", "/hubs", "/research"];

const blogPostPaths = [
  "blog/emergent-power-report-2024.md",
  "blog/atomic-habits-by-james-clear-summary-and-notes.md",
  "blog/2021/consciouscoliving-website-launch.md",
  "blog/what-I-took-from-the-life-itself-values-jam.md",
  "blog/can-new-social-and-digital-technologies-transform-governance.md",
];

// Combine page and blog paths into a single array
const oldPaths = [...pagePaths, ...blogPostPaths];

/**
 * Build absolute URLs from a base site and a list of paths.
 * Uses the URL constructor to resolve paths robustly, and falls back
 * to string concatenation if URL construction fails.
 */
const buildUrls = (base, paths) =>
  paths.map((p) => {
    try {
      return new URL(p, base).toString();
    } catch (e) {
      const trimmedBase = base.replace(/\/$/, "");
      const trimmedPath = p.replace(/^\/+/, "");
      return `${trimmedBase}/${trimmedPath}`;
    }
  });

// Construct the arrays of full URLs for the old and new sites
const oldUrls = buildUrls(oldSite, oldPaths);
const newUrls = buildUrls(newSite, oldPaths);

const oldNewUrls = oldUrls.map((url, index) => ({
  old: url,
  new: newUrls[index],
}));

export { oldNewUrls };
