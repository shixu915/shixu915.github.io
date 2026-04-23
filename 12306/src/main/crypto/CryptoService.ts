import { createCipheriv, createDecipheriv, randomBytes, pbkdf2Sync } from 'crypto';
import { app } from 'electron';
import { join } from 'path';
import { existsSync, readFileSync, writeFileSync, chmodSync } from 'fs';
import { Logger } from '../logger/Logger';

/**
 * 加密服务
 * 使用AES-256-CBC算法加密敏感数据
 */
export class CryptoService {
  private static instance: CryptoService;
  private key: Buffer;
  private logger: Logger;
  private readonly algorithm = 'aes-256-cbc';
  private readonly keyFile = '.keyring';

  private constructor() {
    this.logger = Logger.getInstance();
    this.key = this.loadOrCreateKey();
  }

  /**
   * 获取加密服务实例
   */
  public static getInstance(): CryptoService {
    if (!CryptoService.instance) {
      CryptoService.instance = new CryptoService();
    }
    return CryptoService.instance;
  }

  /**
   * 加载或创建密钥
   */
  private loadOrCreateKey(): Buffer {
    const keyPath = this.getKeyPath();

    try {
      if (existsSync(keyPath)) {
        // 加载现有密钥
        const keyData = readFileSync(keyPath);
        this.logger.info('密钥加载成功');
        return keyData;
      } else {
        // 创建新密钥
        const newKey = this.generateKey();
        writeFileSync(keyPath, newKey);
        
        // 设置文件权限为600（仅用户可读写）
        try {
          chmodSync(keyPath, 0o600);
        } catch (error) {
          this.logger.warn('无法设置密钥文件权限', error);
        }
        
        this.logger.info('新密钥创建成功');
        return newKey;
      }
    } catch (error) {
      this.logger.error('密钥加载失败', error);
      throw error;
    }
  }

  /**
   * 获取密钥文件路径
   */
  private getKeyPath(): string {
    const isDev = process.env.NODE_ENV === 'development';
    const basePath = isDev 
      ? join(__dirname, '../../../data')
      : join(app.getPath('userData'), 'data');
    
    return join(basePath, this.keyFile);
  }

  /**
   * 生成密钥
   */
  private generateKey(): Buffer {
    // 使用PBKDF2从随机盐生成256位密钥
    const salt = randomBytes(32);
    const password = randomBytes(32).toString('hex');
    return pbkdf2Sync(password, salt, 100000, 32, 'sha512');
  }

  /**
   * 加密字符串
   * @param plaintext 明文
   * @returns Base64编码的密文
   */
  public encrypt(plaintext: string): string {
    try {
      // 生成随机IV
      const iv = randomBytes(16);
      
      // 创建加密器
      const cipher = createCipheriv(this.algorithm, this.key, iv);
      
      // 加密
      let encrypted = cipher.update(plaintext, 'utf8', 'base64');
      encrypted += cipher.final('base64');
      
      // 将IV和密文组合（IV:密文）
      const result = `${iv.toString('base64')}:${encrypted}`;
      
      return result;
    } catch (error) {
      this.logger.error('加密失败', error);
      throw error;
    }
  }

  /**
   * 解密字符串
   * @param ciphertext Base64编码的密文（格式：IV:密文）
   * @returns 明文
   */
  public decrypt(ciphertext: string): string {
    try {
      // 分离IV和密文
      const parts = ciphertext.split(':');
      if (parts.length !== 2) {
        throw new Error('无效的密文格式');
      }
      
      const iv = Buffer.from(parts[0], 'base64');
      const encrypted = parts[1];
      
      // 创建解密器
      const decipher = createDecipheriv(this.algorithm, this.key, iv);
      
      // 解密
      let decrypted = decipher.update(encrypted, 'base64', 'utf8');
      decrypted += decipher.final('utf8');
      
      return decrypted;
    } catch (error) {
      this.logger.error('解密失败', error);
      throw error;
    }
  }

  /**
   * 加密对象
   */
  public encryptObject<T>(obj: T): string {
    const json = JSON.stringify(obj);
    return this.encrypt(json);
  }

  /**
   * 解密对象
   */
  public decryptObject<T>(ciphertext: string): T {
    const json = this.decrypt(ciphertext);
    return JSON.parse(json) as T;
  }

  /**
   * 验证密文是否有效
   */
  public isValidCiphertext(text: string): boolean {
    try {
      const parts = text.split(':');
      return parts.length === 2;
    } catch {
      return false;
    }
  }
}
