import { test, expect } from "vitest";
import axios from "axios";
import { oldNewUrls } from "./urls.js";

// Test suite for 404 checks
test("check for 404s", async () => {
  for (const urlPair of oldNewUrls) {
    const newUrl = urlPair.new;
    try {
      const response = await axios.get(newUrl);
      expect(response.status).toBe(200);
    } catch (error) {
      // If the request fails, we'll fail the test
      // and log the error.
      console.error(`Failed to fetch ${newUrl}:`, error.message);
      throw error;
    }
  }
});
