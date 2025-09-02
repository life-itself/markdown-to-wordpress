import ora from 'ora';
import chalk from 'chalk';
import configLoader from '../../utils/config-loader';
import parser from '../../core/parser';
import { Migrator } from '../../core/migrator';
import logger from '../../utils/logger';

interface ValidateOptions {
  config: string;
  input: string;
  type?: string;
  map?: string;
  verbose?: boolean;
}

export async function validateCommand(options: ValidateOptions) {
  const spinner = ora('Initializing validation...').start();
  
  try {
    // Load configuration
    spinner.text = 'Loading configuration...';
    const config = configLoader.loadConfig(options.config);
    const mapping = configLoader.loadMapping(options.map || './mappings.yml');
    
    // Find markdown files
    spinner.text = 'Finding markdown files...';
    const files = await parser.findMarkdownFiles(options.input);
    
    if (files.length === 0) {
      spinner.fail('No markdown files found');
      return;
    }
    
    spinner.succeed(`Found ${files.length} markdown files`);
    
    // Parse files
    spinner.start('Parsing markdown files...');
    const parsedFiles = await parser.parseFiles(files);
    spinner.succeed(`Parsed ${parsedFiles.length} files`);
    
    // Filter by type if specified
    let filesToValidate = parsedFiles;
    if (options.type) {
      filesToValidate = parsedFiles.filter(f => f.frontMatter.type === options.type);
      console.log(chalk.blue(`Filtered to ${filesToValidate.length} files of type: ${options.type}`));
    }
    
    // Create migrator for validation
    const migrator = new Migrator(config, mapping);
    
    // Validate files
    spinner.start('Validating files...');
    const { valid, invalid } = await migrator.validateFiles(filesToValidate);
    spinner.stop();
    
    // Display results
    console.log('\n' + chalk.bold('Validation Results:'));
    console.log(chalk.gray('─'.repeat(50)));
    
    console.log(chalk.green(`✓ Valid files: ${valid.length}`));
    console.log(chalk.red(`✗ Invalid files: ${invalid.length}`));
    
    if (invalid.length > 0 && options.verbose) {
      console.log('\n' + chalk.bold.red('Invalid Files:'));
      
      for (const { file, errors } of invalid) {
        console.log('\n' + chalk.yellow(file.path));
        for (const error of errors) {
          console.log(chalk.red(`  • ${error}`));
        }
      }
    }
    
    // Display content type breakdown
    const typeBreakdown: { [key: string]: number } = {};
    for (const file of parsedFiles) {
      const type = file.frontMatter.type || 'blog';
      typeBreakdown[type] = (typeBreakdown[type] || 0) + 1;
    }
    
    console.log('\n' + chalk.bold('Content Type Breakdown:'));
    console.log(chalk.gray('─'.repeat(50)));
    
    for (const [type, count] of Object.entries(typeBreakdown)) {
      console.log(`  ${type}: ${count}`);
    }
    
    // Exit with error code if validation failed
    if (invalid.length > 0) {
      console.log('\n' + chalk.red('⚠️  Validation failed. Fix errors before migrating.'));
      process.exit(1);
    } else {
      console.log('\n' + chalk.green('✅ All files validated successfully!'));
    }
    
  } catch (error) {
    spinner.fail('Validation failed');
    logger.error('Validation error', { error: (error as Error).message });
    process.exit(1);
  }
}