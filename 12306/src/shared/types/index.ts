/**
 * 任务状态枚举
 */
export enum TaskStatus {
  PENDING = 'pending',       // 待执行
  SCHEDULED = 'scheduled',   // 已调度
  RUNNING = 'running',       // 运行中
  PAUSED = 'paused',         // 已暂停
  SUCCESS = 'success',       // 成功
  FAILED = 'failed',         // 失败
  CANCELLED = 'cancelled'    // 已取消
}

/**
 * 通知状态枚举
 */
export enum NotificationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  FAILED = 'failed'
}

/**
 * 日志级别枚举
 */
export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug'
}

/**
 * 任务配置接口
 */
export interface ITaskConfig {
  departure: string;         // 出发地
  destination: string;       // 目的地
  date: string;              // 出发日期
  trainTypes?: string[];     // 车次类型偏好
  seatTypes: string[];       // 座位类型
  passengers: string[];      // 乘客姓名
  enableWaitlist: boolean;   // 是否启用候补
  accountId: number;         // 账号ID
}

/**
 * 任务调度配置接口
 */
export interface ITaskSchedule {
  executeTime: string;       // 执行时间
  retryTimes: number;        // 重试次数
  retryDelay: number;        // 重试延迟
}

/**
 * 任务断点信息接口
 */
export interface ITaskCheckpoint {
  lastAttemptTime: string;   // 最后尝试时间
  attemptCount: number;      // 尝试次数
  currentStep: string;       // 当前步骤
  sessionId?: string;        // 会话ID
  cookies?: any;             // Cookie信息
}

/**
 * 任务结果接口
 */
export interface ITaskResult {
  success: boolean;
  message: string;
  orderId?: string;          // 订单ID
  trainNumber?: string;      // 车次
  seatType?: string;         // 座位类型
  price?: number;            // 价格
  error?: string;            // 错误信息
}

/**
 * 任务接口
 */
export interface ITask {
  id: number;
  name: string;
  status: TaskStatus;
  config: ITaskConfig;
  schedule: ITaskSchedule;
  checkpoint?: ITaskCheckpoint;
  result?: ITaskResult;
  createdAt: string;
  updatedAt: string;
  startedAt?: string;
  completedAt?: string;
}

/**
 * 乘客信息接口
 */
export interface IPassenger {
  name: string;              // 姓名
  idType: string;            // 证件类型
  idNumber: string;          // 证件号码
  phone?: string;            // 手机号
}

/**
 * 账号接口
 */
export interface IAccount {
  id: number;
  username: string;
  password: string;          // 加密存储
  passengers?: IPassenger[];
  isActive: boolean;
  lastUsedAt?: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * 通知接口
 */
export interface INotification {
  id: number;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  content: string;
  channel: 'desktop' | 'email' | 'sms';
  status: NotificationStatus;
  taskId?: number;
  sentAt?: string;
  createdAt: string;
}

/**
 * 日志接口
 */
export interface ILog {
  id: number;
  level: LogLevel;
  message: string;
  source?: string;
  taskId?: number;
  details?: any;
  createdAt: string;
}

/**
 * 配置接口
 */
export interface IConfig {
  key: string;
  value: string;
  description?: string;
  updatedAt: string;
}

/**
 * 车次信息接口
 */
export interface ITrainInfo {
  trainNumber: string;       // 车次
  departureTime: string;     // 出发时间
  arrivalTime: string;       // 到达时间
  duration: string;          // 历时
  seatInfo: ISeatInfo[];     // 座位信息
}

/**
 * 座位信息接口
 */
export interface ISeatInfo {
  type: string;              // 座位类型
  price: number;             // 价格
  available: number;         // 可用数量
  waitlist?: boolean;        // 是否可候补
}
