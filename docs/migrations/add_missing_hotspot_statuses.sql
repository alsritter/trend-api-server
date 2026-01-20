-- 添加缺失的热点状态值到数据库约束
-- 修复问题: outdated 和 second_stage_rejected 状态在代码中定义但数据库约束中缺失

-- 删除旧的 CHECK 约束
ALTER TABLE hotspots DROP CONSTRAINT IF EXISTS hotspots_status_check;

-- 添加新的 CHECK 约束，包含所有状态值
ALTER TABLE hotspots ADD CONSTRAINT hotspots_status_check CHECK (status IN (
    'pending_validation',      -- 等待持续性验证（首次出现）
    'validated',               -- 已验证有持续性（6小时内二次出现）
    'rejected',                -- 已过滤（无商业价值，第一阶段被拒绝）
    'second_stage_rejected',   -- 第二阶段被拒绝（深度分析后）
    'crawling',                -- 爬虫进行中
    'crawled',                 -- 爬取完成，等待分析
    'analyzing',               -- 商业分析中
    'analyzed',                -- 分析完成
    'archived',                -- 已归档
    'outdated'                 -- 已过时（超过指定天数未更新）
));

-- 添加注释说明状态含义
COMMENT ON CONSTRAINT hotspots_status_check ON hotspots IS '热点状态约束: pending_validation, validated, rejected, second_stage_rejected, crawling, crawled, analyzing, analyzed, archived, outdated';
