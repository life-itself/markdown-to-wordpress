# How to Actually Create WordPress Posts

## **What You Need:**

### 1. **WordPress Site**
You need a WordPress website with:
- REST API enabled (default in WP 5.0+)
- Application Passwords enabled
- A user account with post creation permissions

### 2. **WordPress Application Password**
Go to your WordPress Admin → Users → Your Profile → Application Passwords
- Create a new application password
- Save the generated password (you can only see it once!)

## **How to Run the Migration:**

### **Step 1: Test Connection (Dry Run)**
```bash
cd python-migration

python -m src.cli migrate \
  -i sample/content \
  --wp-url https://your-wordpress-site.com \
  --wp-user your-username \
  --wp-password your-application-password \
  --dry-run
```

This will show you what **would** be created without actually creating anything.

### **Step 2: Actually Create Posts**
```bash
python -m src.cli migrate \
  -i sample/content \
  --wp-url https://your-wordpress-site.com \
  --wp-user your-username \
  --wp-password your-application-password
```

**Remove `--dry-run` to actually create the posts!**

## **What Will Be Created:**

Based on our 3 sample files:

1. **about.md** → WordPress **Page**
   - Title: "About Life Itself"
   - Type: Page
   - Status: Published

2. **community.md** → WordPress **Blog Post**
   - Title: "Our Community"
   - Type: Post
   - Tags: community, connection, wisdom
   - Authors: Rufus Pollock, Sylvie Barbier
   - Status: Published

3. **conscious-coliving-retreat.md** → WordPress **Event** (Custom Post Type)
   - Title: "Conscious Coliving Retreat - Spring 2024"
   - Type: Event
   - Start Date: 2024-04-15
   - Location: Life Itself Hub, Bergerac
   - Status: Published

## **Where to Find Your Posts:**

After successful migration, you can find the posts at:

- **WordPress Admin**: `https://your-site.com/wp-admin/`
  - Posts → All Posts (for blog posts)
  - Pages → All Pages (for pages)
  - Events → All Events (if you have events custom post type)

- **Front-end URLs**:
  - `https://your-site.com/about/` (about page)
  - `https://your-site.com/community/` (community post)
  - `https://your-site.com/events/conscious-coliving-retreat-spring-2024/` (event)

## **Expected Output:**

```
Markdown to WordPress Migration Tool v1.0.0
Python implementation for testing and validation

Testing WordPress connection...
✓ Connected to WordPress

Finding markdown files in: sample/content
Found 3 markdown files

Processing: about.md
  ✓ Created: About Life Itself (ID: 123)

Processing: community.md
  ✓ Created: Our Community (ID: 124)

Processing: conscious-coliving-retreat.md
  ✓ Created: Conscious Coliving Retreat - Spring 2024 (ID: 125)

Migration Summary:
  Created: 3
  Updated: 0
  Errors: 0
  Total: 3
✓ Migration completed successfully!
```

## **Troubleshooting:**

### **Connection Issues:**
- Verify REST API is accessible: `https://your-site.com/wp-json/wp/v2/users/me`
- Check application password is correct
- Ensure user has proper permissions

### **Custom Post Types:**
If "Events" or "Podcasts" don't exist in your WordPress:
- Events and podcasts will be created as regular **Posts** instead
- Or install a plugin that adds these custom post types

### **Missing Images:**
- Images are referenced but not uploaded yet (media handler not implemented)
- Featured images will show as broken links initially

## **Next Steps for Full Production:**

1. **Media Upload** - Implement actual image uploading
2. **Bulk Processing** - Handle 1000+ files efficiently
3. **Error Recovery** - Better error handling and retry logic
4. **Custom Fields** - Map to ACF or custom meta fields

But for testing with 3 files, this works perfectly! 🎉
