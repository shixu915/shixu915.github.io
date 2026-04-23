# 12306智能抢票助手技术设计文档

## 1. 文档信息

| 项目名称 | 小鲁班·抢票版 (12306 Intelligent Ticket Assistant) |
|---------|------------------------------------------------|
| 版本号   | v1.0.0                                         |
| 创建日期 | 2026-04-23                                     |
| 文档状态 | 初始版本                                       |
| 作者     | SDD Agent                                      |

## 2. 技术架构概览

### 2.1 架构设计原则

- **模块化设计**：各功能模块高内聚低耦合，便于独立开发和测试
- **分层架构**：表现层、业务逻辑层、数据访问层清晰分离
- **异步处理**：采用异步编程模型，提升系统响应性能
- **安全优先**：敏感数据加密存储，通信过程安全可控
- **跨平台兼容**：基于Electron框架，实现Windows和macOS跨平台支持

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         表现层 (Renderer Process)                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ 主界面   │  │ 任务管理 │  │ 日志窗口 │  │ 设置界面 │        │
│  │  UI      │  │   UI     │  │   UI     │  │   UI     │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ↕ IPC通信
┌─────────────────────────────────────────────────────────────────┐
│                      主进程层 (Main Process)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ 任务调度器   │  │ 抢票引擎     │  │ 通知管理器   │         │
│  │ Scheduler    │  │ TicketEngine │  │ Notifier     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ 账号管理器   │  │ 验证码处理器 │  │ 配置管理器   │         │
│  │ AccountMgr   │  │ CaptchaHandler│ │ ConfigMgr    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        数据访问层 (Data Layer)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ 任务仓库     │  │ 账号仓库     │  │ 日志仓库     │         │
│  │ TaskRepo     │  │ AccountRepo  │  │ LogRepo      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ 配置仓库     │  │ 加密服务     │                           │
│  │ ConfigRepo   │  │ CryptoService│                           │
│  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        存储层 (Storage Layer)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ SQLite数据库 │  │ 本地文件存储 │  │ 加密密钥库   │         │
│  │ tickets.db   │  │ logs/        │  │ .keyring     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 技术栈选型

| 技术领域 | 技术选型 | 选型理由 |
|---------|---------|---------|
| 桌面框架 | Electron 28+ | 跨平台支持、成熟生态、丰富UI组件库 |
| 前端框架 | Vue 3 + TypeScript | 响应式UI、类型安全、开发效率高 |
| UI组件库 | Element Plus | 成熟的Vue3组件库、美观易用 |
| 后端语言 | Node.js 20+ | 与Electron无缝集成、异步性能优秀 |
| 任务调度 | node-cron | 轻量级定时任务库、表达式灵活 |
| 数据库 | SQLite3 + better-sqlite3 | 轻量级嵌入式数据库、无需独立服务 |
| 加密库 | crypto (Node.js内置) | AES-256加密、无需第三方依赖 |
| HTTP客户端 | axios + axios-retry | 成熟稳定、支持重试机制 |
| 浏览器自动化 | Puppeteer | 官方维护、API友好、支持无头模式 |
| 日志库 | winston | 功能完善、支持多传输方式 |
| 打包工具 | electron-builder | 成熟的打包方案、支持多平台 |

## 3. 核心模块设计

### 3.1 任务调度模块 (TaskScheduler)

#### 3.1.1 模块职责

- 管理抢票任务的生命周期（创建、启动、暂停、停止、删除）
- 定时触发任务执行
- 维护任务状态机
- 支持断点续传

#### 3.1.2 类设计

