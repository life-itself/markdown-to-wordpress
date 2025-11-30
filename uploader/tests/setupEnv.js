import path from "node:path";
import { existsSync } from "node:fs";
import dotenv from "dotenv";

const envPath = path.resolve(process.cwd(), ".env.test");

if (!existsSync(envPath)) {
  throw new Error(
    `Missing ${envPath}. Copy .env.sample to .env.test with test credentials before running tests.`,
  );
}

process.env.DOTENV_CONFIG_PATH = envPath;
process.env.DOTENV_CONFIG_OVERRIDE = "true";

const { parsed } = dotenv.config({ path: envPath, override: true });
const requiredKeys = ["WP_BASE_URL", "WP_USERNAME", "WP_APP_PASSWORD"];
const missing = requiredKeys.filter((key) => !parsed?.[key]);

if (missing.length > 0) {
  throw new Error(
    `Missing required variables in .env.test: ${missing.join(", ")}.`,
  );
}
