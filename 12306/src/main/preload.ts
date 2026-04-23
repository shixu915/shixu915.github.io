import { contextBridge, ipcRenderer } from 'electron';
import { IPCChannels, IPCEvents } from '../shared/constants/ipcChannels';

/**
 * 预加载脚本
 * 通过contextBridge暴露安全的API给渲染进程
 */
contextBridge.exposeInMainWorld('electronAPI', {
  // 任务相关API
  task: {
    create: (taskData: any) => ipcRenderer.invoke(IPCChannels.TASK_CREATE, taskData),
    update: (taskId: number, taskData: any) => ipcRenderer.invoke(IPCChannels.TASK_UPDATE, taskId, taskData),
    delete: (taskId: number) => ipcRenderer.invoke(IPCChannels.TASK_DELETE, taskId),
    get: (taskId: number) => ipcRenderer.invoke(IPCChannels.TASK_GET, taskId),
    list: () => ipcRenderer.invoke(IPCChannels.TASK_LIST),
    start: (taskId: number) => ipcRenderer.invoke(IPCChannels.TASK_START, taskId),
    pause: (taskId: number) => ipcRenderer.invoke(IPCChannels.TASK_PAUSE, taskId),
    resume: (taskId: number) => ipcRenderer.invoke(IPCChannels.TASK_RESUME, taskId),
    cancel: (taskId: number) => ipcRenderer.invoke(IPCChannels.TASK_CANCEL, taskId)
  },

  // 账号相关API
  account: {
    create: (accountData: any) => ipcRenderer.invoke(IPCChannels.ACCOUNT_CREATE, accountData),
    update: (accountId: number, accountData: any) => ipcRenderer.invoke(IPCChannels.ACCOUNT_UPDATE, accountId, accountData),
    delete: (accountId: number) => ipcRenderer.invoke(IPCChannels.ACCOUNT_DELETE, accountId),
    get: (accountId: number) => ipcRenderer.invoke(IPCChannels.ACCOUNT_GET, accountId),
    list: () => ipcRenderer.invoke(IPCChannels.ACCOUNT_LIST),
    verify: (accountId: number) => ipcRenderer.invoke(IPCChannels.ACCOUNT_VERIFY, accountId)
  },

  // 配置相关API
  config: {
    get: (key: string) => ipcRenderer.invoke(IPCChannels.CONFIG_GET, key),
    set: (key: string, value: any) => ipcRenderer.invoke(IPCChannels.CONFIG_SET, key, value),
    getAll: () => ipcRenderer.invoke(IPCChannels.CONFIG_GET_ALL)
  },

  // 日志相关API
  log: {
    query: (params: any) => ipcRenderer.invoke(IPCChannels.LOG_QUERY, params),
    clear: () => ipcRenderer.invoke(IPCChannels.LOG_CLEAR)
  },

  // 通知相关API
  notification: {
    create: (notificationData: any) => ipcRenderer.invoke(IPCChannels.NOTIFICATION_CREATE, notificationData),
    list: () => ipcRenderer.invoke(IPCChannels.NOTIFICATION_LIST),
    markRead: (notificationId: number) => ipcRenderer.invoke(IPCChannels.NOTIFICATION_MARK_READ, notificationId)
  },

  // 验证码相关API
  captcha: {
    show: (imageData: string) => ipcRenderer.invoke(IPCChannels.CAPTCHA_SHOW, imageData),
    submit: (code: string) => ipcRenderer.invoke(IPCChannels.CAPTCHA_SUBMIT, code),
    refresh: () => ipcRenderer.invoke(IPCChannels.CAPTCHA_REFRESH)
  },

  // 事件监听
  on: {
    taskStatusChanged: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.TASK_STATUS_CHANGED, callback);
    },
    taskProgressUpdated: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.TASK_PROGRESS_UPDATED, callback);
    },
    taskCompleted: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.TASK_COMPLETED, callback);
    },
    notificationNew: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.NOTIFICATION_NEW, callback);
    },
    logNew: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.LOG_NEW, callback);
    },
    captchaRequired: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.CAPTCHA_REQUIRED, callback);
    },
    systemError: (callback: (event: any, data: any) => void) => {
      ipcRenderer.on(IPCEvents.SYSTEM_ERROR, callback);
    }
  },

  // 移除事件监听
  off: {
    taskStatusChanged: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.TASK_STATUS_CHANGED, callback);
    },
    taskProgressUpdated: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.TASK_PROGRESS_UPDATED, callback);
    },
    taskCompleted: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.TASK_COMPLETED, callback);
    },
    notificationNew: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.NOTIFICATION_NEW, callback);
    },
    logNew: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.LOG_NEW, callback);
    },
    captchaRequired: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.CAPTCHA_REQUIRED, callback);
    },
    systemError: (callback: (event: any, data: any) => void) => {
      ipcRenderer.removeListener(IPCEvents.SYSTEM_ERROR, callback);
    }
  }
});
