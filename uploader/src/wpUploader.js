import WPAPI from 'wpapi';

function sanitizeBaseUrl(url) {
  return url.endsWith('/') ? url.slice(0, -1) : url;
}

export function createWpClient({baseUrl, username, appPassword}) {
  if (!baseUrl || !username || !appPassword) {
    throw new Error('Missing WordPress credentials (WP_BASE_URL, WP_USERNAME, WP_APP_PASSWORD).');
  }

  const endpoint = `${sanitizeBaseUrl(baseUrl)}/wp-json`;
  return new WPAPI({
    endpoint,
    username,
    password: appPassword
  });
}

export async function uploadToWordpress(client, payload) {
  if (!client) throw new Error('A configured WPAPI client is required.');
  if (!payload) throw new Error('No payload provided to upload.');
  return client.posts().create(payload);
}
