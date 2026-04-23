-- 12306智能抢票助手数据库初始化脚本
-- 版本: 1.0.0
-- 创建日期: 2026-04-23

-- 创建版本表
CREATE TABLE IF NOT EXISTS db_version (
    version INTEGER PRIMARY KEY,
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    config TEXT NOT NULL,
    schedule TEXT NOT NULL,
    checkpoint TEXT,
    result TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    started_at TEXT,
    completed_at TEXT
);

-- 创建账号表
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    passengers TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_used_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 创建通知表
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    task_id INTEGER,
    sent_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- 创建日志表
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    source TEXT,
    task_id INTEGER,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- 创建配置表
CREATE TABLE IF NOT EXISTS configs (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_accounts_username ON accounts(username);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at);
CREATE INDEX IF NOT EXISTS idx_logs_task_id ON logs(task_id);

-- 插入默认配置
INSERT OR IGNORE INTO configs (key, value, description) VALUES
    ('notification.enabled', 'true', '是否启用通知'),
    ('notification.channels', '["desktop"]', '通知渠道列表'),
    ('notification.email.host', '', '邮件服务器地址'),
    ('notification.email.port', '587', '邮件服务器端口'),
    ('notification.email.user', '', '邮件用户名'),
    ('notification.email.password', '', '邮件密码'),
    ('ticket.retry_times', '3', '抢票重试次数'),
    ('ticket.retry_delay_min', '1000', '重试最小延迟(毫秒)'),
    ('ticket.retry_delay_max', '3000', '重试最大延迟(毫秒)'),
    ('ticket.enable_waitlist', 'true', '是否启用候补功能'),
    ('ticket.query_interval', '500', '查询间隔(毫秒)'),
    ('captcha.enable_ocr', 'false', '是否启用OCR识别'),
    ('captcha.timeout', '120', '验证码超时时间(秒)'),
    ('system.max_concurrent_tasks', '5', '最大并发任务数'),
    ('system.log_level', 'info', '日志级别'),
    ('system.log_retention_days', '30', '日志保留天数');

-- 插入数据库版本
INSERT OR REPLACE INTO db_version (version) VALUES (1);
