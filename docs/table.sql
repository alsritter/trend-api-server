-- =====================================================
-- 三阶段热点分析系统数据库设计 (PostgreSQL + pgvector)
-- =====================================================

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- 第一阶段：热点捕获与持续性验证
-- =====================================================

-- 1. 热点主表
CREATE TABLE hotspots (
    id BIGSERIAL PRIMARY KEY,

    -- 热词信息
    keyword VARCHAR(255) NOT NULL,                    -- 原始热词
    normalized_keyword VARCHAR(255) NOT NULL,         -- AI 归一化后的关键词

    -- 向量嵌入（用于语义相似度识别）
    embedding vector,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',

    -- 聚类信息（用于识别语义相似热词）
    cluster_id BIGINT,

    -- 时间追踪
    first_seen_at TIMESTAMP NOT NULL,                 -- 首次发现时间
    last_seen_at TIMESTAMP NOT NULL,                  -- 最后出现时间
    appearance_count INT DEFAULT 1,                   -- 出现次数

    -- 平台信息
    platforms JSONB NOT NULL,                         -- 出现的平台列表 [{"platform": "wechat", "rank": 1, "heat_score": 1000, "seen_at": "..."}]

    -- 状态流转
    status VARCHAR(50) DEFAULT 'pending_validation' CHECK (status IN (
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
    )),

    -- 爬取控制
    last_crawled_at TIMESTAMP,                        -- 上次爬取时间
    crawl_count INT DEFAULT 0,                        -- 爬取次数（每天最多4次）
    crawl_started_at TIMESTAMP,                       -- 当前爬取开始时间
    crawl_failed_count INT DEFAULT 0,                 -- 爬取失败次数

    -- 过滤信息（第一阶段 RAG 判断）
    is_filtered BOOLEAN DEFAULT FALSE,                -- 是否被过滤
    filter_reason TEXT,                               -- 过滤原因
    filtered_at TIMESTAMP,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    CONSTRAINT uk_hotspots_keyword UNIQUE (keyword)
);

-- 创建索引
CREATE INDEX idx_hotspots_normalized_keyword ON hotspots (normalized_keyword);
CREATE INDEX idx_hotspots_cluster_id ON hotspots (cluster_id);
CREATE INDEX idx_hotspots_status ON hotspots (status);
CREATE INDEX idx_hotspots_first_seen_at ON hotspots (first_seen_at);
CREATE INDEX idx_hotspots_last_seen_at ON hotspots (last_seen_at);
CREATE INDEX idx_hotspots_last_crawled_at ON hotspots (last_crawled_at);

-- 向量相似度索引
CREATE INDEX idx_hotspots_embedding ON hotspots
USING hnsw (embedding vector_ip_ops)
WITH (m = 16, ef_construction = 64);

COMMENT ON TABLE hotspots IS '热点主表-管理热词的完整生命周期';
COMMENT ON COLUMN hotspots.keyword IS '原始热词名称';
COMMENT ON COLUMN hotspots.normalized_keyword IS 'AI 归一化后的关键词（用于去重）';
COMMENT ON COLUMN hotspots.embedding IS '文本向量嵌入（用于语义相似度识别）';
COMMENT ON COLUMN hotspots.platforms IS '平台信息数组，包含平台名、排名、热度分数';

