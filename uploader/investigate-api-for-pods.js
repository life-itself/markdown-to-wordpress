import "dotenv/config";
import { createWpClient } from "./src/lib.js";

async function fetchPostWithMeta(client, slug) {
  // Request edit context to include protected meta fields
  const response = await client.posts().slug(slug).get();
  return response[0];
}

async function main() {
  const [slugFromArg] = process.argv.slice(2);
  const slug = slugFromArg || "second-renaissance-name-why";

  if (!slug) {
    throw new Error("Please pass a slug to inspect.");
  }

  const baseUrl = process.env.WP_BASE_URL;
  const username = process.env.WP_USERNAME;
  const appPassword = process.env.WP_APP_PASSWORD;

  const client = createWpClient({
    baseUrl,
    username,
    appPassword,
  });

  const post = await fetchPostWithMeta(client, slug);

  const { id, slug: resolvedSlug, link, meta, pods = undefined } = post;
  console.log(JSON.stringify(post, null, 2));
  console.log(
    JSON.stringify(
      {
        id,
        slug: resolvedSlug,
        link,
        meta,
        pods,
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error("Failed to inspect WordPress API:", error);
  process.exit(1);
});
