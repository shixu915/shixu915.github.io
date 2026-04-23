/**
 * IPC通道名称常量
 * 用于主进程和渲染进程之间的通信
 */
export enum IPCChannels {
  // 任务相关
  TASK_CREATE = 'task:create',
  TASK_UPDATE = 'task:update',
  TASK_DELETE = 'task:delete',
  TASK_GET = 'task:get',
  TASK_LIST = 'task:list',
  TASK_START = 'task:start',
  TASK_PAUSE = 'task:pause',
  TASK_RESUME = 'task:resume',
  TASK_CANCEL = 'task:cancel',
  
  // 账号相关
  ACCOUNT_CREATE = 'account:create',
  ACCOUNT_UPDATE = 'account:update',
  ACCOUNT_DELETE = 'account:delete',
  ACCOUNT_GET = 'account:get',
  ACCOUNT_LIST = 'account:list',
  ACCOUNT_VERIFY = 'account:verify',
  
  // 通知相关
  NOTIFICATION_CREATE = 'notification:create',
  NOTIFICATION_LIST = 'notification:list',
  NOTIFICATION_MARK_READ = 'notification:mark-read',
  
  // 日志相关
  LOG_QUERY = 'log:query',
  LOG_CLEAR = 'log:clear',
  
  // 配置相关
  CONFIG_GET = 'config:get',
  CONFIG_SET = 'config:set',
  CONFIG_GET_ALL = 'config:get-all',
  
  // 验证码相关
  CAPTCHA_SHOW = 'captcha:show',
  CAPTCHA_SUBMIT = 'captcha:submit',
  CAPTCHA_REFRESH = 'captcha:refresh',
  
  // 系统相关
  SYSTEM_STATUS = 'system:status',
  SYSTEM_SHUTDOWN = 'system:shutdown'
}

/**
 * IPC事件名称常量
 * 用于主进程向渲染进程推送事件
 */
export enum IPCEvents {
  // 任务事件
  TASK_STATUS_CHANGED = 'event:task-status-changed',
  TASK_PROGRESS_UPDATED = 'event:task-progress-updated',
  TASK_COMPLETED = 'event:task-completed',
  
  // 通知事件
  NOTIFICATION_NEW = 'event:notification-new',
  
  // 日志事件
  LOG_NEW = 'event:log-new',
  
  // 验证码事件
  CAPTCHA_REQUIRED = 'event:captcha-required',
  
  // 系统事件
  SYSTEM_ERROR = 'event:system-error'
}