-- 2. 热词聚类表（相似热词分组）
CREATE TABLE hotspot_clusters (
    id BIGSERIAL PRIMARY KEY,
    cluster_name VARCHAR(255) NOT NULL,              -- 簇代表名称
    keywords JSONB,                                  -- 簇内所有关键词 ["iPhone 17", "苹果新机", ...]
    selected_hotspot_id BIGINT,                      -- 被选中用于验证的热词ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hotspot_clusters_name ON hotspot_clusters (cluster_name);

COMMENT ON TABLE hotspot_clusters IS '热词聚类表-管理语义相似的热词分组（如"iPhone 17"和"苹果新机"）';

-- 添加外键
ALTER TABLE hotspots
ADD CONSTRAINT fk_hotspots_cluster
FOREIGN KEY (cluster_id) REFERENCES hotspot_clusters(id) ON DELETE SET NULL;

-- =====================================================
-- 第三阶段：商业价值分析与推送
-- =====================================================

-- 5. 商业分析报告表
CREATE TABLE business_reports (
    id BIGSERIAL PRIMARY KEY,
    hotspot_id BIGINT NOT NULL,

    -- 分析报告内容
    report JSONB NOT NULL,                           -- 完整的商业分析报告
    /*
    报告结构示例:
    {
        "summary": "简短总结",
        "virtual_products": {
            "opportunities": ["机会1", "机会2"],
            "feasibility_score": 85
        },
        "physical_products": {
            "opportunities": ["机会1", "机会2"],
            "feasibility_score": 70
        },
        "target_audience": ["人群1", "人群2"],
        "market_size": "估算市场规模",
        "recommendations": ["建议1", "建议2"]
    }
    */

    -- 评分和优先级
    score DECIMAL(5, 2) NOT NULL,                    -- 可行性分数 (0-100)
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),

    -- 商品类型分类
    product_types JSONB,                             -- ["virtual", "physical"]

    -- 时间信息
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_business_reports_hotspot FOREIGN KEY (hotspot_id) REFERENCES hotspots (id) ON DELETE CASCADE
);

CREATE INDEX idx_business_reports_hotspot_id ON business_reports (hotspot_id);
CREATE INDEX idx_business_reports_score ON business_reports (score);
CREATE INDEX idx_business_reports_priority ON business_reports (priority);

COMMENT ON TABLE business_reports IS '商业分析报告表-存储 AI 生成的商业价值分析结果';
COMMENT ON COLUMN business_reports.score IS '可行性分数，用于排序推送优先级';

-- 6. 推送队列表
CREATE TABLE push_queue (
    id BIGSERIAL PRIMARY KEY,
    hotspot_id BIGINT NOT NULL,
    report_id BIGINT NOT NULL,                       -- 关联的分析报告

    -- 推送信息
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('high', 'medium', 'low')),
    score DECIMAL(5, 2) NOT NULL,                    -- 冗余字段，方便排序

    -- 推送状态
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending',       -- 待推送
        'sent',          -- 已发送
        'failed'         -- 发送失败
    )),

    -- 推送渠道
    channels JSONB,                                  -- 推送渠道 ["email", "wechat", "webhook"]

    -- 时间控制
    scheduled_at TIMESTAMP,                          -- 计划推送时间（用于控制推送间隔）
    sent_at TIMESTAMP,                               -- 实际发送时间

    -- 失败处理
    retry_count INT DEFAULT 0,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_push_queue_hotspot FOREIGN KEY (hotspot_id) REFERENCES hotspots (id) ON DELETE CASCADE,
    CONSTRAINT fk_push_queue_report FOREIGN KEY (report_id) REFERENCES business_reports (id) ON DELETE CASCADE
);

CREATE INDEX idx_push_queue_hotspot_id ON push_queue (hotspot_id);
CREATE INDEX idx_push_queue_status ON push_queue (status);
CREATE INDEX idx_push_queue_priority_score ON push_queue (priority, score DESC);
CREATE INDEX idx_push_queue_scheduled_at ON push_queue (scheduled_at);

COMMENT ON TABLE push_queue IS '推送队列表-管理商业分析报告的推送调度';
COMMENT ON COLUMN push_queue.scheduled_at IS '计划推送时间，用于控制推送间隔（每次间隔≥2小时）';

-- =====================================================
-- 触发器：自动更新时间戳
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_hotspots_updated_at BEFORE UPDATE ON hotspots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hotspot_clusters_updated_at BEFORE UPDATE ON hotspot_clusters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_push_queue_updated_at BEFORE UPDATE ON push_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 常用查询示例
-- =====================================================

