import fs from 'fs';
import path from 'path';
import FormData from 'form-data';
import mime from 'mime-types';
import crypto from 'crypto';
import axios, { AxiosInstance } from 'axios';
import { Config, WordPressMedia } from '../types';
import logger from '../utils/logger';

export class MediaHandler {
  private client: AxiosInstance;
  private config: Config;
  private authHeader: string;
  private uploadedMedia: Map<string, WordPressMedia> = new Map();
  
  constructor(config: Config) {
    this.config = config;
    
    // Setup authentication
    if (config.wordpress.auth.method === 'application_passwords') {
      const auth = Buffer.from(
        `${config.wordpress.auth.username}:${config.wordpress.auth.application_password}`
      ).toString('base64');
      this.authHeader = `Basic ${auth}`;
    } else {
      this.authHeader = `Bearer ${config.wordpress.auth.jwt_token}`;
    }
    
    // Create axios instance for media uploads
    this.client = axios.create({
      baseURL: config.wordpress.base_url,
      headers: {
        'Authorization': this.authHeader
      },
      timeout: 60000, // Longer timeout for media uploads
      maxContentLength: 50 * 1024 * 1024, // 50MB
      maxBodyLength: 50 * 1024 * 1024
    });
  }
  
  async uploadImage(imagePath: string, altText?: string): Promise<WordPressMedia | null> {
    try {
      // Check if already uploaded
      const cacheKey = this.getCacheKey(imagePath);
      if (this.uploadedMedia.has(cacheKey)) {
        logger.debug(`Image already uploaded: ${imagePath}`);
        return this.uploadedMedia.get(cacheKey)!;
      }
      
      // Resolve image path
      const fullPath = this.resolveImagePath(imagePath);
      if (!fullPath || !fs.existsSync(fullPath)) {
        logger.warn(`Image file not found: ${imagePath}`);
        return null;
      }
      
      // Check file size
      const stats = fs.statSync(fullPath);
      const maxSize = this.config.defaults.media.max_size_mb * 1024 * 1024;
      if (stats.size > maxSize) {
        logger.warn(`Image too large: ${imagePath} (${stats.size} bytes)`);
        return null;
      }
      
      // Check if media already exists in WordPress
      if (this.config.defaults.media.dedupe_by === 'filename') {
        const existing = await this.findMediaByFilename(path.basename(fullPath));
        if (existing) {
          logger.debug(`Media already exists in WordPress: ${path.basename(fullPath)}`);
          this.uploadedMedia.set(cacheKey, existing);
          return existing;
        }
      }
      
      // Prepare form data
      const form = new FormData();
      const stream = fs.createReadStream(fullPath);
      const filename = this.generateFilename(fullPath);
      const mimeType = mime.lookup(fullPath) || 'application/octet-stream';
      
      form.append('file', stream, {
        filename,
        contentType: mimeType
      });
      
      if (altText) {
        form.append('alt_text', altText);
      }
      
      // Upload to WordPress
      logger.debug(`Uploading image: ${imagePath}`);
      
      const response = await this.client.post(
        this.config.wordpress.endpoints.media,
        form,
        {
          headers: {
            ...form.getHeaders()
          }
        }
      );
      
      const media: WordPressMedia = response.data;
      
      logger.success(`Uploaded image: ${filename} → ID: ${media.id}`);
      
      // Cache the result
      this.uploadedMedia.set(cacheKey, media);
      
      return media;
    } catch (error) {
      logger.error(`Failed to upload image: ${imagePath}`, {
        error: (error as Error).message
      });
      return null;
    }
  }
  
  async findMediaByFilename(filename: string): Promise<WordPressMedia | null> {
    try {
      const response = await this.client.get(this.config.wordpress.endpoints.media, {
        params: {
          search: filename,
          per_page: 100
        }
      });
      
      // Look for exact filename match
      const media = response.data.find((m: WordPressMedia) => {
        const wpFilename = m.media_details.file.split('/').pop();
        return wpFilename === filename;
      });
      
      return media || null;
    } catch (error) {
      logger.debug(`Media not found: ${filename}`);
      return null;
    }
  }
  
  async processContentImages(html: string, basePath?: string): Promise<string> {
    // Find all local images in content
    const imgPattern = /data-local-image="([^"]+)"/g;
    const matches = Array.from(html.matchAll(imgPattern));
    
    let processedHtml = html;
    
    for (const match of matches) {
      const localPath = match[1];
      const fullPath = basePath ? path.join(basePath, localPath) : localPath;
      
      // Upload image
      const media = await this.uploadImage(fullPath);
      
      if (media) {
        // Replace local path with WordPress URL
        processedHtml = processedHtml.replace(
          `data-local-image="${localPath}" src="${localPath}"`,
          `src="${media.source_url}"`
        );
      }
    }
    
    // Also process standard img tags with relative paths
    const standardImgPattern = /<img[^>]+src="(?!http)([^"]+)"/g;
    const standardMatches = Array.from(processedHtml.matchAll(standardImgPattern));
    
    for (const match of standardMatches) {
      const localPath = match[1];
      const fullPath = basePath ? path.join(basePath, localPath) : localPath;
      
      // Upload image
      const media = await this.uploadImage(fullPath);
      
      if (media) {
        processedHtml = processedHtml.replace(
          match[0],
          match[0].replace(localPath, media.source_url)
        );
      }
    }
    
    return processedHtml;
  }
  
  async uploadFeaturedImage(imagePath: string, postTitle?: string): Promise<number | null> {
    const altText = postTitle ? `Featured image for ${postTitle}` : undefined;
    const media = await this.uploadImage(imagePath, altText);
    
    return media ? media.id : null;
  }
  
  private resolveImagePath(imagePath: string): string | null {
    // Handle different path formats
    if (path.isAbsolute(imagePath)) {
      return imagePath;
    }
    
    // Try common image directories
    const possiblePaths = [
      imagePath,
      path.join(process.cwd(), imagePath),
      path.join(process.cwd(), 'assets', imagePath),
      path.join(process.cwd(), 'assets', 'images', imagePath),
      path.join(process.cwd(), 'content', imagePath),
      path.join(process.cwd(), 'static', imagePath)
    ];
    
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) {
        return p;
      }
    }
    
    return null;
  }
  
  private generateFilename(filePath: string): string {
    const ext = path.extname(filePath);
    const basename = path.basename(filePath, ext);
    
    // Clean up filename
    const cleaned = basename
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 100); // Limit length
    
    // Add timestamp for uniqueness if needed
    const timestamp = Date.now();
    
    return `${cleaned}-${timestamp}${ext}`;
  }
  
  private getCacheKey(imagePath: string): string {
    if (this.config.defaults.media.dedupe_by === 'hash') {
      // Generate hash of file content
      try {
        const content = fs.readFileSync(imagePath);
        return crypto.createHash('sha256').update(content).digest('hex');
      } catch {
        return imagePath;
      }
    }
    
    // Use filename as cache key
    return path.basename(imagePath);
  }
  
  clearCache(): void {
    this.uploadedMedia.clear();
  }
  
  getCacheStats(): { size: number; items: string[] } {
    return {
      size: this.uploadedMedia.size,
      items: Array.from(this.uploadedMedia.keys())
    };
  }
}

export default MediaHandler;