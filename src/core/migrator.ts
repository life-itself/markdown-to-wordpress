import pLimit from 'p-limit';
import { MarkdownFile, Config, Mapping, MigrationResult, MigrationOptions, WordPressPost } from '../types';
import { WordPressClient } from '../wordpress/client';
import { ContentMapper } from './mapper';
import logger from '../utils/logger';
import fs from 'fs';
import path from 'path';

export class Migrator {
  private config: Config;
  private mapping: Mapping;
  private mapper: ContentMapper;
  private wpClient: WordPressClient;
  private ledger: Map<string, number> = new Map();
  private ledgerPath: string;
  
  constructor(config: Config, mapping: Mapping) {
    this.config = config;
    this.mapping = mapping;
    this.mapper = new ContentMapper(config, mapping);
    this.wpClient = new WordPressClient(config);
    this.ledgerPath = path.join(process.cwd(), 'migration-ledger.json');
    
    this.loadLedger();
  }
  
  private loadLedger(): void {
    try {
      if (fs.existsSync(this.ledgerPath)) {
        const data = fs.readFileSync(this.ledgerPath, 'utf8');
        const parsed = JSON.parse(data);
        this.ledger = new Map(Object.entries(parsed));
        logger.debug(`Loaded migration ledger with ${this.ledger.size} entries`);
      }
    } catch (error) {
      logger.warn('Could not load migration ledger', { error: (error as Error).message });
    }
  }
  
  private saveLedger(): void {
    try {
      const data = Object.fromEntries(this.ledger.entries());
      fs.writeFileSync(this.ledgerPath, JSON.stringify(data, null, 2));
      logger.debug('Saved migration ledger');
    } catch (error) {
      logger.error('Could not save migration ledger', { error: (error as Error).message });
    }
  }
  
  async migrate(files: MarkdownFile[], options: MigrationOptions): Promise<MigrationResult[]> {
    logger.info(`Starting migration of ${files.length} files`);
    
    // Test connection first
    const connected = await this.mapper.testConnection();
    if (!connected) {
      throw new Error('Could not connect to WordPress');
    }
    
    // Filter files if needed
    let filesToProcess = files;
    
    if (options.since) {
      const sinceDate = new Date(options.since);
      filesToProcess = files.filter(f => {
        const fileDate = new Date(f.frontMatter.date_published || f.frontMatter.date_updated || 0);
        return fileDate >= sinceDate;
      });
      logger.info(`Filtered to ${filesToProcess.length} files since ${options.since}`);
    }
    
    if (options.limit) {
      filesToProcess = filesToProcess.slice(0, options.limit);
      logger.info(`Limited to ${filesToProcess.length} files`);
    }
    
    // Set up concurrency limiter
    const limit = pLimit(options.concurrency || this.config.migration.concurrency);
    
    // Process files
    const promises = filesToProcess.map(file => 
      limit(() => this.processFile(file, options))
    );
    
    const results = await Promise.all(promises);
    
    // Save ledger after processing
    this.saveLedger();
    
    // Print summary
    logger.printSummary();
    
    return results;
  }
  