/*
--------------------------------------------------
第一阶段查询：热点捕获与持续性验证
--------------------------------------------------

-- 1. 查找新热词是否存在语义相似的已有热词
WITH query_embedding AS (
    SELECT embedding FROM hotspots WHERE keyword = '新热词名称'
)
SELECT
    h.id,
    h.keyword,
    h.normalized_keyword,
    h.status,
    h.appearance_count,
    (h.embedding <#> qe.embedding) * -1 as similarity
FROM hotspots h, query_embedding qe
WHERE h.embedding <#> qe.embedding < -0.85  -- 相似度阈值 > 0.85
ORDER BY similarity DESC
LIMIT 5;

-- 2. 查找需要验证持续性的热点（6小时内二次出现）
SELECT *
FROM hotspots
WHERE status = 'pending_validation'
    AND last_seen_at >= NOW() - INTERVAL '6 hours'
    AND appearance_count >= 2;

--------------------------------------------------
第二阶段查询：深度数据采集
--------------------------------------------------

-- 4. 查找需要爬取的热点（状态为 validated 且未爬取或距上次爬取 > 6小时）
SELECT *
FROM hotspots
WHERE status = 'validated'
    AND (
        last_crawled_at IS NULL
        OR last_crawled_at < NOW() - INTERVAL '6 hours'
    )
    AND crawl_count < 4  -- 每天最多4次（需要额外的日期判断）
ORDER BY last_seen_at DESC
LIMIT 10;

-- 5. 查找超时的爬虫任务（>30分钟仍未完成）
SELECT *
FROM crawl_tasks
WHERE status = 'running'
    AND started_at < NOW() - INTERVAL '30 minutes';

-- 6. 统计某个热点的爬取数据量
SELECT
    h.keyword,
    h.status,
    COUNT(n.id) as note_count,
    SUM((n.metrics->>'likes')::INT) as total_likes
FROM hotspots h
LEFT JOIN notes n ON h.id = n.hotspot_id
WHERE h.id = 1
GROUP BY h.id, h.keyword, h.status;

--------------------------------------------------
第三阶段查询：商业价值分析与推送
--------------------------------------------------

-- 7. 查找待分析的热点（状态为 crawled）
SELECT
    h.*,
    COUNT(n.id) as note_count
FROM hotspots h
LEFT JOIN notes n ON h.id = n.hotspot_id
WHERE h.status = 'crawled'
GROUP BY h.id
HAVING COUNT(n.id) > 0  -- 确保有爬取数据
ORDER BY h.last_seen_at DESC
LIMIT 5;

-- 8. 获取下一个待推送的报告（优先级最高 + 分数最高 + 间隔≥2小时）
WITH last_push AS (
    SELECT MAX(sent_at) as last_sent_at
    FROM push_queue
    WHERE status = 'sent'
)
SELECT
    pq.*,
    br.report,
    h.keyword
FROM push_queue pq
JOIN business_reports br ON pq.report_id = br.id
JOIN hotspots h ON pq.hotspot_id = h.id
CROSS JOIN last_push lp
WHERE pq.status = 'pending'
    AND (lp.last_sent_at IS NULL OR lp.last_sent_at < NOW() - INTERVAL '2 hours')
ORDER BY
    CASE pq.priority
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
    END,
    pq.score DESC
LIMIT 1;

-- 9. 查看推送历史和效果
SELECT
    h.keyword,
    br.score,
    pq.priority,
    pq.sent_at,
    pq.channels
FROM push_queue pq
JOIN hotspots h ON pq.hotspot_id = h.id
JOIN business_reports br ON pq.report_id = br.id
WHERE pq.status = 'sent'
ORDER BY pq.sent_at DESC
LIMIT 20;

--------------------------------------------------
综合查询：全流程追踪
--------------------------------------------------

-- 10. 热点完整生命周期追踪
SELECT
    h.keyword,
    h.status,
    h.first_seen_at,
    h.last_seen_at,
    h.appearance_count,
    h.platforms,
    COUNT(DISTINCT n.id) as note_count,
    br.score as business_score,
    br.priority,
    pq.status as push_status,
    pq.sent_at
FROM hotspots h
LEFT JOIN notes n ON h.id = n.hotspot_id
LEFT JOIN business_reports br ON h.id = br.hotspot_id
LEFT JOIN push_queue pq ON h.id = pq.hotspot_id
WHERE h.keyword = '目标热词'
GROUP BY h.id, br.id, pq.id;

*/

