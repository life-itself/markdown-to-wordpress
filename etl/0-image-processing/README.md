# Step 0: Image Processing

## Purpose

Analyze all image assets in the source content and create a dictionary of renaming recommendations. Images are renamed to be SEO-friendly and contextual based on the posts that use them.

## Inputs

- `input/content/` - Source markdown files and assets
- `input/assets/` - Image files to process

## Outputs

- `output/image_rename_dict.json` - Dictionary mapping original → new filenames
- `output/image_usage_report.json` - Analysis of image usage across files
- `output/orphaned_images.json` - List of unused image files

## Process

1. **Scan all markdown files** to find image references
2. **Analyze image usage**:
   - Which images are used in which files
   - How many times each image is used
   - Featured images vs inline images
3. **Generate SEO-friendly names**:
   - For single-use images: `{post-slug}-{sequence}.ext`
   - For featured images: `{post-slug}-feature.ext`
   - For multi-use images: Keep original or use generic name
4. **Create renaming dictionary** for use in later steps

## Usage

```bash
python main.py --input-dir ../sample --output-dir ./output
```

## Testing

```bash
python -m pytest tests/ -v
```