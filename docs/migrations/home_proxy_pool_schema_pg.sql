-- 家宽代理池系统数据库表结构 (PostgreSQL)
-- 创建时间：2026-01-22

-- 1. 代理节点表（agents）
DROP TABLE IF EXISTS proxy_agents CASCADE;

CREATE TABLE proxy_agents (
    id              BIGSERIAL PRIMARY KEY,
    agent_id        VARCHAR(64)  NOT NULL UNIQUE,
    agent_name      VARCHAR(128) NOT NULL,
    auth_token      VARCHAR(256) NOT NULL,
    public_ip       VARCHAR(45)  NULL,
    city            VARCHAR(64)  NULL,
    isp             VARCHAR(64)  NULL,
    proxy_type      VARCHAR(32)  NOT NULL DEFAULT 'socks5',
    proxy_port      INTEGER      NOT NULL DEFAULT 1080,
    proxy_username  VARCHAR(64)  NULL,
    proxy_password  VARCHAR(128) NULL,
    status          VARCHAR(32)  NOT NULL DEFAULT 'offline',
    latency         INTEGER      NULL,
    last_heartbeat  TIMESTAMP    NULL,
    total_requests  BIGINT       NOT NULL DEFAULT 0,
    failed_requests BIGINT       NOT NULL DEFAULT 0,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_proxy_agents_agent_id ON proxy_agents(agent_id);
CREATE INDEX idx_proxy_agents_status ON proxy_agents(status);
CREATE INDEX idx_proxy_agents_last_heartbeat ON proxy_agents(last_heartbeat);

-- 创建触发器自动更新 updated_at
CREATE OR REPLACE FUNCTION update_proxy_agents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_proxy_agents_updated_at
    BEFORE UPDATE ON proxy_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_proxy_agents_updated_at();

COMMENT ON TABLE proxy_agents IS '家宽代理 Agent 节点表';
COMMENT ON COLUMN proxy_agents.id IS '主键ID';
COMMENT ON COLUMN proxy_agents.agent_id IS 'Agent 唯一标识 (UUID)';
COMMENT ON COLUMN proxy_agents.agent_name IS 'Agent 名称/主机名';
COMMENT ON COLUMN proxy_agents.auth_token IS '认证 Token';
COMMENT ON COLUMN proxy_agents.public_ip IS '公网 IP 地址';
COMMENT ON COLUMN proxy_agents.city IS '城市';
COMMENT ON COLUMN proxy_agents.isp IS '运营商';
COMMENT ON COLUMN proxy_agents.proxy_type IS '代理类型：http, socks5, both';
COMMENT ON COLUMN proxy_agents.proxy_port IS '代理端口';
COMMENT ON COLUMN proxy_agents.proxy_username IS '代理认证用户名';
COMMENT ON COLUMN proxy_agents.proxy_password IS '代理认证密码';
COMMENT ON COLUMN proxy_agents.status IS '状态：online, offline, disabled';
COMMENT ON COLUMN proxy_agents.latency IS '延迟(ms)';
COMMENT ON COLUMN proxy_agents.last_heartbeat IS '最后心跳时间';
COMMENT ON COLUMN proxy_agents.total_requests IS '总请求数';
COMMENT ON COLUMN proxy_agents.failed_requests IS '失败请求数';
COMMENT ON COLUMN proxy_agents.created_at IS '创建时间';
COMMENT ON COLUMN proxy_agents.updated_at IS '更新时间';

-- 2. 代理节点健康日志表（proxy_health_log）
DROP TABLE IF EXISTS proxy_health_log CASCADE;

CREATE TABLE proxy_health_log (
    id             BIGSERIAL PRIMARY KEY,
    agent_id       VARCHAR(64)  NOT NULL,
    check_time     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_available   BOOLEAN      NOT NULL,
    latency        INTEGER      NULL,
    error_message  TEXT         NULL,
    check_type     VARCHAR(32)  NOT NULL DEFAULT 'auto'
);

-- 创建索引
CREATE INDEX idx_proxy_health_log_agent_id ON proxy_health_log(agent_id);
CREATE INDEX idx_proxy_health_log_check_time ON proxy_health_log(check_time);

COMMENT ON TABLE proxy_health_log IS '代理健康检查日志表';
COMMENT ON COLUMN proxy_health_log.id IS '主键ID';
COMMENT ON COLUMN proxy_health_log.agent_id IS 'Agent ID';
COMMENT ON COLUMN proxy_health_log.check_time IS '检测时间';
COMMENT ON COLUMN proxy_health_log.is_available IS '是否可用';
COMMENT ON COLUMN proxy_health_log.latency IS '延迟(ms)';
COMMENT ON COLUMN proxy_health_log.error_message IS '错误信息';
COMMENT ON COLUMN proxy_health_log.check_type IS '检测类型：auto, manual';

-- 3. 代理使用记录表（proxy_usage_log）
DROP TABLE IF EXISTS proxy_usage_log CASCADE;

CREATE TABLE proxy_usage_log (
    id         BIGSERIAL PRIMARY KEY,
    agent_id   VARCHAR(64)  NOT NULL,
    request_id VARCHAR(64)  NULL,
    platform   VARCHAR(32)  NULL,
    is_success BOOLEAN      NOT NULL,
    error_msg  TEXT         NULL,
    used_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_proxy_usage_log_agent_id ON proxy_usage_log(agent_id);
CREATE INDEX idx_proxy_usage_log_used_at ON proxy_usage_log(used_at);
CREATE INDEX idx_proxy_usage_log_platform ON proxy_usage_log(platform);

COMMENT ON TABLE proxy_usage_log IS '代理使用记录表';
COMMENT ON COLUMN proxy_usage_log.id IS '主键ID';
COMMENT ON COLUMN proxy_usage_log.agent_id IS 'Agent ID';
COMMENT ON COLUMN proxy_usage_log.request_id IS '请求标识';
COMMENT ON COLUMN proxy_usage_log.platform IS '平台：xhs, douyin, etc.';
COMMENT ON COLUMN proxy_usage_log.is_success IS '是否成功';
COMMENT ON COLUMN proxy_usage_log.error_msg IS '错误信息';
COMMENT ON COLUMN proxy_usage_log.used_at IS '使用时间';
