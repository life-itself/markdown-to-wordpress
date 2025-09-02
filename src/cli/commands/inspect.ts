import chalk from 'chalk';
import configLoader from '../../utils/config-loader';
import parser from '../../core/parser';
import { ContentMapper } from '../../core/mapper';
import logger from '../../utils/logger';

interface InspectOptions {
  file: string;
  config: string;
  map?: string;
  verbose?: boolean;
}

export async function inspectCommand(options: InspectOptions) {
  try {
    console.log(chalk.bold('Inspecting file:'), options.file);
    console.log(chalk.gray('─'.repeat(50)));
    
    // Load configuration
    const config = configLoader.loadConfig(options.config);
    const mapping = configLoader.loadMapping(options.map || './mappings.yml');
    
    // Parse the file
    const parsed = parser.parseFile(options.file);
    
    // Display front matter
    console.log('\n' + chalk.bold('Front Matter:'));
    console.log(chalk.gray(JSON.stringify(parsed.frontMatter, null, 2)));
    
    // Display content preview
    console.log('\n' + chalk.bold('Content Preview (first 500 chars):'));
    console.log(chalk.gray(parsed.content.substring(0, 500)));
    if (parsed.content.length > 500) {
      console.log(chalk.gray('... (truncated)'));
    }
    
    // Map to WordPress format
    const mapper = new ContentMapper(config, mapping);
    
    try {
      const wpPost = await mapper.mapToWordPress(parsed);
      
      console.log('\n' + chalk.bold('WordPress Payload:'));
      console.log(chalk.gray(JSON.stringify(wpPost, null, 2)));
      
      // Display mapping info
      const type = parsed.frontMatter.type || 'blog';
      const postType = mapper.getPostType(type);
      
      console.log('\n' + chalk.bold('Mapping Information:'));
      console.log(chalk.gray('─'.repeat(50)));
      console.log(`Content Type: ${type}`);
      console.log(`WordPress Post Type: ${postType}`);
      console.log(`Status: ${wpPost.status}`);
      
      if (wpPost.featured_media) {
        console.log(`Featured Image: Will be uploaded`);
      }
      
      if (wpPost.tags && wpPost.tags.length > 0) {
        console.log(`Tags: ${wpPost.tags.length} tags will be assigned`);
      }
      
      if (wpPost.categories && wpPost.categories.length > 0) {
        console.log(`Categories: ${wpPost.categories.length} categories will be assigned`);
      }
      
      if (wpPost.meta && Object.keys(wpPost.meta).length > 0) {
        console.log(`Meta Fields: ${Object.keys(wpPost.meta).length} meta fields`);
        
        if (options.verbose) {
          console.log('\n' + chalk.bold('Meta Fields:'));
          for (const [key, value] of Object.entries(wpPost.meta)) {
            console.log(`  ${key}: ${JSON.stringify(value)}`);
          }
        }
      }
      
      // Check for issues
      console.log('\n' + chalk.bold('Validation:'));
      const issues: string[] = [];
      
      if (!wpPost.title) {
        issues.push('Missing title');
      }
      
      if (!wpPost.slug) {
        issues.push('Missing slug');
      }
      
      if (!wpPost.content || wpPost.content.trim() === '') {
        issues.push('Empty content');
      }
      
      if (type === 'event' && !parsed.frontMatter.start_date) {
        issues.push('Event missing start_date');
      }
      
      if (type === 'podcast' && !parsed.frontMatter.audio_url) {
        issues.push('Podcast missing audio_url');
      }
      
      if (issues.length > 0) {
        console.log(chalk.red('Issues found:'));
        for (const issue of issues) {
          console.log(chalk.red(`  • ${issue}`));
        }
      } else {
        console.log(chalk.green('✓ No issues found'));
      }
      
    } catch (error) {
      console.log('\n' + chalk.red('Error mapping to WordPress:'));
      console.log(chalk.red((error as Error).message));
    }
    
  } catch (error) {
    logger.error('Inspection error', { error: (error as Error).message });
    process.exit(1);
  }
}