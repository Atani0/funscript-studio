#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const outRoot = path.join(root, 'outputs');
const portableName = process.env.PORTABLE_NAME || 'FunscriptStudio-Portable';
const portableDir = path.join(outRoot, portableName);
const appDir = path.join(portableDir, 'resources', 'app');
const isWin = process.platform === 'win32';

const clean = target => fs.rmSync(target, { recursive: true, force: true });
const ensure = target => fs.mkdirSync(target, { recursive: true });
const shouldCopy = source => {
  const normalized = source.replace(/\\/g, '/');
  const base = path.basename(source);
  if (base === '__pycache__') return false;
  if (base === '.pytest_cache' || base === '.mypy_cache' || base === '.ruff_cache') return false;
  if (normalized.includes('/perception_outputs')) return false;
  if (normalized.includes('/training_datasets')) return false;
  if (normalized.includes('/generated')) return false;
  if (/\.(pyc|pyo|log)$/i.test(base)) return false;
  return true;
};
const copy = (from, to) => fs.cpSync(from, to, { recursive: true, force: true, dereference: true, filter: shouldCopy });
const writeJson = (file, data) => fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');

const electronExe = require('electron');
const electronDist = path.dirname(electronExe);

ensure(outRoot);
clean(portableDir);
ensure(appDir);

console.log('[portable] copying Electron runtime...');
copy(electronDist, portableDir);

console.log('[portable] copying app files...');
copy(path.join(root, 'dist'), path.join(appDir, 'dist'));
copy(path.join(root, 'dist-electron'), path.join(appDir, 'dist-electron'));
copy(path.join(root, 'backend'), path.join(appDir, 'backend'));
const backendExe = path.join(root, 'dist', 'funscript-backend.exe');
if (fs.existsSync(backendExe)) {
  console.log('[portable] copying standalone Python backend...');
  fs.copyFileSync(backendExe, path.join(appDir, 'backend', 'funscript-backend.exe'));
}

console.log('[portable] copying runtime node modules...');
ensure(path.join(appDir, 'node_modules'));
copy(path.join(root, 'node_modules', 'ffmpeg-static'), path.join(appDir, 'node_modules', 'ffmpeg-static'));

const sourcePackage = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
writeJson(path.join(appDir, 'package.json'), {
  name: sourcePackage.name,
  version: sourcePackage.version,
  productName: 'Funscript Studio',
  main: 'dist-electron/main.js',
  dependencies: {
    'ffmpeg-static': sourcePackage.dependencies['ffmpeg-static'],
  },
});

fs.writeFileSync(
  path.join(portableDir, 'README-运行说明.txt'),
  [
    'Funscript Studio Portable',
    '',
    '运行方式：',
    '1. 双击 Funscript Studio.exe',
    '2. 如果自动生成或感知分析提示 Python 不存在，请先安装 Python 3.9+，或运行项目源码里的 install.bat 初始化环境。',
    '',
    '说明：',
    '- 视频播放、时间轴编辑、funscript 导入/导出不需要额外配置。',
    '- 自动生成和感知分析会优先启动本地 Python backend；缺少可选 CV/pose 依赖时会自动使用 fallback。',
  ].join('\r\n'),
  'utf8',
);

fs.writeFileSync(
  path.join(portableDir, 'README-运行说明.txt'),
  [
    `Funscript Studio ${sourcePackage.version} Portable Preview`,
    '',
    '运行方式：',
    '1. 双击 Funscript Studio.exe',
    '2. 自动生成、感知分析和混合生成会优先使用随包附带的本地 Python backend。',
    '',
    '说明：',
    '- 这是 Alpha / Preview 版本，生成脚本仍需人工检查。',
    '- 软件默认本地运行，不会自动上传视频、脚本或训练数据。',
    '- 设备连接功能请先设置安全限位，并在预览模式中确认脚本。',
    '- 便携包不应包含 data/、训练集、视频样本或用户 funscript。',
  ].join('\r\n'),
  'utf8',
);

if (isWin) {
  const electronBinary = path.join(portableDir, 'electron.exe');
  const targetBinary = path.join(portableDir, 'Funscript Studio.exe');
  if (fs.existsSync(electronBinary)) fs.renameSync(electronBinary, targetBinary);
}

console.log(`[portable] output: ${portableDir}`);
