#!/usr/bin/env node
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const net = require('node:net');
const os = require('node:os');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const isWin = process.platform === 'win32';
const npmCmd = isWin ? 'npm.cmd' : 'npm';
const pnpmCmd = isWin ? 'pnpm.cmd' : 'pnpm';
const electronCmd = path.join(root, 'node_modules', '.bin', isWin ? 'electron.cmd' : 'electron');
const viteCmd = path.join(root, 'node_modules', '.bin', isWin ? 'vite.cmd' : 'vite');
const pythonVenv = isWin
  ? path.join(root, '.venv', 'Scripts', 'python.exe')
  : path.join(root, '.venv', 'bin', 'python');

const children = [];
const log = (message) => console.log(`[start-app] ${message}`);
const quoteWin = (value) => `"${String(value).replace(/"/g, '\\"')}"`;

function exists(command) {
  const result = spawnSync(isWin ? 'where' : 'which', [command], { stdio: 'ignore' });
  return result.status === 0;
}

function run(command, args, options = {}) {
  log(`${command} ${args.join(' ')}`);
  const result = spawnSync(command, args, { cwd: root, stdio: 'inherit', shell: false, ...options });
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function ensureNode() {
  if (!exists('node')) {
    console.error('Node.js 未安装。请先安装 Node.js 20+：https://nodejs.org/');
    process.exit(1);
  }
}

function ensurePackageManager() {
  if (!exists('pnpm')) {
    log('pnpm not found. Installing pnpm with npm...');
    run(npmCmd, ['install', '-g', 'pnpm']);
  }
}

function ensureNodeModules() {
  if (!fs.existsSync(path.join(root, 'node_modules'))) {
    log('node_modules not found. Installing Node/Electron dependencies...');
    run(exists('pnpm') ? pnpmCmd : npmCmd, exists('pnpm') ? ['install'] : ['install']);
  }
}

function findPython() {
  if (fs.existsSync(pythonVenv)) return pythonVenv;
  const codexPython = path.join(process.env.USERPROFILE || '', '.cache', 'codex-runtimes', 'codex-primary-runtime', 'dependencies', 'python', 'python.exe');
  if (isWin && fs.existsSync(codexPython)) return codexPython;
  const candidates = isWin ? ['python', 'py'] : ['python3', 'python'];
  for (const candidate of candidates) {
    const args = candidate === 'py' ? ['-3', '--version'] : ['--version'];
    const result = spawnSync(candidate, args, { stdio: 'ignore' });
    if (result.status === 0) return candidate;
  }
  return null;
}

function ensureVenv() {
  let python = findPython();
  if (!python) {
    console.error('Python 未安装。请先安装 Python 3.9+，并勾选 Add Python to PATH。');
    process.exit(1);
  }
  if (!fs.existsSync(pythonVenv)) {
    log('Creating Python venv...');
    if (python === 'py') run('py', ['-3', '-m', 'venv', '.venv']);
    else run(python, ['-m', 'venv', '.venv']);
  }
  log('Checking Python backend dependencies...');
  run(pythonVenv, ['-m', 'pip', 'install', '-r', path.join('backend', 'requirements.txt')]);
  return pythonVenv;
}

function getFreePort(start = 5173) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.listen(start, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => resolve(getFreePort(start + 1)));
  });
}

function getFfmpegPath() {
  try {
    return require('ffmpeg-static');
  } catch {
    return process.env.FFMPEG_PATH || '';
  }
}

function startBackend(python) {
  return new Promise((resolve, reject) => {
    const ffmpeg = getFfmpegPath();
    if (!ffmpeg) log('Bundled FFmpeg not found. Backend will try system FFMPEG_PATH/ffmpeg.');
    const child = spawn(python, ['backend/main.py', '--host', '127.0.0.1', '--port', '0', '--ffmpeg', ffmpeg || 'ffmpeg'], {
      cwd: root,
      env: {
        ...process.env,
        FFMPEG_PATH: ffmpeg || process.env.FFMPEG_PATH || 'ffmpeg',
        FUNSCRIPT_STUDIO_DATA_DIR: path.join(os.tmpdir(), 'funscript-studio-dev-data'),
      },
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
    children.push(child);
    let stderr = '';
    const timeout = setTimeout(() => reject(new Error(`Python backend 启动超时：${stderr}`)), 15000);
    child.stdout.on('data', (chunk) => {
      const text = String(chunk).trim();
      console.log(`[backend] ${text}`);
      try {
        const data = JSON.parse(text);
        if (data.endpoint) {
          clearTimeout(timeout);
          resolve(data.endpoint);
        }
      } catch {}
    });
    child.stderr.on('data', (chunk) => {
      stderr += String(chunk);
      process.stderr.write(`[backend] ${chunk}`);
    });
    child.on('exit', (code) => {
      if (code !== 0) console.error(`[backend] exited with ${code}`);
    });
  });
}

function startProcess(name, command, args, env = {}) {
  const useCmd = isWin && command.toLowerCase().endsWith('.cmd');
  const finalCommand = useCmd ? 'cmd.exe' : command;
  const finalArgs = useCmd ? ['/d', '/s', '/c', `${quoteWin(command)} ${args.map(quoteWin).join(' ')}`] : args;
  const child = spawn(finalCommand, finalArgs, {
    cwd: root,
    env: { ...process.env, ...env },
    stdio: 'inherit',
    windowsHide: false,
  });
  children.push(child);
  child.on('exit', (code) => {
    if (code && code !== 0) console.error(`[${name}] exited with ${code}`);
  });
  return child;
}

async function main() {
  if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log('Usage: node scripts/start-app.cjs');
    console.log('Starts Python backend, Vite dev server, and Electron with FS_BACKEND_URL.');
    return;
  }
  ensureNode();
  ensurePackageManager();
  ensureNodeModules();
  const python = ensureVenv();
  const backendUrl = await startBackend(python);
  const vitePort = await getFreePort(Number(process.env.VITE_PORT || 5173));
  const viteUrl = `http://127.0.0.1:${vitePort}`;
  log(`Backend endpoint: ${backendUrl}`);
  log(`Vite endpoint: ${viteUrl}`);
  startProcess('vite', viteCmd, ['--host', '127.0.0.1', '--port', String(vitePort)], { VITE_PORT: String(vitePort) });
  setTimeout(() => {
    startProcess('electron', electronCmd, ['.'], {
      VITE_DEV_SERVER_URL: viteUrl,
      FS_BACKEND_URL: backendUrl,
    });
  }, 1800);
}

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
process.on('exit', () => children.forEach((child) => child.kill()));
function shutdown() {
  children.forEach((child) => child.kill());
  process.exit(0);
}

main().catch((error) => {
  console.error(error);
  shutdown();
});
