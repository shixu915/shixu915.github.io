import winston from 'winston';
import { app } from 'electron';
import { join } from 'path';
import { format } from 'logform';

/**
 * 日志服务
 * 基于winston实现多传输日志记录
 */
export class Logger {
  private static instance: Logger;
  private logger: winston.Logger;

  private constructor() {
    this.logger = this.createLogger();
  }

  /**
   * 获取日志服务实例
   */
  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  /**
   * 创建winston日志器
   */
  private createLogger(): winston.Logger {
    const logPath = this.getLogPath();

    // 自定义日志格式
    const customFormat = format.combine(
      format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      format.errors({ stack: true }),
      format.printf(({ level, message, timestamp, stack, ...metadata }) => {
        let log = `${timestamp} [${level.toUpperCase()}]: ${message}`;
        
        // 添加元数据
        if (Object.keys(metadata).length > 0) {
          log += ` ${JSON.stringify(metadata)}`;
        }
        
        // 添加堆栈信息
        if (stack) {
          log += `\n${stack}`;
        }
        
        return log;
      })
    );

    return winston.createLogger({
      level: process.env.NODE_ENV === 'development' ? 'debug' : 'info',
      format: customFormat,
      transports: [
        // 控制台输出
        new winston.transports.Console({
          format: format.combine(
            format.colorize(),
            customFormat
          )
        }),
        
        // 错误日志文件
        new winston.transports.File({
          filename: join(logPath, 'error.log'),
          level: 'error',
          maxsize: 5242880, // 5MB
          maxFiles: 5
        }),
        
        // 所有日志文件
        new winston.transports.File({
          filename: join(logPath, 'combined.log'),
          maxsize: 5242880, // 5MB
          maxFiles: 10
        })
      ]
    });
  }

  /**
   * 获取日志文件路径
   */
  private getLogPath(): string {
    const isDev = process.env.NODE_ENV === 'development';
    return isDev 
      ? join(__dirname, '../../../logs')
      : join(app.getPath('userData'), 'logs');
  }

  /**
   * 记录错误日志
   */
  public error(message: string, error?: any): void {
    if (error instanceof Error) {
      this.logger.error(message, { error: error.message, stack: error.stack });
    } else {
      this.logger.error(message, { error });
    }
  }

  /**
   * 记录警告日志
   */
  public warn(message: string, meta?: any): void {
    this.logger.warn(message, meta);
  }

  /**
   * 记录信息日志
   */
  public info(message: string, meta?: any): void {
    this.logger.info(message, meta);
  }

  /**
   * 记录调试日志
   */
  public debug(message: string, meta?: any): void {
    this.logger.debug(message, meta);
  }

  /**
   * 记录HTTP请求日志
   */
  public http(message: string, meta?: any): void {
    this.logger.http(message, meta);
  }

  /**
   * 获取winston日志器实例
   */
  public getWinstonLogger(): winston.Logger {
    return this.logger;
  }
}
