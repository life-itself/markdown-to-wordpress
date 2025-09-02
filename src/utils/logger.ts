import winston from 'winston';
import chalk from 'chalk';
import { MigrationResult } from '../types';

const { combine, timestamp, json, printf, colorize } = winston.format;

const consoleFormat = printf(({ level, message, timestamp, ...meta }) => {
  let output = `${timestamp} [${level}]: ${message}`;
  
  if (meta && Object.keys(meta).length) {
    const metaStr = JSON.stringify(meta, null, 2);
    if (metaStr !== '{}') {
      output += `\n${metaStr}`;
    }
  }
  
  return output;
});

class Logger {
  private winston: winston.Logger;
  private results: MigrationResult[] = [];
  
  constructor() {
    this.winston = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: combine(
        timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
        json()
      ),
      transports: [
        new winston.transports.File({ 
          filename: 'migration-error.log', 
          level: 'error' 
        }),
        new winston.transports.File({ 
          filename: 'migration.log' 
        }),
        new winston.transports.Console({
          format: combine(
            colorize(),
            timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
            consoleFormat
          )
        })
      ]
    });
  }
  
  info(message: string, meta?: any) {
    this.winston.info(message, meta);
  }
  
  warn(message: string, meta?: any) {
    this.winston.warn(message, meta);
  }
  
  error(message: string, meta?: any) {
    this.winston.error(message, meta);
  }
  
  debug(message: string, meta?: any) {
    this.winston.debug(message, meta);
  }
  
  success(message: string) {
    console.log(chalk.green('✓'), message);
  }
  
  fail(message: string) {
    console.log(chalk.red('✗'), message);
  }
  
  addResult(result: MigrationResult) {
    this.results.push(result);
    
    const emoji = result.action === 'created' ? '➕' :
                  result.action === 'updated' ? '✏️' :
                  result.action === 'skipped' ? '⏭️' :
                  result.action === 'error' ? '❌' : '❓';
    
    const color = result.action === 'created' ? chalk.green :
                  result.action === 'updated' ? chalk.blue :
                  result.action === 'skipped' ? chalk.yellow :
                  result.action === 'error' ? chalk.red : chalk.gray;
    
    console.log(
      emoji,
      color(`[${result.action.toUpperCase()}]`),
      chalk.white(result.source),
      result.target?.id ? `→ WP ID: ${result.target.id}` : ''
    );
    
    if (result.error) {
      this.error(`Error processing ${result.source}: ${result.error}`);
    }
  }
  
  printSummary() {
    console.log('\n' + chalk.bold('Migration Summary:'));
    console.log(chalk.gray('─'.repeat(50)));
    
    const summary = {
      created: this.results.filter(r => r.action === 'created').length,
      updated: this.results.filter(r => r.action === 'updated').length,
      skipped: this.results.filter(r => r.action === 'skipped').length,
      errors: this.results.filter(r => r.action === 'error').length,
      total: this.results.length
    };
    
    console.log(chalk.green(`  Created: ${summary.created}`));
    console.log(chalk.blue(`  Updated: ${summary.updated}`));
    console.log(chalk.yellow(`  Skipped: ${summary.skipped}`));
    console.log(chalk.red(`  Errors:  ${summary.errors}`));
    console.log(chalk.gray('─'.repeat(50)));
    console.log(chalk.bold(`  Total:   ${summary.total}`));
    
    if (summary.errors > 0) {
      console.log('\n' + chalk.red('⚠️  Some items failed to migrate. Check migration-error.log for details.'));
    }
  }
  
  getResults(): MigrationResult[] {
    return this.results;
  }
}

export default new Logger();