-- 数据库迁移脚本：添加 AI 分析字段和 word_cover 字段
-- 日期：2026-01-21
-- 描述：为 hotspots 表添加 AI 分析相关字段以及 word_cover（词封面信息）

-- PostgreSQL 迁移脚本

-- 1. 添加 AI 分析字段
ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS confidence DECIMAL(5, 4);

ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS opportunities TEXT[] DEFAULT '{}';

ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS reasoning_keep TEXT[] DEFAULT '{}';

ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS reasoning_risk TEXT[] DEFAULT '{}';

ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS platform_url TEXT;

ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS primary_category VARCHAR(100);

-- 2. 添加 word_cover 字段（封面信息）
ALTER TABLE hotspots 
ADD COLUMN IF NOT EXISTS word_cover JSONB;

-- 3. 添加字段注释
COMMENT ON COLUMN hotspots.tags IS 'AI 分析的标签列表';
COMMENT ON COLUMN hotspots.confidence IS 'AI 分析置信度（0-1）';
COMMENT ON COLUMN hotspots.opportunities IS 'AI 识别的商业机会列表';
COMMENT ON COLUMN hotspots.reasoning_keep IS 'AI 保留该热词的理由';
COMMENT ON COLUMN hotspots.reasoning_risk IS 'AI 识别的风险列表';
COMMENT ON COLUMN hotspots.platform_url IS '平台原始URL链接';
COMMENT ON COLUMN hotspots.primary_category IS 'AI 分类的主要类别';
COMMENT ON COLUMN hotspots.word_cover IS '词封面信息（包含 uri 和 url_list）';

-- 4. 创建索引以提升查询性能（可选）
CREATE INDEX IF NOT EXISTS idx_hotspots_primary_category 
ON hotspots(primary_category) 
WHERE primary_category IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_hotspots_confidence 
ON hotspots(confidence) 
WHERE confidence IS NOT NULL;

-- 验证迁移
-- 查看表结构
-- \d hotspots

-- 示例：查询所有带标签的热点
-- SELECT id, keyword, tags, confidence, primary_category, word_cover 
-- FROM hotspots 
-- WHERE tags IS NOT NULL AND array_length(tags, 1) > 0
-- ORDER BY confidence DESC;
