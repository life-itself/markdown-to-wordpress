#!/usr/bin/env node

import { Command } from 'commander';
import chalk from 'chalk';
import { migrateCommand } from './commands/migrate';
import { validateCommand } from './commands/validate';
import { inspectCommand } from './commands/inspect';

const program = new Command();

// ASCII Art Banner
const banner = `
╔══════════════════════════════════════════════════════╗
║     Markdown to WordPress Migration Tool v1.0.0      ║
╚══════════════════════════════════════════════════════╝
`;

console.log(chalk.cyan(banner));

program
  .name('markdown-to-wordpress')
  .description('Migrate markdown content to WordPress via REST API')
  .version('1.0.0');

// Migrate command
program
  .command('migrate')
  .description('Migrate markdown files to WordPress')
  .requiredOption('-c, --config <path>', 'Path to config file', './config.yml')
  .requiredOption('-i, --input <path>', 'Path to markdown files')
  .option('-t, --type <type>', 'Content type (blog|podcast|event|page|auto)', 'auto')
  .option('-m, --map <path>', 'Path to mapping file', './mappings.yml')
  .option('--dry-run', 'Simulate migration without making changes')
  .option('--concurrency <number>', 'Number of concurrent operations', '4')
  .option('--limit <number>', 'Limit number of files to process')
  .option('--since <date>', 'Only process files since date (YYYY-MM-DD)')
  .option('--media-mode <mode>', 'Media handling mode (upload|skip)', 'upload')
  .option('-v, --verbose', 'Show detailed output')
  .action(async (options) => {
    await migrateCommand({
      ...options,
      concurrency: parseInt(options.concurrency),
      limit: options.limit ? parseInt(options.limit) : undefined
    });
  });

// Validate command
program
  .command('validate')
  .description('Validate markdown files against schemas')
  .requiredOption('-c, --config <path>', 'Path to config file', './config.yml')
  .requiredOption('-i, --input <path>', 'Path to markdown files')
  .option('-t, --type <type>', 'Content type to validate')
  .option('-m, --map <path>', 'Path to mapping file', './mappings.yml')
  .option('-v, --verbose', 'Show detailed validation errors')
  .action(validateCommand);

// Inspect command
program
  .command('inspect')
  .description('Inspect a single markdown file and show mapping')
  .requiredOption('-f, --file <path>', 'Path to markdown file')
  .requiredOption('-c, --config <path>', 'Path to config file', './config.yml')
  .option('-m, --map <path>', 'Path to mapping file', './mappings.yml')
  .option('-v, --verbose', 'Show detailed output')
  .action(inspectCommand);

// Help text
program.on('--help', () => {
  console.log('');
  console.log('Examples:');
  console.log('');
  console.log('  $ markdown-to-wordpress migrate -c config.yml -i ./content');
  console.log('  $ markdown-to-wordpress migrate -c config.yml -i ./content --dry-run');
  console.log('  $ markdown-to-wordpress migrate -c config.yml -i ./content -t blog --limit 10');
  console.log('  $ markdown-to-wordpress validate -c config.yml -i ./content');
  console.log('  $ markdown-to-wordpress inspect -f ./content/post.md -c config.yml');
  console.log('');
  console.log('Environment Variables:');
  console.log('');
  console.log('  WP_APP_PASSWORD     WordPress application password');
  console.log('  LOG_LEVEL           Logging level (debug|info|warn|error)');
  console.log('');
});

// Parse arguments
program.parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}