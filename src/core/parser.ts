import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import MarkdownIt from 'markdown-it';
import { glob } from 'glob';
import { MarkdownFile, FrontMatter } from '../types';
import logger from '../utils/logger';

export class MarkdownParser {
  private md: MarkdownIt;
  
  constructor() {
    this.md = new MarkdownIt({
      html: true,
      linkify: true,
      typographer: true,
      breaks: true
    });
  }
  
  async findMarkdownFiles(inputPath: string, pattern: string = '**/*.md'): Promise<string[]> {
    try {
      const fullPath = path.resolve(inputPath);
      const globPattern = path.join(fullPath, pattern);
      
      const files = await glob(globPattern, {
        ignore: ['**/node_modules/**', '**/dist/**', '**/build/**'],
        absolute: true
      });
      
      logger.info(`Found ${files.length} markdown files in ${inputPath}`);
      return files;
    } catch (error) {
      logger.error('Error finding markdown files', { error: (error as Error).message });
      throw error;
    }
  }
  
  parseFile(filePath: string): MarkdownFile {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const parsed = matter(content);
      
      // Extract and validate front matter
      const frontMatter = this.normalizeFrontMatter(parsed.data as FrontMatter, filePath);
      
      // Convert markdown to HTML
      const html = this.convertMarkdownToHtml(parsed.content, frontMatter);
      
      return {
        path: filePath,
        frontMatter,
        content: parsed.content,
        html
      };
    } catch (error) {
      logger.error(`Error parsing file ${filePath}`, { error: (error as Error).message });
      throw error;
    }
  }
  
  private normalizeFrontMatter(data: any, filePath: string): FrontMatter {
    // Generate slug from filename if not provided
    if (!data.slug) {
      const basename = path.basename(filePath, '.md');
      data.slug = this.generateSlug(basename);
    }
    
    // Detect type from path if not specified
    if (!data.type) {
      data.type = this.detectTypeFromPath(filePath);
    }
    
    // Ensure arrays for array fields
    const arrayFields = ['authors', 'tags', 'categories', 'initiatives', 'guests'];
    arrayFields.forEach(field => {
      if (data[field] && !Array.isArray(data[field])) {
        data[field] = [data[field]];
      }
    });
    
    // Normalize dates to ISO format
    if (data.date_published) {
      data.date_published = this.normalizeDate(data.date_published);
    }
    if (data.date_updated) {
      data.date_updated = this.normalizeDate(data.date_updated);
    }
    if (data.start_date) {
      data.start_date = this.normalizeDate(data.start_date);
    }
    if (data.end_date) {
      data.end_date = this.normalizeDate(data.end_date);
    }
    
    // Set external_id if not provided
    if (!data.external_id) {
      data.external_id = data.slug;
    }
    
    return data as FrontMatter;
  }
  
  private convertMarkdownToHtml(markdown: string, frontMatter: FrontMatter): string {
    let html = this.md.render(markdown);
    
    // Handle wiki-style links [[Page Name]] or [[slug|Display Text]]
    html = this.processWikiLinks(html);
    
    // Process image paths
    html = this.processImagePaths(html, frontMatter);
    
    return html;
  }
  
  private processWikiLinks(html: string): string {
    // Pattern for [[Page Name]] or [[slug|Display Text]]
    const wikiLinkPattern = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;
    
    return html.replace(wikiLinkPattern, (match, target, displayText) => {
      const slug = this.generateSlug(target);
      const text = displayText || target;
      
      // For now, create a placeholder link that will be resolved later
      return `<a href="/${slug}" data-wiki-link="${target}">${text}</a>`;
    });
  }
  
  private processImagePaths(html: string, frontMatter: FrontMatter): string {
    // Convert relative image paths to absolute paths
    // This will be updated later when images are uploaded to WordPress
    const imgPattern = /<img[^>]+src="([^"]+)"/g;
    
    return html.replace(imgPattern, (match, src) => {
      if (src.startsWith('http://') || src.startsWith('https://')) {
        return match; // Already absolute
      }
      
      // Mark relative images for later processing
      return match.replace(src, `data-local-image="${src}" src="${src}"`);
    });
  }
  
  private generateSlug(text: string): string {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '') // Remove special characters
      .replace(/\s+/g, '-')      // Replace spaces with hyphens
      .replace(/-+/g, '-')       // Replace multiple hyphens with single
      .replace(/^-+|-+$/g, '');  // Remove leading/trailing hyphens
  }
  
  private detectTypeFromPath(filePath: string): 'blog' | 'podcast' | 'event' | 'page' {
    const normalizedPath = filePath.toLowerCase().replace(/\\/g, '/');
    
    if (normalizedPath.includes('/podcast') || normalizedPath.includes('/episodes')) {
      return 'podcast';
    }
    if (normalizedPath.includes('/event') || normalizedPath.includes('/residenc')) {
      return 'event';
    }
    if (normalizedPath.includes('/page') || normalizedPath.includes('/learn') || 
        normalizedPath.includes('/initiative')) {
      return 'page';
    }
    
    // Default to blog
    return 'blog';
  }
  
  private normalizeDate(date: any): string {
    if (!date) return new Date().toISOString();
    
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) {
        logger.warn(`Invalid date: ${date}, using current date`);
        return new Date().toISOString();
      }
      return d.toISOString();
    } catch (error) {
      logger.warn(`Error parsing date: ${date}`, { error: (error as Error).message });
      return new Date().toISOString();
    }
  }
  
  async parseFiles(files: string[]): Promise<MarkdownFile[]> {
    const results: MarkdownFile[] = [];
    
    for (const file of files) {
      try {
        const parsed = this.parseFile(file);
        results.push(parsed);
      } catch (error) {
        logger.error(`Failed to parse ${file}`, { error: (error as Error).message });
      }
    }
    
    return results;
  }
}

export default new MarkdownParser();