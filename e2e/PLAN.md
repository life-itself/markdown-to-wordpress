## Content Migration Verification Issue

The objective is to create **functional end-to-end tests** using **Node.js** to verify successful content migration from an old system to a new system. The tests must confirm that migrated pages exist (no 404s) and that the core content is **reasonably similar** despite underlying HTML differences. The tests should be executable via `npm test` using a standard Node testing framework (probably vitest).

## ✅ Acceptance Criteria (Incremental)

* [ ] **Criterion 1 (Existence Check):** The code successfully iterates through a provided list of **old URLs**, constructs the corresponding **new URLs** (using the new base URL), and verifies that each new URL returns a **200 OK** status code (i.e., does not 404).
* [ ] **Criterion 2 (Title Check):** For each successfully loaded new page, the test extracts the page **title** (from the `<title>` tag) and compares it to the title from the old page. The test should pass if the titles are within a high similarity threshold (e.g., using a string distance metric or simple inclusion/length check).
* [ ] **Criterion 3 (Body Content Check):** For each pair of URLs, the test extracts key structural or body content (e.g., main article text, specific metadata) and performs a **fuzzy comparison** (e.g., checking for the presence of key sentences/paragraphs, or using a text similarity score) to ensure content fidelity.

## 🛠️ Tasks

### 1. Write the 404 Check

* **Input:** A list of old URLs and the new URLs configured from a list of paths, old base url and new base url.
* **Action:** Implement a Node.js test using a chosen framework that fetches the calculated new URLs and asserts a **200 HTTP status code**.
* **Output:** The test file, a minimal `package.json` with necessary dependencies (e.g., `axios` for fetching, plus the testing framework), and a simple `README.md` explaining how to run the test with `npm test`.

## Notes

- Use vitest in `--run` mode to avoid hanging (defaults to watch mode)
- Tests *should* fail initially because the content will not exist. these are "black-box" functional tests on an external system (not local unit tests).
- I want the tests here in this directory to run over all urls and report on those that are broken and not just fail on the first on that is broken.
