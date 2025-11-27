# Content Migration Verification

This project contains end-to-end tests to verify content migration from an old system to a new system.

## Prerequisites

- Node.js
- npm

## Installation

1. Clone the repository.
2. Install the dependencies:
   ```bash
   npm install
   ```

## Running the Tests

To run the tests, execute the following command:

```bash
npm test
```

## Configuration

The tests are configured using the `urls.js` file.

- `oldUrls`: A list of URLs from the old system to be tested.
- `newBaseUrl`: The base URL of the new system.