```typescript
// 任务状态枚举
enum TaskStatus {
  PENDING = 'pending',        // 待执行
  SCHEDULED = 'scheduled',    // 已调度
  RUNNING = 'running',        // 执行中
  PAUSED = 'paused',          // 已暂停
  COMPLETED = 'completed',    // 已完成
  FAILED = 'failed',          // 失败
  CANCELLED = 'cancelled'     // 已取消
}

// 任务优先级
enum TaskPriority {
  LOW = 1,
  NORMAL = 5,
  HIGH = 10,
  URGENT = 20
}

// 任务接口
interface ITask {
  id: string;                           // 任务ID
  name: string;                         // 任务名称
  status: TaskStatus;                   // 任务状态
  priority: TaskPriority;               // 优先级
  config: TaskConfig;                   // 任务配置
  schedule: ScheduleConfig;             // 调度配置
  createdAt: Date;                      // 创建时间
  updatedAt: Date;                      // 更新时间
  startedAt?: Date;                     // 启动时间
  completedAt?: Date;                   // 完成时间
  retryCount: number;                   // 重试次数
  maxRetry: number;                     // 最大重试次数
  checkpoint?: TaskCheckpoint;          // 断点信息
}

// 任务配置
interface TaskConfig {
  departure: string;                    // 出发地
  destination: string;                  // 目的地
  date: string;                         // 出发日期 (YYYY-MM-DD)
  trainNumbers?: string[];              // 车次偏好（可选）
  seatTypes: SeatType[];                // 座位类型偏好
  passengers: Passenger[];              // 乘客信息
  enableWaitlist: boolean;              // 是否启用候补
  waitlistPriority?: number;            // 候补优先级
}

// 调度配置
interface ScheduleConfig {
  startTime: Date;                      // 开始时间
  endTime?: Date;                       // 结束时间
  interval: number;                     // 执行间隔（秒）
  cronExpression?: string;              // cron表达式（可选）
}

// 断点信息
interface TaskCheckpoint {
  step: string;                         // 当前步骤
  data: any;                            // 步骤数据
  timestamp: Date;                      // 保存时间
}

// 任务调度器类
class TaskScheduler {
  private tasks: Map<string, ITask>;
  private cronJobs: Map<string, CronJob>;
  private taskEngine: TicketEngine;
  private taskRepo: TaskRepository;

  // 创建任务
  async createTask(config: TaskConfig, schedule: ScheduleConfig): Promise<ITask>;

  // 启动任务
  async startTask(taskId: string): Promise<void>;

  // 暂停任务
  async pauseTask(taskId: string): Promise<void>;

  // 恢复任务
  async resumeTask(taskId: string): Promise<void>;

  // 取消任务
  async cancelTask(taskId: string): Promise<void>;

  // 删除任务
  async deleteTask(taskId: string): Promise<void>;

  // 获取任务列表
  async getTasks(filter?: TaskFilter): Promise<ITask[]>;

  // 获取任务详情
  async getTask(taskId: string): Promise<ITask>;

  // 更新任务
  async updateTask(taskId: string, updates: Partial<ITask>): Promise<ITask>;

  // 保存断点
  async saveCheckpoint(taskId: string, checkpoint: TaskCheckpoint): Promise<void>;

  // 恢复断点
  async restoreCheckpoint(taskId: string): Promise<TaskCheckpoint | null>;

  // 系统启动时恢复未完成任务
  async restoreTasks(): Promise<void>;
}
```

#### 3.1.3 状态转换图

```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │ startTask()
                         ↓
                    ┌──────────┐
          ┌────────→│SCHEDULED │←────────┐
          │         └────┬─────┘         │
          │              │ trigger       │
          │              ↓               │
          │         ┌──────────┐         │
   resume │         │ RUNNING  │         │ pause
          │         └────┬─────┘         │
          │              │               │
          │              ├─complete─────→│
          │              │               │
          │              ├─fail─────────→│
          │              │               │
          │              ↓               │
          │         ┌──────────┐         │
          └─────────│  PAUSED  │─────────┘
                    └────┬─────┘
                         │ cancel()
                         ↓
                    ┌──────────┐
                    │CANCELLED │
                    └──────────┘

        RUNNING ──complete──→ COMPLETED
        RUNNING ──fail──────→ FAILED
```

### 3.2 抢票引擎模块 (TicketEngine)

#### 3.2.1 模块职责

