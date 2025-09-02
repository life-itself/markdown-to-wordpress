import { MarkdownFile, WordPressPost, Config, Mapping, FrontMatter } from '../types';
import { WordPressClient } from '../wordpress/client';
import { MediaHandler } from '../wordpress/media';
import logger from '../utils/logger';
import path from 'path';

export class ContentMapper {
  private wpClient: WordPressClient;
  private mediaHandler: MediaHandler;
  private config: Config;
  private mapping: Mapping;
  
  constructor(config: Config, mapping: Mapping) {
    this.config = config;
    this.mapping = mapping;
    this.wpClient = new WordPressClient(config);
    this.mediaHandler = new MediaHandler(config);
  }
  
  async mapToWordPress(file: MarkdownFile): Promise<WordPressPost> {
    const type = file.frontMatter.type || 'blog';
    const typeMapping = this.mapping.post_types[type];
    
    if (!typeMapping) {
      throw new Error(`No mapping found for type: ${type}`);
    }
    
    // Validate required fields
    this.validateRequiredFields(file.frontMatter, typeMapping.required_fields);
    
    // Create base post object
    const post: WordPressPost = {
      title: file.frontMatter.title,
      slug: file.frontMatter.slug!,
      status: file.frontMatter.status || this.config.defaults.status,
      content: '',
      meta: {}
    };
    
    // Map fields
    if (typeMapping.fields) {
      for (const [wpField, sourceField] of Object.entries(typeMapping.fields)) {
        if (sourceField === 'BODY') {
          // Process content with media handler
          const basePath = path.dirname(file.path);
          post.content = await this.mediaHandler.processContentImages(file.html!, basePath);
        } else if (file.frontMatter[sourceField as keyof FrontMatter] !== undefined) {
          const value = file.frontMatter[sourceField as keyof FrontMatter];
          this.setNestedProperty(post, wpField, value);
        }
      }
    }
    
    // Map excerpt
    if (file.frontMatter.subtitle || file.frontMatter.description) {
      post.excerpt = file.frontMatter.subtitle || file.frontMatter.description;
    }
    
    // Map dates
    if (file.frontMatter.date_published) {
      post.date = file.frontMatter.date_published;
      post.date_gmt = this.toGMT(file.frontMatter.date_published);
    }
    
    if (file.frontMatter.date_updated) {
      post.modified = file.frontMatter.date_updated;
      post.modified_gmt = this.toGMT(file.frontMatter.date_updated);
    }
    
    // Handle featured image
    if (file.frontMatter.featured_image && this.config.defaults.media.upload) {
      const mediaId = await this.mediaHandler.uploadFeaturedImage(
        file.frontMatter.featured_image,
        file.frontMatter.title
      );
      if (mediaId) {
        post.featured_media = mediaId;
      }
    }
    
    // Handle author
    const authorId = await this.resolveAuthor(file.frontMatter.authors);
    if (authorId) {
      post.author = authorId;
    }
    
    // Handle taxonomies
    if (typeMapping.taxonomies) {
      await this.mapTaxonomies(post, file.frontMatter, typeMapping.taxonomies);
    }
    
    // Map meta fields
    if (typeMapping.meta) {
      for (const [metaKey, sourceField] of Object.entries(typeMapping.meta)) {
        const value = file.frontMatter[sourceField as keyof FrontMatter];
        if (value !== undefined) {
          post.meta![metaKey] = value;
        }
      }
    }
    
    // Always set external_id for idempotency
    post.meta!._external_id = file.frontMatter.external_id || file.frontMatter.slug;
    
    return post;
  }
  
  private validateRequiredFields(frontMatter: FrontMatter, requiredFields: string[]): void {
    const missing: string[] = [];
    
    for (const field of requiredFields) {
      if (!frontMatter[field as keyof FrontMatter]) {
        missing.push(field);
      }
    }
    
    if (missing.length > 0) {
      throw new Error(`Missing required fields: ${missing.join(', ')}`);
    }
  }
  
  private setNestedProperty(obj: any, path: string, value: any): void {
    const parts = path.split('.');
    let current = obj;
    
    for (let i = 0; i < parts.length - 1; i++) {
      if (!current[parts[i]]) {
        current[parts[i]] = {};
      }
      current = current[parts[i]];
    }
    
    current[parts[parts.length - 1]] = value;
  }
  
  private toGMT(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toISOString();
  }
  
  private async resolveAuthor(authors?: string[]): Promise<number | null> {
    if (!authors || authors.length === 0) {
      return null;
    }
    
    const firstAuthor = authors[0];
    
    // Check if it's an email
    if (firstAuthor.includes('@')) {
      const userId = await this.wpClient.getUserIdByEmail(firstAuthor);
      if (userId) return userId;
    }
    
    // Try by display name
    const userId = await this.wpClient.getUserIdByName(firstAuthor);
    if (userId) return userId;
    
    // Use fallback author
    const fallbackId = await this.wpClient.getUserIdByName(this.config.defaults.author_fallback);
    
    if (fallbackId) {
      logger.debug(`Using fallback author for: ${firstAuthor}`);
      return fallbackId;
    }
    
    logger.warn(`Could not resolve author: ${firstAuthor}`);
    return null;
  }
  
  private async mapTaxonomies(
    post: WordPressPost,
    frontMatter: FrontMatter,
    taxonomyMapping: { [key: string]: string }
  ): Promise<void> {
    for (const [wpTaxonomy, sourceField] of Object.entries(taxonomyMapping)) {
      const terms = frontMatter[sourceField as keyof FrontMatter] as string[] | undefined;
      
      if (!terms || !Array.isArray(terms) || terms.length === 0) {
        continue;
      }
      
      const termIds: number[] = [];
      
      for (const term of terms) {
        const termId = await this.wpClient.getTaxonomyTermId(wpTaxonomy, term);
        if (termId) {
          termIds.push(termId);
        }
      }
      
      if (termIds.length > 0) {
        // Map to correct post field based on taxonomy type
        if (wpTaxonomy === 'post_tag' || wpTaxonomy === 'tags') {
          post.tags = termIds;
        } else if (wpTaxonomy === 'category' || wpTaxonomy === 'categories') {
          post.categories = termIds;
        } else {
          // Custom taxonomy - store in meta or use REST API field name
          if (!post.meta) post.meta = {};
          post.meta[wpTaxonomy] = termIds;
        }
      }
    }
  }
  
  getPostType(contentType: string): string {
    const typeMapping = this.mapping.post_types[contentType];
    
    if (!typeMapping || !typeMapping.endpoint) {
      return 'posts'; // Default to posts
    }
    
    // Extract post type from endpoint
    const match = typeMapping.endpoint.match(/\/wp-json\/wp\/v2\/(\w+)/);
    
    if (match) {
      return match[1];
    }
    
    return 'posts';
  }
  
  async testConnection(): Promise<boolean> {
    return await this.wpClient.testConnection();
  }
}