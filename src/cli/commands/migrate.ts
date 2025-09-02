import ora from 'ora';
import chalk from 'chalk';
import { MigrationOptions } from '../../types';
import configLoader from '../../utils/config-loader';
import parser from '../../core/parser';
import { Migrator } from '../../core/migrator';
import logger from '../../utils/logger';

export async function migrateCommand(options: MigrationOptions & { config: string; input: string; map?: string }) {
  const spinner = ora('Initializing migration...').start();
  
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
    let filesToMigrate = parsedFiles;
    if (options.type && options.type !== 'auto') {
      filesToMigrate = parsedFiles.filter(f => f.frontMatter.type === options.type);
      console.log(chalk.blue(`Filtered to ${filesToMigrate.length} files of type: ${options.type}`));
    }
    
    // Create migrator
    const migrator = new Migrator(config, mapping);
    
    // Validate files
    spinner.start('Validating files...');
    const { valid, invalid } = await migrator.validateFiles(filesToMigrate);
    
    if (invalid.length > 0) {
      spinner.warn(`${invalid.length} files have validation errors`);
      
      if (!options.dryRun) {
        const proceed = await confirmProceed(valid.length, invalid.length);
        if (!proceed) {
          spinner.fail('Migration cancelled');
          return;
        }
      }
      
      filesToMigrate = valid;
    } else {
      spinner.succeed('All files validated successfully');
    }
    
    // Dry run notification
    if (options.dryRun) {
      console.log(chalk.yellow('\n🔍 DRY RUN MODE - No changes will be made\n'));
    }
    
    // Start migration
    spinner.start(`Migrating ${filesToMigrate.length} files...`);
    spinner.stop(); // Let the migrator handle logging
    
    console.log(''); // Empty line for better formatting
    
    const results = await migrator.migrate(filesToMigrate, options);
    
    // Final message
    if (options.dryRun) {
      console.log(chalk.yellow('\n✅ Dry run completed. Review the output above.'));
      console.log(chalk.gray('Run without --dry-run to perform actual migration.'));
    } else {
      console.log(chalk.green('\n✅ Migration completed successfully!'));
    }
    
  } catch (error) {
    spinner.fail('Migration failed');
    logger.error('Migration error', { error: (error as Error).message });
    process.exit(1);
  }
}

async function confirmProceed(validCount: number, invalidCount: number): Promise<boolean> {
  console.log(chalk.yellow(`\n⚠️  ${invalidCount} files have validation errors.`));
  console.log(chalk.blue(`   ${validCount} files are valid and can be migrated.`));
  console.log(chalk.gray('   Run with --verbose to see validation details.\n'));
  
  // In a real implementation, you'd use inquirer or similar for interactive prompt
  // For now, we'll proceed with valid files
  console.log(chalk.green('   Proceeding with valid files only...\n'));
  
  return true;
}