# ETL Pipeline for Markdown to WordPress Migration

This directory contains the ETL (Extract, Transform, Load) pipeline for migrating markdown content to WordPress, following the design specified in DESIGN.md.

## Pipeline Structure

Each step is isolated with clear inputs and outputs:

```
etl/
├── 0-image-processing/     # Analyze and create image renaming dictionary
├── 1-prepare-content/      # Clean up front-matter and markdown
├── 2-decide-mappings/      # Map content to WordPress types
├── 3-upload-media/         # Upload images to WordPress media library
├── 4-rewrite-links/        # Update image and internal links
├── 5-create-content/       # Create posts/pages in WordPress
└── 6-verify/              # Verify migration results
```

Each step contains:
- `input/` - Input data for this step
- `output/` - Generated output for next step
- `tests/` - Unit tests for this step
- `README.md` - Step documentation
- `main.py` - Main processing script

## Running the Pipeline

Run each step in order:

```bash
# Step 0: Process images
cd etl/0-image-processing && python main.py

# Step 1: Prepare content
cd ../1-prepare-content && python main.py

# Continue through remaining steps...
```

Or run the full pipeline:

```bash
python run_pipeline.py
```

## Data Flow

1. **Input**: Raw markdown files and assets from lifeitself.org
2. **Step 0**: Creates image renaming dictionary
3. **Step 1**: Cleans and standardizes markdown
4. **Step 2**: Maps content to WordPress structure
5. **Step 3**: Uploads media files
6. **Step 4**: Updates all links to point to new locations
7. **Step 5**: Creates content in WordPress
8. **Step 6**: Verifies migration success