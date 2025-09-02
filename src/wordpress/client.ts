import axios, { AxiosInstance, AxiosError } from 'axios';
import { Config, WordPressPost, WordPressMedia } from '../types';
import logger from '../utils/logger';

export class WordPressClient {
  private client: AxiosInstance;
  private config: Config;
  private authHeader: string;
  
  constructor(config: Config) {
    this.config = config;
    
    // Setup authentication
    if (config.wordpress.auth.method === 'application_passwords') {
      const auth = Buffer.from(
        `${config.wordpress.auth.username}:${config.wordpress.auth.application_password}`
      ).toString('base64');
      this.authHeader = `Basic ${auth}`;
    } else if (config.wordpress.auth.method === 'jwt') {
      this.authHeader = `Bearer ${config.wordpress.auth.jwt_token}`;
    } else {
      throw new Error('Invalid authentication method');
    }
    
    // Create axios instance
    this.client = axios.create({
      baseURL: config.wordpress.base_url,
      headers: {
        'Authorization': this.authHeader,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
    
    // Add retry interceptor
    this.setupRetryInterceptor();
  }
  
  private setupRetryInterceptor() {
    this.client.interceptors.response.use(
      response => response,
      async (error: AxiosError) => {
        const config = error.config;
        
        if (!config || !config.url) {
          return Promise.reject(error);
        }
        
        // Check if we should retry
        const retryCount = (config as any).retryCount || 0;
        const maxRetries = this.config.migration.retry_attempts;
        
        if (retryCount >= maxRetries) {
          return Promise.reject(error);
        }
        
        // Check if error is retryable
        const isRetryable = !error.response || 
          error.response.status === 429 || 
          error.response.status >= 500;
        
        if (!isRetryable) {
          return Promise.reject(error);
        }
        
        // Calculate delay
        const delay = this.config.migration.retry_delay_ms * Math.pow(2, retryCount);
        
        logger.debug(`Retrying request to ${config.url} (attempt ${retryCount + 1}/${maxRetries})`);
        
        // Wait and retry
        await new Promise(resolve => setTimeout(resolve, delay));
        
        (config as any).retryCount = retryCount + 1;
        return this.client.request(config);
      }
    );
  }
  
  async testConnection(): Promise<boolean> {
    try {
      const response = await this.client.get('/wp-json/wp/v2/users/me');
      logger.info('WordPress connection successful', {
        user: response.data.name,
        id: response.data.id
      });
      return true;
    } catch (error) {
      logger.error('WordPress connection failed', {
        error: (error as AxiosError).message,
        response: (error as AxiosError).response?.data
      });
      return false;
    }
  }
  
  async findPostBySlug(slug: string, postType: string = 'posts'): Promise<WordPressPost | null> {
    try {
      const endpoint = this.getEndpoint(postType);
      const response = await this.client.get(endpoint, {
        params: { slug, per_page: 1 }
      });
      
      if (response.data && response.data.length > 0) {
        return response.data[0];
      }
      
      return null;
    } catch (error) {
      logger.debug(`Post not found by slug: ${slug}`);
      return null;
    }
  }
  
  async findPostByMeta(metaKey: string, metaValue: string, postType: string = 'posts'): Promise<WordPressPost | null> {
    try {
      const endpoint = this.getEndpoint(postType);
      const response = await this.client.get(endpoint, {
        params: {
          meta_key: metaKey,
          meta_value: metaValue,
          per_page: 1
        }
      });
      
      if (response.data && response.data.length > 0) {
        return response.data[0];
      }
      
      return null;
    } catch (error) {
      logger.debug(`Post not found by meta: ${metaKey}=${metaValue}`);
      return null;
    }
  }
  
  async createPost(post: WordPressPost, postType: string = 'posts'): Promise<WordPressPost> {
    try {
      const endpoint = this.getEndpoint(postType);
      
      // Add rate limiting
      await this.rateLimit();
      
      const response = await this.client.post(endpoint, post);
      
      logger.debug(`Created post: ${post.slug}`, { id: response.data.id });
      
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      logger.error(`Failed to create post: ${post.slug}`, {
        error: axiosError.message,
        response: axiosError.response?.data
      });
      throw error;
    }
  }
  
  async updatePost(id: number, post: Partial<WordPressPost>, postType: string = 'posts'): Promise<WordPressPost> {
    try {
      const endpoint = `${this.getEndpoint(postType)}/${id}`;
      
      // Add rate limiting
      await this.rateLimit();
      
      const response = await this.client.post(endpoint, post);
      
      logger.debug(`Updated post: ${post.slug}`, { id: response.data.id });
      
      return response.data;
    } catch (error) {
      const axiosError = error as AxiosError;
      logger.error(`Failed to update post: ${post.slug}`, {
        error: axiosError.message,
        response: axiosError.response?.data
      });
      throw error;
    }
  }
  
  async getTaxonomyTermId(taxonomy: string, term: string): Promise<number | null> {
    try {
      const endpoint = `/wp-json/wp/v2/${taxonomy}`;
      const response = await this.client.get(endpoint, {
        params: { search: term, per_page: 100 }
      });
      
      // Look for exact match
      const exactMatch = response.data.find((t: any) => 
        t.name.toLowerCase() === term.toLowerCase()
      );
      
      if (exactMatch) {
        return exactMatch.id;
      }
      
      // Create new term
      return await this.createTaxonomyTerm(taxonomy, term);
    } catch (error) {
      logger.error(`Failed to get taxonomy term: ${taxonomy}/${term}`, {
        error: (error as Error).message
      });
      return null;
    }
  }
  
  async createTaxonomyTerm(taxonomy: string, term: string): Promise<number | null> {
    try {
      const endpoint = `/wp-json/wp/v2/${taxonomy}`;
      
      // Add rate limiting
      await this.rateLimit();
      
      const response = await this.client.post(endpoint, {
        name: term,
        slug: this.generateSlug(term)
      });
      
      logger.debug(`Created taxonomy term: ${taxonomy}/${term}`, { id: response.data.id });
      
      return response.data.id;
    } catch (error) {
      const axiosError = error as AxiosError;
      
      // Check if term already exists (409 conflict)
      if (axiosError.response?.status === 409) {
        // Try to get existing term
        return await this.getTaxonomyTermId(taxonomy, term);
      }
      
      logger.error(`Failed to create taxonomy term: ${taxonomy}/${term}`, {
        error: axiosError.message,
        response: axiosError.response?.data
      });
      return null;
    }
  }
  
  async getUserIdByEmail(email: string): Promise<number | null> {
    try {
      const response = await this.client.get('/wp-json/wp/v2/users', {
        params: { search: email, per_page: 100 }
      });
      
      const user = response.data.find((u: any) => u.email === email);
      
      if (user) {
        return user.id;
      }
      
      return null;
    } catch (error) {
      logger.debug(`User not found by email: ${email}`);
      return null;
    }
  }
  
  async getUserIdByName(name: string): Promise<number | null> {
    try {
      const response = await this.client.get('/wp-json/wp/v2/users', {
        params: { search: name, per_page: 100 }
      });
      
      const user = response.data.find((u: any) => 
        u.name.toLowerCase() === name.toLowerCase()
      );
      
      if (user) {
        return user.id;
      }
      
      return null;
    } catch (error) {
      logger.debug(`User not found by name: ${name}`);
      return null;
    }
  }
  
  private getEndpoint(postType: string): string {
    const endpoints: { [key: string]: string } = {
      posts: this.config.wordpress.endpoints.posts,
      pages: this.config.wordpress.endpoints.pages,
      podcast: this.config.wordpress.endpoints.podcast || '/wp-json/wp/v2/podcast',
      event: this.config.wordpress.endpoints.event || '/wp-json/wp/v2/event'
    };
    
    return endpoints[postType] || `/wp-json/wp/v2/${postType}`;
  }
  
  private generateSlug(text: string): string {
    return text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '');
  }
  
  private async rateLimit(): Promise<void> {
    if (this.config.migration.rate_limit_ms > 0) {
      await new Promise(resolve => setTimeout(resolve, this.config.migration.rate_limit_ms));
    }
  }
}

export default WordPressClient;