- 执行抢票核心流程
- 与12306网站交互
- 实现智能抢票策略
- 处理验证码
- 提交候补订单

#### 3.2.2 类设计

```typescript
// 抢票结果
interface TicketResult {
  success: boolean;
  message: string;
  orderId?: string;
  orderInfo?: OrderInfo;
  waitlistId?: string;
  timestamp: Date;
}

// 订单信息
interface OrderInfo {
  trainNumber: string;
  departure: string;
  destination: string;
  departureTime: string;
  arrivalTime: string;
  seatType: string;
  price: number;
  passengers: string[];
}

// 抢票策略配置
interface StrategyConfig {
  minDelay: number;                     // 最小延迟（毫秒）
  maxDelay: number;                     // 最大延迟（毫秒）
  maxRetry: number;                     // 最大重试次数
  timeout: number;                      // 请求超时（毫秒）
  enableOCR: boolean;                   // 是否启用OCR
  simulateHuman: boolean;               // 是否模拟人工
}

// 抢票引擎类
class TicketEngine {
  private browser: Browser;
  private page: Page;
  private accountMgr: AccountManager;
  private captchaHandler: CaptchaHandler;
  private strategy: StrategyConfig;
  private logger: Logger;

  // 初始化浏览器
  async initialize(): Promise<void>;

  // 登录12306
  async login(username: string, password: string): Promise<boolean>;

  // 查询余票
  async queryTickets(config: TaskConfig): Promise<TicketInfo[]>;

  // 提交订单
  async submitOrder(ticket: TicketInfo, passengers: Passenger[]): Promise<TicketResult>;

  // 提交候补订单
  async submitWaitlist(config: TaskConfig): Promise<TicketResult>;

  // 执行抢票流程
  async execute(task: ITask): Promise<TicketResult>;

  // 智能延迟
  private async smartDelay(): Promise<void>;

  // 模拟人工操作
  private async simulateHumanAction(action: () => Promise<void>): Promise<void>;

  // 处理验证码
  private async handleCaptcha(): Promise<string>;

  // 检查余票并抢票
  private async checkAndGrab(task: ITask): Promise<TicketResult>;

  // 关闭浏览器
  async close(): Promise<void>;
}
```

#### 3.2.3 抢票流程图

```
┌─────────────┐
│   开始      │
└──────┬──────┘
       ↓
┌─────────────┐
│ 初始化浏览器│
└──────┬──────┘
       ↓
┌─────────────┐
│  登录12306  │←────────┐
└──────┬──────┘         │
       ↓                │
  ┌────────┐            │
  │验证码？│──Yes──→┌──────────┐
  └────┬───┘        │处理验证码│
       │            └─────┬────┘
       No                 │
       ↓                  │
┌─────────────┐           │
│  查询余票   │           │
└──────┬──────┘           │
       ↓                  │
  ┌────────┐              │
  │有余票？│              │
  └────┬───┘              │
       │                  │
   Yes │ No               │
       ↓                  ↓
┌─────────────┐     ┌──────────┐
│  提交订单   │     │启用候补？│
└──────┬──────┘     └────┬─────┘
       ↓                 │
  ┌────────┐         Yes │ No
  │成功？  │             │
  └────┬───┘             ↓
       │            ┌──────────┐
   Yes │ No         │提交候补  │
       ↓            └────┬─────┘
┌─────────────┐          │
│  返回成功   │          ↓
└──────┬──────┘     ┌──────────┐
       │            │智能延迟  │
       │            └────┬─────┘
       │                 │
       │                 └──────┘(循环)
       ↓
┌─────────────┐
│   结束      │
└─────────────┘
```

### 3.3 通知管理模块 (NotificationManager)

#### 3.3.1 模块职责

- 发送抢票结果通知
- 支持多种通知方式（弹窗、邮件、短信）
- 管理通知配置
- 记录通知历史

#### 3.3.2 类设计

