import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';
import { DatabaseManager } from './database/DatabaseManager';
import { Logger } from './logger/Logger';
import { registerIPCHandlers } from './ipc/IPCHandlers';

let mainWindow: BrowserWindow | null = null;
const logger = Logger.getInstance();

/**
 * 创建主窗口
 */
function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: join(__dirname, 'preload.js')
    },
    icon: join(__dirname, '../../resources/icons/icon.png'),
    title: '小鲁班抢票助手'
  });

  // 开发环境加载开发服务器
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // 生产环境加载打包后的文件
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * 应用初始化
 */
async function initialize(): Promise<void> {
  try {
    logger.info('应用初始化开始');

    // 初始化数据库
    const dbManager = DatabaseManager.getInstance();
    dbManager.initialize();

    // 注册IPC处理器
    registerIPCHandlers();

    logger.info('应用初始化完成');
  } catch (error) {
    logger.error('应用初始化失败', error);
    app.quit();
  }
}

/**
 * 应用就绪
 */
app.whenReady().then(async () => {
  await initialize();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

/**
 * 所有窗口关闭
 */
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * 应用退出
 */
app.on('will-quit', () => {
  // 关闭数据库连接
  const dbManager = DatabaseManager.getInstance();
  dbManager.close();
  
  logger.info('应用退出');
});

/**
 * 捕获未处理的异常
 */
process.on('uncaughtException', (error) => {
  logger.error('未捕获的异常', error);
});

process.on('unhandledRejection', (reason) => {
  logger.error('未处理的Promise拒绝', reason);
});