-- =====================================================
-- 应用层实现参考
-- =====================================================

/*
--------------------------------------------------
三阶段工作流调度建议（使用定时任务）
--------------------------------------------------

1. 第一阶段任务（每 30 分钟执行）
   - 拉取多平台热榜数据
   - 生成 embedding 向量
   - 检查是否存在相似热词（向量搜索）
   - 更新 appearance_count 和 last_seen_at
   - 检查持续性验证条件（6小时内二次出现 → status = 'validated'）

2. 第二阶段任务（每 10 分钟执行）
   - 查询 status = 'validated' 且满足爬取条件的热点
   - 调用爬虫 API，传入热词和平台列表
   - 更新状态为 'crawling'，记录 crawl_started_at
   - 监控超时任务（可选，独立任务）

3. 爬虫回调接口
   - 接收爬虫完成通知
   - 批量插入 notes 表
   - 更新 hotspots.status = 'crawled'
   - 更新 hotspots.last_crawled_at

4. 第三阶段任务（每 30 分钟执行）
   - 查询 status = 'crawled' 的热点及其笔记数据
   - 调用 Coze Agent 进行商业分析
   - 写入 business_reports 表
   - 写入 push_queue 表，设置 scheduled_at
   - 更新 hotspots.status = 'analyzed'

5. 推送任务（每 10 分钟执行）
   - 查询 push_queue 中 status = 'pending'
   - 检查推送间隔（≥2小时）
   - 按优先级和分数排序，取第一条
   - 执行推送，更新 status = 'sent', sent_at = NOW()

--------------------------------------------------
Python 伪代码示例（使用 asyncpg + OpenAI）
--------------------------------------------------

import asyncpg
from openai import AsyncOpenAI

# 第一阶段：检查热词是否存在相似项
async def check_similar_hotspot(keyword: str, embedding: list[float]):
    conn = await asyncpg.connect('postgresql://...')

    # 向量相似度搜索
    similar = await conn.fetchrow('''
        SELECT id, keyword, cluster_id,
               (embedding <#> $1) * -1 as similarity
        FROM hotspots
        WHERE embedding <#> $1 < -0.85
        ORDER BY similarity DESC
        LIMIT 1
    ''', embedding)

    await conn.close()
    return similar

# 第二阶段：触发爬虫任务
async def trigger_crawl_task(hotspot_id: int, platforms: list[str]):
    # 调用爬虫 API
    response = await crawler_api.crawl(
        hotspot_id=hotspot_id,
        platforms=platforms,
        callback_url='https://your-domain.com/api/crawl-callback'
    )

    # 更新数据库
    conn = await asyncpg.connect('postgresql://...')
    await conn.execute('''
        UPDATE hotspots
        SET status = 'crawling',
            crawl_started_at = NOW(),
            crawl_count = crawl_count + 1
        WHERE id = $1
    ''', hotspot_id)
    await conn.close()

# 第三阶段：商业分析
async def analyze_business_value(hotspot_id: int):
    conn = await asyncpg.connect('postgresql://...')

    # 获取热点和笔记数据
    data = await conn.fetch('''
        SELECT h.keyword, n.content, n.comments, n.metrics
        FROM hotspots h
        JOIN notes n ON h.id = n.hotspot_id
        WHERE h.id = $1
    ''', hotspot_id)

    # 调用 Coze Agent 分析
    report = await coze_agent.analyze(data)

    # 写入数据库
    report_id = await conn.fetchval('''
        INSERT INTO business_reports (hotspot_id, report, score, priority)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    ''', hotspot_id, report, report['score'], report['priority'])

    # 加入推送队列
    await conn.execute('''
        INSERT INTO push_queue (hotspot_id, report_id, priority, score, scheduled_at)
        VALUES ($1, $2, $3, $4, NOW())
    ''', hotspot_id, report_id, report['priority'], report['score'])

    await conn.close()

*/