```typescript
// 通知类型
enum NotificationType {
  POPUP = 'popup',             // 弹窗通知
  EMAIL = 'email',             // 邮件通知
  SMS = 'sms'                  // 短信通知
}

// 通知级别
enum NotificationLevel {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error'
}

// 通知内容
interface INotification {
  id: string;
  type: NotificationType;
  level: NotificationLevel;
  title: string;
  message: string;
  data?: any;
  timestamp: Date;
  read: boolean;
}

// 通知配置
interface NotificationConfig {
  enablePopup: boolean;
  enableEmail: boolean;
  enableSMS: boolean;
  emailConfig?: EmailConfig;
  smsConfig?: SMSConfig;
}

// 邮件配置
interface EmailConfig {
  smtp: string;
  port: number;
  username: string;
  password: string;
  from: string;
  to: string;
}

// 短信配置
interface SMSConfig {
  provider: string;
  apiKey: string;
  phone: string;
}

// 通知管理器类
class NotificationManager {
  private config: NotificationConfig;
  private notificationRepo: NotificationRepository;
  private logger: Logger;

  // 发送通知
  async send(notification: INotification): Promise<boolean>;

  // 发送弹窗通知
  private async sendPopup(notification: INotification): Promise<boolean>;

  // 发送邮件通知
  private async sendEmail(notification: INotification): Promise<boolean>;

  // 发送短信通知
  private async sendSMS(notification: INotification): Promise<boolean>;

  // 获取通知列表
  async getNotifications(filter?: NotificationFilter): Promise<INotification[]>;

  // 标记为已读
  async markAsRead(notificationId: string): Promise<void>;

  // 更新配置
  async updateConfig(config: NotificationConfig): Promise<void>;
}
```

### 3.4 账号管理模块 (AccountManager)

#### 3.4.1 模块职责

- 管理用户12306账号信息
- 加密存储敏感信息
- 验证账号有效性
- 管理乘客信息

#### 3.4.2 类设计

```typescript
// 账号信息
interface IAccount {
  id: string;
  username: string;
  encryptedPassword: string;
  passengers: Passenger[];
  createdAt: Date;
  updatedAt: Date;
  lastVerified?: Date;
  isValid: boolean;
}

// 乘客信息
interface Passenger {
  name: string;
  idType: string;                       // 证件类型
  idNumber: string;                     // 证件号码
  phone?: string;                       // 手机号
}

// 账号管理器类
class AccountManager {
  private accountRepo: AccountRepository;
  private cryptoService: CryptoService;
  private logger: Logger;

  // 保存账号
  async saveAccount(username: string, password: string, passengers: Passenger[]): Promise<IAccount>;

  // 获取账号
  async getAccount(): Promise<IAccount | null>;

  // 获取解密后的密码
  async getDecryptedPassword(account: IAccount): Promise<string>;

  // 验证账号
  async verifyAccount(username: string, password: string): Promise<boolean>;

  // 更新乘客信息
  async updatePassengers(passengers: Passenger[]): Promise<void>;

  // 删除账号
  async deleteAccount(): Promise<void>;
}
```

### 3.5 验证码处理模块 (CaptchaHandler)

#### 3.5.1 模块职责

- 识别验证码图片
- 支持手动输入和OCR自动识别
- 处理验证码失败重试

#### 3.5.2 类设计

```typescript
// 验证码类型
enum CaptchaType {
  IMAGE = 'image',             // 图片验证码
  SLIDE = 'slide',             // 滑块验证码
  CLICK = 'click'              // 点击验证码
}

// 验证码结果
interface CaptchaResult {
  success: boolean;
  code?: string;
  position?: { x: number; y: number };
  message?: string;
}

// 验证码处理器类
class CaptchaHandler {
  private ocrEnabled: boolean;
  private ocrService?: OCRService;
  private logger: Logger;

  // 处理验证码
  async handle(image: Buffer, type: CaptchaType): Promise<CaptchaResult>;

  // OCR识别
  private async recognizeByOCR(image: Buffer, type: CaptchaType): Promise<CaptchaResult>;

  // 手动输入
  private async manualInput(image: Buffer): Promise<CaptchaResult>;

  // 显示验证码窗口（供用户手动输入）
  private async showCaptchaWindow(image: Buffer): Promise<string>;
}
```

