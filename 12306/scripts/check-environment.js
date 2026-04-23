/**
 * 环境检查和依赖安装脚本
 * 在应用启动前自动检查并安装所需依赖
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('========================================');
console.log('  小鲁班抢票助手 - 环境检查');
console.log('========================================\n');

/**
 * 检查Node.js版本
 */
function checkNodeVersion() {
  console.log('📌 检查Node.js版本...');
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
  
  if (majorVersion < 18) {
    console.error('❌ Node.js版本过低，需要 >= 18.0.0');
    console.error(`   当前版本: ${nodeVersion}`);
    console.error('   请访问 https://nodejs.org/ 下载最新版本');
    process.exit(1);
  }
  
  console.log(`✅ Node.js版本: ${nodeVersion}\n`);
}

/**
 * 检查npm版本
 */
function checkNpmVersion() {
  console.log('📌 检查npm版本...');
  try {
    const npmVersion = execSync('npm --version', { encoding: 'utf-8' }).trim();
    console.log(`✅ npm版本: ${npmVersion}\n`);
  } catch (error) {
    console.error('❌ npm未安装或不可用');
    process.exit(1);
  }
}

/**
 * 检查依赖是否已安装
 */
function checkDependencies() {
  console.log('📌 检查项目依赖...');
  const nodeModulesPath = path.join(__dirname, '..', 'node_modules');
  
  if (!fs.existsSync(nodeModulesPath)) {
    console.log('⚠️  依赖未安装，开始自动安装...\n');
    return false;
  }
  
  // 检查关键依赖
  const criticalDeps = ['electron', 'vue', 'better-sqlite3'];
  for (const dep of criticalDeps) {
    const depPath = path.join(nodeModulesPath, dep);
    if (!fs.existsSync(depPath)) {
      console.log(`⚠️  缺少关键依赖: ${dep}`);
      return false;
    }
  }
  
  console.log('✅ 依赖已安装\n');
  return true;
}

/**
 * 安装依赖
 */
function installDependencies() {
  console.log('📦 开始安装依赖...\n');
  
  try {
    // 使用npm install安装依赖
    const installProcess = spawn('npm', ['install'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'inherit',
      shell: true
    });
    
    installProcess.on('close', (code) => {
      if (code === 0) {
        console.log('\n✅ 依赖安装完成\n');
        startApplication();
      } else {
        console.error('\n❌ 依赖安装失败');
        console.error('   请尝试手动执行: npm install');
        process.exit(1);
      }
    });
  } catch (error) {
    console.error('❌ 依赖安装失败:', error.message);
    process.exit(1);
  }
}

/**
 * 启动应用
 */
function startApplication() {
  console.log('========================================');
  console.log('  启动应用');
  console.log('========================================\n');
  
  try {
    // 启动Electron应用
    const electronProcess = spawn('npm', ['run', 'start'], {
      cwd: path.join(__dirname, '..'),
      stdio: 'inherit',
      shell: true
    });
    
    electronProcess.on('close', (code) => {
      process.exit(code || 0);
    });
  } catch (error) {
    console.error('❌ 应用启动失败:', error.message);
    process.exit(1);
  }
}

/**
 * 主函数
 */
function main() {
  // 检查环境
  checkNodeVersion();
  checkNpmVersion();
  
  // 检查并安装依赖
  const depsInstalled = checkDependencies();
  
  if (depsInstalled) {
    // 依赖已安装，直接启动应用
    startApplication();
  } else {
    // 安装依赖后启动应用
    installDependencies();
  }
}

// 执行主函数
main();
