# WordPress.com Setup Guide

## Quick Start (3 Steps)

### 1. Get Your WordPress.com OAuth Token

1. **Create a WordPress.com App**:
   - Go to: https://developer.wordpress.com/apps/
   - Click "Create New Application"
   - Fill in:
     - **Name**: `Markdown Migration`
     - **Description**: `Migration tool`
     - **Website URL**: `http://localhost`
     - **Redirect URLs**: `http://localhost:8080/callback`
     - **Type**: `Web`

2. **Get Your Token**:
   - After creating the app, note your **Client ID**
   - Visit this URL (replace `YOUR_CLIENT_ID`):
   ```
   https://public-api.wordpress.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&response_type=token&scope=global
   ```
   - Authorize the app
   - You'll be redirected to a 404 page - **this is normal!**
   - Copy the `access_token` from the URL (everything between `access_token=` and `&expires_in`)

### 2. Configure Your Environment

1. **Copy the example**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`**:
   ```
   WORDPRESS_SITE_DOMAIN=yoursite.wordpress.com
   WORDPRESS_OAUTH_TOKEN=your-token-here
   ```

### 3. Test Your Setup

```bash
python etl/test_connection.py
```

## Migration Usage

```bash
# Run the ETL pipeline
python etl/run_pipeline.py --input path/to/your/content

# Test individual steps
python etl/run_pipeline.py --test 0-image-processing
```

## Security Notes

- ✅ **Tokens are in `.env`** (gitignored - never committed)
- ✅ **No hardcoded credentials** in code
- ✅ **Secure by default** - all sensitive files ignored

## Troubleshooting

**"Token expired"**: WordPress.com tokens expire in ~14 days. Simply get a new one.

**"Site not found"**: Make sure `WORDPRESS_SITE_DOMAIN` is just the domain (no https://).

**"Permission denied"**: Your token might need the `global` scope. Re-authorize with the URL above.

---

That's it! The setup is designed to be secure and simple. 🚀