import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';
import dotenv from 'dotenv';
import { Config, Mapping } from '../types';
import logger from './logger';

dotenv.config();

export class ConfigLoader {
  private config: Config | null = null;
  private mapping: Mapping | null = null;
  
  loadConfig(configPath: string): Config {
    try {
      const fullPath = path.resolve(configPath);
      
      if (!fs.existsSync(fullPath)) {
        throw new Error(`Config file not found: ${fullPath}`);
      }
      
      const fileContent = fs.readFileSync(fullPath, 'utf8');
      const rawConfig = yaml.load(fileContent) as any;
      
      // Replace environment variables
      const configStr = JSON.stringify(rawConfig);
      const processedStr = configStr.replace(/\$\{([^}]+)\}/g, (match, envVar) => {
        const value = process.env[envVar];
        if (!value) {
          logger.warn(`Environment variable ${envVar} not found`);
          return '';
        }
        return value;
      });
      
      this.config = JSON.parse(processedStr) as Config;
      
      // Set defaults
      this.setDefaults();
      
      logger.info('Configuration loaded successfully', {
        wordpress_url: this.config.wordpress.base_url,
        auth_method: this.config.wordpress.auth.method
      });
      
      return this.config;
    } catch (error) {
      logger.error('Failed to load configuration', { error: (error as Error).message });
      throw error;
    }
  }
  
  loadMapping(mappingPath: string): Mapping {
    try {
      const fullPath = path.resolve(mappingPath);
      
      if (!fs.existsSync(fullPath)) {
        logger.warn(`Mapping file not found: ${fullPath}, using defaults`);
        return this.getDefaultMapping();
      }
      
      const fileContent = fs.readFileSync(fullPath, 'utf8');
      this.mapping = yaml.load(fileContent) as Mapping;
      
      logger.info('Mapping loaded successfully');
      
      return this.mapping;
    } catch (error) {
      logger.error('Failed to load mapping', { error: (error as Error).message });
      return this.getDefaultMapping();
    }
  }
  
  private setDefaults() {
    if (!this.config) return;
    
    // Set default values if not provided
    this.config.defaults = {
      status: this.config.defaults?.status || 'draft',
      timezone: this.config.defaults?.timezone || 'UTC',
      author_fallback: this.config.defaults?.author_fallback || 'admin',
      media: {
        upload: this.config.defaults?.media?.upload !== false,
        dedupe_by: this.config.defaults?.media?.dedupe_by || 'filename',
        max_size_mb: this.config.defaults?.media?.max_size_mb || 10
      }
    };
    
    this.config.migration = {
      concurrency: this.config.migration?.concurrency || 4,
      retry_attempts: this.config.migration?.retry_attempts || 3,
      retry_delay_ms: this.config.migration?.retry_delay_ms || 1000,
      rate_limit_ms: this.config.migration?.rate_limit_ms || 100
    };
  }
  
  private getDefaultMapping(): Mapping {
    return {
      post_types: {
        blog: {
          endpoint: '/wp-json/wp/v2/posts',
          required_fields: ['title', 'slug'],
          fields: {
            title: 'title',
            excerpt: 'subtitle',
            date: 'date_published',
            modified: 'date_updated',
            slug: 'slug',
            content: 'BODY',
            featured_media: 'featured_image'
          },
          taxonomies: {
            post_tag: 'tags',
            category: 'categories',
            initiative: 'initiatives'
          },
          meta: {
            featured: 'featured',
            _external_id: 'external_id'
          }
        },
        podcast: {
          endpoint: '/wp-json/wp/v2/podcast',
          required_fields: ['title', 'episode_number'],
          fields: {
            title: 'title',
            date: 'date_published',
            slug: 'slug',
            content: 'BODY',
            featured_media: 'featured_image'
          },
          taxonomies: {
            post_tag: 'tags',
            initiative: 'initiatives'
          },
          meta: {
            episode_number: 'episode_number',
            audio_url: 'audio_url',
            duration: 'duration',
            guests: 'guests',
            show: 'show',
            _external_id: 'external_id'
          }
        },
        event: {
          endpoint: '/wp-json/wp/v2/event',
          required_fields: ['title', 'start_date'],
          fields: {
            title: 'title',
            slug: 'slug',
            content: 'BODY',
            featured_media: 'featured_image'
          },
          taxonomies: {
            post_tag: 'tags',
            initiative: 'initiatives'
          },
          meta: {
            start_date: 'start_date',
            end_date: 'end_date',
            host: 'host',
            location_name: 'location_name',
            location_address: 'location_address',
            location_lat: 'location_lat',
            location_lng: 'location_lng',
            registration_url: 'registration_url',
            _external_id: 'external_id'
          }
        },
        page: {
          endpoint: '/wp-json/wp/v2/pages',
          required_fields: ['title', 'slug'],
          fields: {
            title: 'title',
            slug: 'slug',
            content: 'BODY',
            featured_media: 'featured_image'
          },
          meta: {
            description: 'description',
            template: 'template',
            _external_id: 'external_id'
          }
        }
      },
      taxonomies: {
        tag: 'post_tag',
        category: 'category',
        initiatives: 'initiatives'
      },
      relationships: {
        initiatives: {
          mode: 'taxonomy'
        }
      }
    };
  }
  
  getConfig(): Config | null {
    return this.config;
  }
  
  getMapping(): Mapping | null {
    return this.mapping;
  }
}

export default new ConfigLoader();