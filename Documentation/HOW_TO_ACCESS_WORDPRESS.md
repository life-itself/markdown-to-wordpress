# How to Access Your WordPress Posts

## After Running the Migration

Once you run the migration command successfully, your markdown files will be converted to WordPress posts. Here's how to find and access them:

## 1. WordPress Admin Dashboard

Go to your WordPress admin area:
```
https://your-wordpress-site.com/wp-admin/
```

### Find Your Posts:
- **Blog Posts**: Go to `Posts → All Posts`
- **Pages**: Go to `Pages → All Pages` 
- **Events**: Go to `Events → All Events` (if custom post type exists)

## 2. View Posts on Your Website

Your posts will be accessible at these URLs:

### About Page:
```
https://your-wordpress-site.com/about/
```

### Community Blog Post:
```
https://your-wordpress-site.com/community/
```

### Event Page:
```
https://your-wordpress-site.com/events/conscious-coliving-retreat-spring-2024/
```

## 3. What You Need to Run Migration

### Requirements:
1. A WordPress website
2. WordPress admin access
3. Application password

### Get Application Password:
1. Go to WordPress Admin → Users → Your Profile
2. Scroll down to "Application Passwords"
3. Enter a name (like "Migration Tool")
4. Click "Add New Application Password"
5. Copy the generated password (you can only see it once!)

## 4. Run the Migration

### Test First (Dry Run):
```bash
python -m src.cli migrate -i sample-data/content \
  --wp-url https://your-site.com \
  --wp-user admin \
  --wp-password your-app-password \
  --dry-run
```

### Actually Create Posts:
```bash
python -m src.cli migrate -i sample-data/content \
  --wp-url https://your-site.com \
  --wp-user admin \
  --wp-password your-app-password
```

## 5. Expected Results

After successful migration, you'll see:
```
Migration Summary:
  Created: 3
  Updated: 0
  Errors: 0
  Total: 3
✓ Migration completed successfully!
```

The tool will show WordPress post IDs for each created post.

## 6. Troubleshooting

### Can't Access Admin?
- Make sure you have admin credentials
- Check if WordPress URL is correct
- Verify site is accessible

### Posts Not Showing?
- Check post status (draft vs published)
- Look in correct post type section
- Check if custom post types are registered

### Connection Failed?
- Verify REST API is enabled: `https://your-site.com/wp-json/wp/v2/`
- Check application password is correct
- Ensure user has posting permissions