import 'dotenv/config';
import path from 'node:path';
import {convertMarkdownToPost} from './src/markdownProcessor.js';
import {createWpClient, uploadToWordpress} from './src/wpUploader.js';

async function main() {
  const markdownPath = path.resolve('sample-post.md');
  const {payload} = await convertMarkdownToPost(markdownPath);

  const client = createWpClient({
    baseUrl: process.env.WP_BASE_URL,
    username: process.env.WP_USERNAME,
    appPassword: process.env.WP_APP_PASSWORD
  });

  const response = await uploadToWordpress(client, payload);
  console.log('Post uploaded successfully:', {
    id: response?.id,
    link: response?.link,
    status: response?.status
  });
}

main().catch((error) => {
  console.error('Failed to upload post:', error.message);
  process.exit(1);
});
