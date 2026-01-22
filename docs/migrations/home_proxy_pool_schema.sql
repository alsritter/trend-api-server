-- 家宽代理池系统数据库表结构
-- 创建时间：2026-01-22

-- 1. 代理节点表（agents）
DROP TABLE IF EXISTS proxy_agents;
CREATE TABLE proxy_agents
(
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    agent_id        VARCHAR(64)  NOT NULL UNIQUE COMMENT 'Agent 唯一标识 (UUID)',
    agent_name      VARCHAR(128) NOT NULL COMMENT 'Agent 名称/主机名',
    auth_token      VARCHAR(256) NOT NULL COMMENT '认证 Token',
    public_ip       VARCHAR(45)  NULL COMMENT '公网 IP 地址',
    city            VARCHAR(64)  NULL COMMENT '城市',
    isp             VARCHAR(64)  NULL COMMENT '运营商',

    -- 代理配置
    proxy_type      VARCHAR(32)  NOT NULL DEFAULT 'socks5' COMMENT '代理类型：http, socks5, both',
    proxy_port      INT UNSIGNED NOT NULL DEFAULT 1080 COMMENT '代理端口',
    proxy_username  VARCHAR(64)  NULL COMMENT '代理认证用户名',
    proxy_password  VARCHAR(128) NULL COMMENT '代理认证密码',

    -- 状态信息
    status          VARCHAR(32)  NOT NULL DEFAULT 'offline' COMMENT '状态：online, offline, disabled',
    latency         INT UNSIGNED NULL COMMENT '延迟(ms)',
    last_heartbeat  DATETIME     NULL COMMENT '最后心跳时间',

    -- 统计信息
    total_requests  BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总请求数',
    failed_requests BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '失败请求数',

    -- 元数据
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_agent_id (agent_id),
    INDEX idx_status (status),
    INDEX idx_last_heartbeat (last_heartbeat)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='家宽代理 Agent 节点表';

-- 2. 代理节点健康日志表（proxy_health_log）
DROP TABLE IF EXISTS proxy_health_log;
CREATE TABLE proxy_health_log
(
    id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    agent_id       VARCHAR(64)   NOT NULL COMMENT 'Agent ID',
    check_time     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    is_available   TINYINT(1)    NOT NULL COMMENT '是否可用：1-可用，0-不可用',
    latency        INT UNSIGNED  NULL COMMENT '延迟(ms)',
    error_message  TEXT          NULL COMMENT '错误信息',
    check_type     VARCHAR(32)   NOT NULL DEFAULT 'auto' COMMENT '检测类型：auto, manual',

    INDEX idx_agent_id (agent_id),
    INDEX idx_check_time (check_time)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='代理健康检查日志表';

-- 3. 代理使用记录表（proxy_usage_log）
DROP TABLE IF EXISTS proxy_usage_log;
CREATE TABLE proxy_usage_log
(
    id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    agent_id   VARCHAR(64)  NOT NULL COMMENT 'Agent ID',
    request_id VARCHAR(64)  NULL COMMENT '请求标识',
    platform   VARCHAR(32)  NULL COMMENT '平台：xhs, douyin, etc.',
    is_success TINYINT(1)   NOT NULL COMMENT '是否成功：1-成功，0-失败',
    error_msg  TEXT         NULL COMMENT '错误信息',
    used_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '使用时间',

    INDEX idx_agent_id (agent_id),
    INDEX idx_used_at (used_at),
    INDEX idx_platform (platform)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci COMMENT ='代理使用记录表';
