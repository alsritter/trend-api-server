-- 数据库迁移脚本：添加第二阶段拒绝字段
-- 日期：2026-01-11
-- 描述：为 hotspots 表添加 second_stage_rejection_reason 和 second_stage_rejected_at 字段

-- PostgreSQL 迁移脚本

-- 1. 添加第二阶段拒绝原因字段
ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS second_stage_rejection_reason TEXT;

-- 2. 添加第二阶段拒绝时间字段
ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS second_stage_rejected_at TIMESTAMP;

-- 3. 添加字段注释
COMMENT ON COLUMN hotspots.second_stage_rejection_reason IS '第二阶段拒绝原因（深度分析后）';
COMMENT ON COLUMN hotspots.second_stage_rejected_at IS '第二阶段拒绝时间';

-- 4. 创建索引以提升查询性能（可选）
CREATE INDEX IF NOT EXISTS idx_hotspots_second_stage_rejected_at 
ON hotspots(second_stage_rejected_at) 
WHERE second_stage_rejected_at IS NOT NULL;

-- 验证迁移
-- 查看表结构
\d hotspots

-- 示例：查询所有第二阶段被拒绝的热点
-- SELECT id, keyword, status, second_stage_rejection_reason, second_stage_rejected_at 
-- FROM hotspots 
-- WHERE status = 'second_stage_rejected'
-- ORDER BY second_stage_rejected_at DESC;
