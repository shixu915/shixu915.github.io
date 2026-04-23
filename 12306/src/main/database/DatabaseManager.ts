import Database from 'better-sqlite3';
import { app } from 'electron';
import { join } from 'path';
import { readFileSync } from 'fs';
import { Logger } from '../logger/Logger';

/**
 * 数据库管理器 - 单例模式
 * 负责SQLite数据库的连接管理和初始化
 */
export class DatabaseManager {
  private static instance: DatabaseManager;
  private db: Database.Database | null = null;
  private logger: Logger;

  private constructor() {
    this.logger = Logger.getInstance();
  }

  /**
   * 获取数据库管理器实例
   */
  public static getInstance(): DatabaseManager {
    if (!DatabaseManager.instance) {
      DatabaseManager.instance = new DatabaseManager();
    }
    return DatabaseManager.instance;
  }

  /**
   * 初始化数据库连接
   */
  public initialize(): void {
    if (this.db) {
      return;
    }

    try {
      // 获取数据库文件路径
      const dbPath = this.getDatabasePath();
      this.logger.info(`数据库路径: ${dbPath}`);

      // 创建数据库连接
      this.db = new Database(dbPath, {
        verbose: (message) => {
          this.logger.debug(`SQL: ${message}`);
        }
      });

      // 启用外键约束
      this.db.pragma('foreign_keys = ON');

      // 初始化数据库结构
      this.initDatabase();

      this.logger.info('数据库初始化成功');
    } catch (error) {
      this.logger.error('数据库初始化失败', error);
      throw error;
    }
  }

  /**
   * 获取数据库文件路径
   */
  private getDatabasePath(): string {
    // 开发环境使用项目目录，生产环境使用用户数据目录
    const isDev = process.env.NODE_ENV === 'development';
    const basePath = isDev 
      ? join(__dirname, '../../../data')
      : join(app.getPath('userData'), 'data');
    
    return join(basePath, 'ticket_assistant.db');
  }

  /**
   * 初始化数据库结构
   */
  private initDatabase(): void {
    if (!this.db) {
      throw new Error('数据库未初始化');
    }

    try {
      // 读取初始化SQL脚本
      const sqlPath = join(__dirname, '../../../data/init.sql');
      const sql = readFileSync(sqlPath, 'utf-8');

      // 执行SQL脚本
      this.db.exec(sql);

      this.logger.info('数据库结构初始化完成');
    } catch (error) {
      this.logger.error('数据库结构初始化失败', error);
      throw error;
    }
  }

  /**
   * 获取数据库连接
   */
  public getDatabase(): Database.Database {
    if (!this.db) {
      this.initialize();
    }
    return this.db!;
  }

  /**
   * 执行事务
   */
  public transaction<T>(fn: () => T): T {
    const db = this.getDatabase();
    return db.transaction(fn)();
  }

  /**
   * 关闭数据库连接
   */
  public close(): void {
    if (this.db) {
      this.db.close();
      this.db = null;
      this.logger.info('数据库连接已关闭');
    }
  }

  /**
   * 执行查询
   */
  public query<T = any>(sql: string, params: any[] = []): T[] {
    const db = this.getDatabase();
    const stmt = db.prepare(sql);
    return stmt.all(...params) as T[];
  }

  /**
   * 执行单条查询
   */
  public queryOne<T = any>(sql: string, params: any[] = []): T | undefined {
    const db = this.getDatabase();
    const stmt = db.prepare(sql);
    return stmt.get(...params) as T | undefined;
  }

  /**
   * 执行更新操作
   */
  public execute(sql: string, params: any[] = []): Database.RunResult {
    const db = this.getDatabase();
    const stmt = db.prepare(sql);
    return stmt.run(...params);
  }

  /**
   * 批量执行
   */
  public executeBatch(sql: string, paramsList: any[][]): Database.RunResult[] {
    const db = this.getDatabase();
    const stmt = db.prepare(sql);
    const results: Database.RunResult[] = [];

    const insertMany = db.transaction((items: any[][]) => {
      for (const params of items) {
        results.push(stmt.run(...params));
      }
    });

    insertMany(paramsList);
    return results;
  }
}
