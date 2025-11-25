import {describe, expect, it} from 'vitest';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {convertMarkdownToPost, normalizeTags} from '../src/markdownProcessor.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const fixturesDir = path.join(__dirname, 'fixtures');

describe('convertMarkdownToPost', () => {
  it('parses front matter and converts markdown to HTML with gfm support', async () => {
    const fixturePath = path.join(fixturesDir, 'post.md');
    const {payload, htmlContent} = await convertMarkdownToPost(fixturePath);

    expect(payload).toMatchObject({
      title: 'Fixture Title',
      status: 'publish',
      slug: 'fixture-title',
      excerpt: expect.stringContaining('Quick summary')
    });
    expect(htmlContent).toContain('<strong>');
    expect(htmlContent).toContain('<sup');
  });

  it('applies sensible defaults when optional fields are missing', async () => {
    const fixturePath = path.join(fixturesDir, 'minimal.md');
    const {payload} = await convertMarkdownToPost(fixturePath);

    expect(payload.status).toBe('draft');
    expect(payload.slug).toBeUndefined();
  });
});

describe('normalizeTags', () => {
  it('normalizes string inputs to arrays', () => {
    expect(normalizeTags('alpha')).toEqual(['alpha']);
  });

  it('returns undefined when tags are missing or empty', () => {
    expect(normalizeTags(undefined)).toBeUndefined();
    expect(normalizeTags([])).toBeUndefined();
  });
});