  private async processFile(file: MarkdownFile, options: MigrationOptions): Promise<MigrationResult> {
    const startTime = Date.now();
    
    try {
      // Check if already migrated
      const ledgerKey = file.frontMatter.external_id || file.frontMatter.slug || file.path;
      
      if (this.ledger.has(ledgerKey) && !options.dryRun) {
        const existingId = this.ledger.get(ledgerKey)!;
        logger.debug(`File already in ledger: ${file.path} → WP ID: ${existingId}`);
      }
      
      // Map to WordPress format
      const wpPost = await this.mapper.mapToWordPress(file);
      const postType = this.mapper.getPostType(file.frontMatter.type || 'blog');
      
      // Dry run - just log what would happen
      if (options.dryRun) {
        const result: MigrationResult = {
          source: file.path,
          target: {
            type: postType,
            slug: wpPost.slug
          },
          action: 'skipped',
          details: { dryRun: true, payload: wpPost },
          duration_ms: Date.now() - startTime
        };
        
        logger.addResult(result);
        
        if (options.verbose) {
          console.log('DRY RUN - Would create/update:', JSON.stringify(wpPost, null, 2));
        }
        
        return result;
      }
      
      // Check if post exists (idempotent logic)
      let existingPost = null;
      
      // 1. Check by external_id meta
      if (wpPost.meta?._external_id) {
        existingPost = await this.wpClient.findPostByMeta('_external_id', wpPost.meta._external_id, postType);
      }
      
      // 2. Check by slug
      if (!existingPost && wpPost.slug) {
        existingPost = await this.wpClient.findPostBySlug(wpPost.slug, postType);
      }
      
      let action: 'created' | 'updated';
      let wpId: number;
      
      if (existingPost) {
        // Update existing post
        wpId = existingPost.id!;
        await this.wpClient.updatePost(wpId, wpPost, postType);
        action = 'updated';
        logger.debug(`Updated post: ${wpPost.slug} (ID: ${wpId})`);
      } else {
        // Create new post
        const created = await this.wpClient.createPost(wpPost, postType);
        wpId = created.id!;
        action = 'created';
        logger.debug(`Created post: ${wpPost.slug} (ID: ${wpId})`);
      }
      
      // Update ledger
      this.ledger.set(ledgerKey, wpId);
      
      const result: MigrationResult = {
        source: file.path,
        target: {
          type: postType,
          id: wpId,
          slug: wpPost.slug
        },
        action,
        duration_ms: Date.now() - startTime
      };
      
      logger.addResult(result);
      
      return result;
      
    } catch (error) {
      const result: MigrationResult = {
        source: file.path,
        target: {
          type: file.frontMatter.type || 'unknown',
          slug: file.frontMatter.slug || 'unknown'
        },
        action: 'error',
        error: (error as Error).message,
        duration_ms: Date.now() - startTime
      };
      
      logger.addResult(result);
      
      return result;
    }
  }
  
  async validateFiles(files: MarkdownFile[]): Promise<{ valid: MarkdownFile[], invalid: { file: MarkdownFile, errors: string[] }[] }> {
    const valid: MarkdownFile[] = [];
    const invalid: { file: MarkdownFile, errors: string[] }[] = [];
    
    for (const file of files) {
      const errors: string[] = [];
      
      // Check required fields based on type
      const type = file.frontMatter.type || 'blog';
      const typeMapping = this.mapping.post_types[type];
      
      if (!typeMapping) {
        errors.push(`Unknown content type: ${type}`);
      } else {
        for (const field of typeMapping.required_fields) {
          if (!file.frontMatter[field as keyof typeof file.frontMatter]) {
            errors.push(`Missing required field: ${field}`);
          }
        }
      }
      
      // Type-specific validation
      if (type === 'event') {
        if (!file.frontMatter.start_date) {
          errors.push('Events must have a start_date');
        }
      }
      
      if (type === 'podcast') {
        if (!file.frontMatter.audio_url && !file.frontMatter.episode_number) {
          errors.push('Podcasts must have either audio_url or episode_number');
        }
      }
      
      if (errors.length > 0) {
        invalid.push({ file, errors });
      } else {
        valid.push(file);
      }
    }
    
    if (invalid.length > 0) {
      logger.warn(`Found ${invalid.length} invalid files:`);
      for (const { file, errors } of invalid) {
        logger.warn(`  ${file.path}:`);
        for (const error of errors) {
          logger.warn(`    - ${error}`);
        }
      }
    }
    
    return { valid, invalid };
  }
  
  getLedgerStats(): { size: number, entries: Array<{ source: string, wpId: number }> } {
    return {
      size: this.ledger.size,
      entries: Array.from(this.ledger.entries()).map(([source, wpId]) => ({ source, wpId }))
    };
  }
  
  clearLedger(): void {
    this.ledger.clear();
    this.saveLedger();
    logger.info('Cleared migration ledger');
  }
}