-- Doggy 数据库初始化脚本
-- 在 PostgreSQL 首次启动时自动执行

-- API Keys 表
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGSERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    app_id VARCHAR(64) NOT NULL,
    app_name VARCHAR(128) NOT NULL,
    app_owner VARCHAR(128),
    policy_name VARCHAR(128) NOT NULL DEFAULT 'default',
    rate_limit_qps INT DEFAULT 50,
    allowed_models TEXT[] DEFAULT '{*}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- 审计日志表（按月分区）
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL,
    app_id VARCHAR(64) NOT NULL,
    request_id VARCHAR(32) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    direction VARCHAR(16) NOT NULL,
    rail_type VARCHAR(32) NOT NULL,
    result VARCHAR(16) NOT NULL,
    model_name VARCHAR(64),
    duration_ms INTEGER,
    request_summary TEXT,
    response_summary TEXT,
    metadata JSONB DEFAULT '{}',
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- 创建当月分区
CREATE TABLE IF NOT EXISTS audit_logs_2026_07 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

-- 索引
CREATE INDEX IF NOT EXISTS idx_audit_app_time ON audit_logs (app_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_result ON audit_logs (result) WHERE result = 'BLOCKED';

-- 安全策略表
CREATE TABLE IF NOT EXISTS policies (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    version INT NOT NULL DEFAULT 1,
    config_yaml TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(128),
    role VARCHAR(32) NOT NULL DEFAULT 'app_developer',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认测试数据
INSERT INTO api_keys (key_hash, app_id, app_name, policy_name)
VALUES ('test-key-hash-do-not-use-in-production', 'test-app', '测试应用', 'default')
ON CONFLICT (key_hash) DO NOTHING;