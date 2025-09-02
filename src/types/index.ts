export interface Config {
  wordpress: {
    base_url: string;
    auth: {
      method: 'application_passwords' | 'jwt';
      username?: string;
      application_password?: string;
      jwt_token?: string;
    };
    endpoints: {
      posts: string;
      pages: string;
      media: string;
      podcast?: string;
      event?: string;
    };
  };
  defaults: {
    status: 'draft' | 'publish' | 'private';
    timezone: string;
    author_fallback: string;
    media: {
      upload: boolean;
      dedupe_by: 'filename' | 'hash';
      max_size_mb: number;
    };
  };
  migration: {
    concurrency: number;
    retry_attempts: number;
    retry_delay_ms: number;
    rate_limit_ms: number;
  };
}

export interface Mapping {
  post_types: {
    [key: string]: {
      endpoint: string;
      required_fields: string[];
      meta_prefix?: string;
      fields?: { [key: string]: string };
      taxonomies?: { [key: string]: string };
      meta?: { [key: string]: string };
    };
  };
  taxonomies: {
    [key: string]: string;
  };
  relationships?: {
    initiatives?: {
      mode: 'taxonomy' | 'relation';
      page_post_type?: string;
    };
  };
}

export interface FrontMatter {
  type?: 'blog' | 'news' | 'event' | 'podcast' | 'page';
  title: string;
  slug?: string;
  subtitle?: string;
  description?: string;
  date_published?: string;
  date_updated?: string;
  featured_image?: string;
  authors?: string[];
  status?: 'draft' | 'publish' | 'private';
  featured?: boolean;
  tags?: string[];
  categories?: string[];
  initiatives?: string[];
  external_id?: string;
  
  // Event specific
  start_date?: string;
  end_date?: string;
  host?: string | string[];
  location_name?: string;
  location_address?: string;
  location_lat?: number;
  location_lng?: number;
  registration_url?: string;
  
  // Podcast specific
  episode_number?: number;
  audio_url?: string;
  duration?: string;
  guests?: string[];
  show?: string;
  
  // Page specific
  template?: string;
  parent_slug?: string;
}

export interface MarkdownFile {
  path: string;
  frontMatter: FrontMatter;
  content: string;
  html?: string;
}

export interface WordPressPost {
  id?: number;
  title: string;
  content: string;
  excerpt?: string;
  slug: string;
  status: 'draft' | 'publish' | 'private';
  date?: string;
  date_gmt?: string;
  modified?: string;
  modified_gmt?: string;
  author?: number;
  featured_media?: number;
  categories?: number[];
  tags?: number[];
  meta?: { [key: string]: any };
  acf?: { [key: string]: any };
}

export interface WordPressMedia {
  id: number;
  source_url: string;
  title: {
    rendered: string;
  };
  media_details: {
    width: number;
    height: number;
    file: string;
  };
}

export interface MigrationResult {
  source: string;
  target: {
    type: string;
    id?: number;
    slug: string;
  };
  action: 'created' | 'updated' | 'skipped' | 'error';
  details?: any;
  error?: string;
  duration_ms?: number;
}

export interface MigrationOptions {
  type?: 'blog' | 'podcast' | 'event' | 'page' | 'auto';
  dryRun?: boolean;
  concurrency?: number;
  limit?: number;
  since?: string;
  mediaMode?: 'upload' | 'skip';
  filter?: string;
  verbose?: boolean;
}