### 3.6 加密服务模块 (CryptoService)

#### 3.6.1 模块职责

- 提供AES-256加密/解密功能
- 管理加密密钥
- 确保数据安全存储

#### 3.6.2 类设计

```typescript
// 加密服务类
class CryptoService {
  private algorithm: string = 'aes-256-cbc';
  private keyPath: string;
  private key: Buffer;
  private iv: Buffer;

  // 初始化（生成或加载密钥）
  async initialize(): Promise<void>;

  // 加密
  encrypt(plainText: string): string;

  // 解密
  decrypt(cipherText: string): string;

  // 生成密钥
  private generateKey(): Buffer;

  // 保存密钥到本地
  private saveKey(): Promise<void>;

  // 从本地加载密钥
  private loadKey(): Promise<Buffer>;
}
```

## 4. 数据模型设计

### 4.1 数据库表结构

#### 4.1.1 任务表 (tasks)

```sql
CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  priority INTEGER DEFAULT 5,
  config TEXT NOT NULL,              -- JSON格式
  schedule TEXT NOT NULL,            -- JSON格式
  checkpoint TEXT,                   -- JSON格式
  retry_count INTEGER DEFAULT 0,
  max_retry INTEGER DEFAULT 10,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  started_at TEXT,
  completed_at TEXT
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created ON tasks(created_at DESC);
```

#### 4.1.2 账号表 (accounts)

```sql
CREATE TABLE accounts (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  encrypted_password TEXT NOT NULL,
  passengers TEXT,                   -- JSON格式
  is_valid INTEGER DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_verified TEXT
);
```

#### 4.1.3 通知表 (notifications)

```sql
CREATE TABLE notifications (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  level TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  data TEXT,                         -- JSON格式
  read INTEGER DEFAULT 0,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

#### 4.1.4 日志表 (logs)

```sql
CREATE TABLE logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  level TEXT NOT NULL,
  source TEXT,
  message TEXT NOT NULL,
  data TEXT,                         -- JSON格式
  created_at TEXT NOT NULL
);

CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_created ON logs(created_at DESC);
```

#### 4.1.5 配置表 (configs)

```sql
CREATE TABLE configs (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

### 4.2 数据访问层设计

```typescript
// 通用仓库接口
interface IRepository<T> {
  create(entity: T): Promise<T>;
  update(id: string, updates: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
  findById(id: string): Promise<T | null>;
  findAll(filter?: any): Promise<T[]>;
}

// 任务仓库
class TaskRepository implements IRepository<ITask> {
  private db: Database;

  async create(task: ITask): Promise<ITask>;
  async update(id: string, updates: Partial<ITask>): Promise<ITask>;
  async delete(id: string): Promise<void>;
  async findById(id: string): Promise<ITask | null>;
  async findAll(filter?: TaskFilter): Promise<ITask[]>;
  async findByStatus(status: TaskStatus): Promise<ITask[]>;
}

// 账号仓库
class AccountRepository implements IRepository<IAccount> {
  private db: Database;

  async create(account: IAccount): Promise<IAccount>;
  async update(id: string, updates: Partial<IAccount>): Promise<IAccount>;
  async delete(id: string): Promise<void>;
  async findById(id: string): Promise<IAccount | null>;
  async findByUsername(username: string): Promise<IAccount | null>;
}

// 日志仓库
class LogRepository {
  private db: Database;

  async save(log: ILog): Promise<void>;
  async findByLevel(level: string): Promise<ILog[]>;
  async findByDateRange(start: Date, end: Date): Promise<ILog[]>;
  async clearOldLogs(before: Date): Promise<void>;
}
```

## 5. 接口设计

### 5.1 IPC通信接口

Electron主进程与渲染进程通过IPC（Inter-Process Communication）进行通信。

#### 5.1.1 任务相关接口

```typescript
// 渲染进程 → 主进程
ipcRenderer.invoke('task:create', config, schedule): Promise<ITask>
ipcRenderer.invoke('task:update', taskId, updates): Promise<ITask>
ipcRenderer.invoke('task:delete', taskId): Promise<void>
ipcRenderer.invoke('task:start', taskId): Promise<void>
ipcRenderer.invoke('task:pause', taskId): Promise<void>
ipcRenderer.invoke('task:resume', taskId): Promise<void>
ipcRenderer.invoke('task:cancel', taskId): Promise<void>
ipcRenderer.invoke('task:getAll', filter): Promise<ITask[]>
ipcRenderer.invoke('task:getById', taskId): Promise<ITask>

// 主进程 → 渲染进程（事件通知）
ipcMain.on('task:statusChanged', (event, taskId, status) => {})
ipcMain.on('task:progress', (event, taskId, progress) => {})
ipcMain.on('task:completed', (event, taskId, result) => {})
```

#### 5.1.2 账号相关接口

```typescript
ipcRenderer.invoke('account:save', username, password, passengers): Promise<IAccount>
ipcRenderer.invoke('account:get'): Promise<IAccount | null>
ipcRenderer.invoke('account:verify', username, password): Promise<boolean>
ipcRenderer.invoke('account:delete'): Promise<void>
ipcRenderer.invoke('account:updatePassengers', passengers): Promise<void>
```

#### 5.1.3 通知相关接口

```typescript
ipcRenderer.invoke('notification:send', notification): Promise<boolean>
ipcRenderer.invoke('notification:getAll', filter): Promise<INotification[]>
ipcRenderer.invoke('notification:markAsRead', notificationId): Promise<void>
ipcRenderer.invoke('notification:updateConfig', config): Promise<void>
```

#### 5.1.4 配置相关接口

```typescript
ipcRenderer.invoke('config:get', key): Promise<any>
ipcRenderer.invoke('config:set', key, value): Promise<void>
ipcRenderer.invoke('config:getAll'): Promise<Record<string, any>>
```

#### 5.1.5 日志相关接口

```typescript
ipcRenderer.invoke('log:getAll', filter): Promise<ILog[]>
ipcRenderer.invoke('log:export', format): Promise<string>
ipcRenderer.invoke('log:clear'): Promise<void>
```

### 5.2 12306网站交互接口

```typescript
// 12306 API封装
class Railway12306API {
  private baseURL: string = 'https://kyfw.12306.cn/otn/';
  private session: AxiosInstance;

  // 登录
  async login(username: string, password: string, captcha: string): Promise<LoginResult>;

  // 获取验证码
  async getCaptcha(): Promise<Buffer>;

  // 查询余票
  async queryTickets(params: QueryParams): Promise<TicketInfo[]>;

  // 提交订单
  async submitOrder(params: OrderParams): Promise<OrderResult>;

  // 提交候补
  async submitWaitlist(params: WaitlistParams): Promise<WaitlistResult>;

  // 检查订单状态
  async checkOrderStatus(orderId: string): Promise<OrderStatus>;

  // 获取乘客信息
  async getPassengers(): Promise<Passenger[]>;
}
```

## 6. 安全设计

### 6.1 数据加密

- **加密算法**：AES-256-CBC
- **密钥管理**：密钥存储在用户本地 `.keyring` 文件中，不上传至任何服务器
- **加密范围**：用户密码、账号信息、敏感配置项

### 6.2 通信安全

- 使用HTTPS协议与12306网站通信
- 不保存用户Cookie到数据库，仅在内存中维护会话
- 定期清理临时文件和缓存

### 6.3 异常检测

- 检测异常登录行为（频繁失败、异地登录等）
- 检测机器人识别特征，动态调整策略
- 记录所有操作日志，便于审计

## 7. 性能优化设计

### 7.1 异步处理

- 所有I/O操作使用异步API
- 抢票流程采用异步流水线处理
- 使用Promise.all并发执行独立任务

### 7.2 资源管理

- 浏览器实例复用，避免频繁创建销毁
- 数据库连接池管理
- 日志文件定期轮转，避免过大

### 7.3 缓存策略

- 缓存车站代码表、车次信息等静态数据
- 缓存用户配置，减少数据库访问
- 设置合理的缓存过期时间

## 8. 部署架构

### 8.1 目录结构

```
小鲁班-抢票版/
├── package.json                 # 项目配置
├── electron-builder.yml         # 打包配置
├── src/
│   ├── main/                    # 主进程代码
│   │   ├── index.ts            # 主进程入口
│   │   ├── scheduler/          # 任务调度模块
│   │   ├── engine/             # 抢票引擎模块
│   │   ├── notification/       # 通知管理模块
│   │   ├── account/            # 账号管理模块
│   │   ├── captcha/            # 验证码处理模块
│   │   ├── crypto/             # 加密服务模块
│   │   ├── database/           # 数据库模块
│   │   └── ipc/                # IPC通信模块
│   ├── renderer/               # 渲染进程代码
│   │   ├── index.html         # 主页面
│   │   ├── App.vue            # Vue根组件
│   │   ├── components/        # UI组件
│   │   ├── views/             # 页面视图
│   │   ├── store/             # 状态管理
│   │   └── utils/             # 工具函数
│   └── shared/                 # 共享代码
│       ├── types/             # 类型定义
│       └── constants/         # 常量定义
├── resources/                  # 资源文件
│   ├── icons/                 # 图标
│   └── images/                # 图片
├── data/                       # 数据目录（运行时创建）
│   ├── tickets.db             # SQLite数据库
│   ├── logs/                  # 日志文件
│   └── .keyring               # 加密密钥
└── dist/                       # 打包输出目录
```

### 8.2 打包配置

```yaml
# electron-builder.yml
appId: com.xiaoluban.ticket-assistant
productName: 小鲁班·抢票版
directories:
  output: dist
  buildResources: resources

win:
  target:
    - nsis
    - portable
  icon: resources/icons/icon.ico

mac:
  target:
    - dmg
    - zip
  icon: resources/icons/icon.icns

nsis:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true

dmg:
  contents:
    - x: 130
      y: 220
    - x: 410
      y: 220
      type: link
      path: /Applications
```

## 9. 测试策略

### 9.1 单元测试

- 测试框架：Jest
- 测试覆盖：核心业务逻辑、工具函数
- 模拟对象：数据库、外部API

### 9.2 集成测试

- 测试各模块间协作
- 测试IPC通信
- 测试数据库操作

### 9.3 端到端测试

- 测试完整抢票流程
- 测试用户界面交互
- 测试跨平台兼容性

## 10. 监控与日志

### 10.1 日志级别

- **ERROR**：错误信息，需要立即处理
- **WARN**：警告信息，可能存在问题
- **INFO**：一般信息，记录关键操作
- **DEBUG**：调试信息，详细执行过程

### 10.2 日志格式

```typescript
interface ILog {
  timestamp: string;              // ISO 8601格式
  level: string;                  // 日志级别
  source: string;                 // 来源模块
  message: string;                // 日志消息
  data?: any;                     // 附加数据
}
```

### 10.3 日志输出

- 控制台输出（开发环境）
- 文件输出（生产环境）
- 数据库存储（便于查询）

## 11. 扩展性设计

### 11.1 插件机制

- 支持自定义通知方式插件
- 支持自定义验证码识别插件
- 支持自定义抢票策略插件

### 11.2 配置扩展

- 支持用户自定义配置项
- 支持导入导出配置
- 支持配置版本管理

## 12. 变更历史

| 版本 | 日期 | 变更内容 | 变更人 |
|-----|------|---------|--------|
| v1.0.0 | 2026-04-23 | 初始版本创建 | SDD Agent |
