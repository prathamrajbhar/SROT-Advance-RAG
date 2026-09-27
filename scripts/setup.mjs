#!/usr/bin/env node

import { execSync, spawn } from 'node:child_process';
import { existsSync, copyFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import chalk from 'chalk';
import ora from 'ora';
import { confirm } from '@inquirer/prompts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');

const runCmd = (cmd, cwd = ROOT_DIR) => {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, { shell: true, cwd, stdio: 'pipe' });
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(stdout.trim());
      } else {
        reject(new Error(stderr.trim() || stdout.trim() || `Command failed with code ${code}`));
      }
    });
  });
};

const printBanner = () => {
  console.clear();
  console.log(chalk.bold.cyan(`
  ┌────────────────────────────────────────────────────────┐
  │                                                        │
  │   🚀  SROT MONOREPO ENVIRONMENT SETUP ASSISTANT        │
  │   Next.js + FastAPI Production Suite                       │
  │                                                        │
  └────────────────────────────────────────────────────────┘
  `));
};

const printSummary = () => {
  console.log('\n' + chalk.bold.green('✔ Setup complete successfully!\n'));
  console.log(chalk.cyan('┌────────────────────────────────────────────────────────┐'));
  console.log(chalk.cyan('│') + chalk.bold(' Application Services:                                 ') + chalk.cyan('│'));
  console.log(chalk.cyan('│') + `  • Web Frontend: ` + chalk.underline.blue('http://localhost:3000') + '             ' + chalk.cyan('│'));
  console.log(chalk.cyan('│') + `  • FastAPI Server: ` + chalk.underline.blue('http://localhost:8000') + '            ' + chalk.cyan('│'));
  console.log(chalk.cyan('│') + `  • API Docs:       ` + chalk.underline.blue('http://localhost:8000/docs') + '       ' + chalk.cyan('│'));
  console.log(chalk.cyan('├────────────────────────────────────────────────────────┤'));
  console.log(chalk.cyan('│') + chalk.bold(' Useful Development Commands:                          ') + chalk.cyan('│'));
  console.log(chalk.cyan('│') + `  • ${chalk.yellow('npm run dev')}      Start API & Web concurrently     ` + chalk.cyan('│'));
  console.log(chalk.cyan('│') + `  • ${chalk.yellow('npm test')}         Run automated test suite         ` + chalk.cyan('│'));
  console.log(chalk.cyan('│') + `  • ${chalk.yellow('npm run health')}   Verify services & database       ` + chalk.cyan('│'));
  console.log(chalk.cyan('└────────────────────────────────────────────────────────┘\n'));
};

async function main() {
  printBanner();

  // Step 1: Environment configuration
  const envSpinner = ora('Configuring environment variables...').start();
  try {
    const envPath = path.join(ROOT_DIR, '.env');
    const envExamplePath = path.join(ROOT_DIR, '.env.example');
    if (!existsSync(envPath)) {
      if (existsSync(envExamplePath)) {
        copyFileSync(envExamplePath, envPath);
        envSpinner.succeed('Environment file created from .env.example');
      } else {
        envSpinner.warn('.env.example not found; skipping .env creation');
      }
    } else {
      envSpinner.succeed('Environment file .env already present');
    }
  } catch (err) {
    envSpinner.fail(`Failed environment setup: ${err.message}`);
    process.exit(1);
  }

  // Step 2: Python environment setup
  const pySpinner = ora('Setting up Python virtual environment & dependencies...').start();
  const apiDir = path.join(ROOT_DIR, 'apps/api');
  try {
    const venvDir = path.join(apiDir, '.venv');
    if (!existsSync(venvDir)) {
      pySpinner.text = 'Creating Python venv...';
      await runCmd('python3 -m venv .venv', apiDir);
    }
    pySpinner.text = 'Upgrading pip, setuptools & wheel...';
    await runCmd('.venv/bin/python -m pip install -q --upgrade pip setuptools wheel', apiDir);

    pySpinner.text = 'Installing Python packages from requirements.txt...';
    await runCmd('.venv/bin/python -m pip install -q -r requirements.txt', apiDir);
    pySpinner.succeed('Python API environment configured');
  } catch (err) {
    pySpinner.fail(`Python environment setup failed: ${err.message}`);
    process.exit(1);
  }

  // Step 3: Node workspace dependencies
  const nodeSpinner = ora('Installing Node workspace dependencies...').start();
  try {
    await runCmd('npm install --silent --legacy-peer-deps');
    nodeSpinner.succeed('Node workspace dependencies installed');
  } catch (err) {
    nodeSpinner.fail(`Node dependencies installation failed: ${err.message}`);
    process.exit(1);
  }

  // Step 4: Infrastructure check & Docker Compose setup
  const infraSpinner = ora('Checking infrastructure services...').start();
  let dockerAvailable = false;
  try {
    await runCmd('docker info');
    dockerAvailable = true;
  } catch {
    dockerAvailable = false;
  }

  if (dockerAvailable) {
    try {
      infraSpinner.text = 'Starting PostgreSQL container via Docker Compose...';
      await runCmd('docker compose -f infra/docker-compose.yml up -d');
      infraSpinner.succeed('PostgreSQL Docker container started');
    } catch (err) {
      infraSpinner.warn(`Docker compose failed: ${err.message}. Ensure database is running on host.`);
    }
  } else {
    infraSpinner.info('Docker unavailable; expecting PostgreSQL running on host');
  }

  // Step 5: Database migrations
  const migSpinner = ora('Running database migrations (Alembic)...').start();
  try {
    await runCmd('.venv/bin/alembic upgrade head', apiDir);
    migSpinner.succeed('Database schema upgraded to head');
  } catch (err) {
    migSpinner.fail(`Database migration failed: ${err.message}`);
    process.exit(1);
  }

  // Step 6: Database connectivity test
  const dbSpinner = ora('Testing PostgreSQL database connectivity...').start();
  try {
    const pyCode = `
import asyncio
from sqlalchemy import text
from core.database import async_session_factory

async def check():
    async with async_session_factory() as session:
        await session.execute(text('SELECT 1'))

asyncio.run(check())
`;
    await new Promise((resolve, reject) => {
      const py = spawn('.venv/bin/python', ['-'], { cwd: apiDir });
      let errBuf = '';
      py.stderr.on('data', d => errBuf += d.toString());
      py.on('close', code => code === 0 ? resolve() : reject(new Error(errBuf)));
      py.stdin.write(pyCode);
      py.stdin.end();
    });
    dbSpinner.succeed('PostgreSQL database reachable');
  } catch (err) {
    dbSpinner.fail(`Database connectivity test failed: ${err.message}`);
    process.exit(1);
  }

  printSummary();

  const startDev = await confirm({
    message: 'Would you like to start the development servers now (npm run dev)?',
    default: false
  });

  if (startDev) {
    console.log('\n' + chalk.bold.cyan('Starting development servers...\n'));
    spawn('npm', ['run', 'dev'], { stdio: 'inherit', cwd: ROOT_DIR });
  }
}

main().catch((err) => {
  console.error(chalk.red('\n✖ Unexpected setup error:'), err);
  process.exit(1);
});
