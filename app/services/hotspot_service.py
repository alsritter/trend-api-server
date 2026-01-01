from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.db import vector_session
from app.services.vector_service import vector_service
from app.schemas.hotspot import (
    KeywordAnalysis,
    SimilarHotspot,
    HotspotStatus,
    Priority,
    PushStatus,
    HotspotDetail,
    PlatformInfo,
    BusinessReportContent,
    PushQueueItem,
    ClusterInfo,
)
import json


class HotspotService:
    """热点服务类 - 提供热点管理的完整业务逻辑"""

    # 相似度阈值配置
    EXACT_MATCH_THRESHOLD = 0.95  # 完全一致阈值
    HIGH_SIMILARITY_THRESHOLD = 0.85  # 高相似度阈值
    SIMILAR_THRESHOLD = 0.75  # 相似阈值

    def __init__(self):
        """初始化热点服务"""
        pass

    def _parse_viewnum(self, viewnum_str: str) -> int:
        """
        解析热度值（将 "541.2万" 这样的字符串转换为数字）

        Args:
            viewnum_str: 热度字符串，如 "541.2万"、"1.5亿"

        Returns:
            热度数值
        """
        if not viewnum_str or viewnum_str == "0":
            return 0

        # 去除空格
        viewnum_str = viewnum_str.strip()

        # 处理万、亿等单位
        multiplier = 1
        if "亿" in viewnum_str:
            multiplier = 100000000
            viewnum_str = viewnum_str.replace("亿", "")
        elif "万" in viewnum_str:
            multiplier = 10000
            viewnum_str = viewnum_str.replace("万", "")

        # 转换为浮点数并乘以倍数
        try:
            return int(float(viewnum_str) * multiplier)
        except ValueError:
            return 0

    async def add_keyword_from_analysis(
        self, analysis: KeywordAnalysis, platform_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        根据AI分析结果添加热词

        Args:
            analysis: AI返回的热词分析结果
            platform_data: 平台原始数据(包含 type, rank, viewnum 等)

        Returns:
            包含 hotspot_id, action, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            # 检查是否已存在（无论是低价值词还是有价值词都添加到热点表）
            existing_hotspot = await conn.fetchrow(
                "SELECT id, status, last_seen_at FROM hotspots WHERE keyword = $1",
                analysis.title,
            )

            if existing_hotspot:
                # 更新现有热点
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET last_seen_at = CURRENT_TIMESTAMP,
                        appearance_count = appearance_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    existing_hotspot["id"],
                )

                return {
                    "hotspot_id": existing_hotspot["id"],
                    "action": "updated",
                    "message": f"热点 '{analysis.title}' 已更新出现次数",
                }

            # 创建新热点
            # 生成向量
            embedding = await vector_service.generate_embedding(analysis.title)

            # 检查是否存在高相似度的热词(>=85%)，如果存在则关联到同一个cluster
            # 如果不存在相似的热词，则为该热词创建一个新的独立cluster
            cluster_id = None
            seven_days_ago = datetime.now() - timedelta(days=7)

            similar_records = await conn.fetch(
                """
                SELECT
                    id, keyword, cluster_id,
                    (embedding <#> $1) * -1 as similarity
                FROM hotspots
                WHERE last_seen_at >= $2
                    AND embedding IS NOT NULL
                    AND (embedding <#> $1) < $3
                ORDER BY similarity DESC
                LIMIT 1
                """,
                embedding,
                seven_days_ago,
                -self.HIGH_SIMILARITY_THRESHOLD,  # >= 85%
            )

            if similar_records:
                similar_record = similar_records[0]
                similarity = similar_record["similarity"]

                # 如果相似度 >= 85%，关联到同一个cluster
                if similarity >= self.HIGH_SIMILARITY_THRESHOLD:
                    existing_cluster_id = similar_record["cluster_id"]

                    if existing_cluster_id:
                        # 使用已存在的cluster
                        cluster_id = existing_cluster_id
                        # 更新cluster的成员列表
                        await conn.execute(
                            """
                            UPDATE hotspot_clusters
                            SET member_count = member_count + 1,
                                keywords = keywords || $1::jsonb,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                            """,
                            json.dumps([analysis.title]),
                            cluster_id,
                        )
                    else:
                        # 创建新的cluster，并将两个热词都加入
                        cluster_id = await conn.fetchval(
                            """
                            INSERT INTO hotspot_clusters (cluster_name, member_count, keywords)
                            VALUES ($1, 2, $2)
                            RETURNING id
                            """,
                            similar_record["keyword"],  # 使用第一个热词作为cluster名称
                            json.dumps([similar_record["keyword"], analysis.title]),
                        )

                        # 更新已存在的相似热词的cluster_id
                        await conn.execute(
                            """
                            UPDATE hotspots
                            SET cluster_id = $1,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                            """,
                            cluster_id,
                            similar_record["id"],
                        )

            # 如果没有找到相似的热词，创建一个新的独立cluster
            if cluster_id is None:
                cluster_id = await conn.fetchval(
                    """
                    INSERT INTO hotspot_clusters (cluster_name, member_count, keywords)
                    VALUES ($1, 1, $2)
                    RETURNING id
                    """,
                    analysis.title,  # 使用热词本身作为cluster名称
                    json.dumps([analysis.title]),
                )

            # 平台名称映射
            platform_name_map = {
                "xhs": "小红书",
                "dy": "抖音",
                "bili": "哔哩哔哩",
                "ks": "快手",
                "wb": "微博",
                "tieba": "贴吧",
                "zhihu": "知乎",
            }

            # 构建平台信息（从传入的平台数据中提取）
            if platform_data:
                platform_type = platform_data.get("type", "unknown")
                platform_name = platform_name_map.get(platform_type, platform_type)

                # 解析热度值（去除万、亿等单位）
                viewnum_str = platform_data.get("viewnum", "0")
                heat_score = self._parse_viewnum(viewnum_str)

                # 安全地转换 rank,处理空字符串的情况
                rank_value = platform_data.get("rank", 0)
                rank = int(rank_value) if rank_value and str(rank_value).strip() else 0

                platforms = [
                    {
                        "platform": platform_name,
                        "rank": rank,
                        "heat_score": heat_score,
                        "seen_at": platform_data.get(
                            "date", datetime.now().isoformat()
                        ),
                    }
                ]
            else:
                # 如果没有平台数据，使用默认值
                platforms = [
                    {
                        "platform": "unknown",
                        "rank": 0,
                        "heat_score": int(analysis.confidence * 100),
                        "seen_at": datetime.now().isoformat(),
                    }
                ]

            # 根据是否低价值词决定状态和过滤信息
            if analysis.is_remove:
                # 低价值词：状态设为 rejected，记录拒绝原因
                status = HotspotStatus.REJECTED.value
                is_filtered = True
                filter_reason = "; ".join(analysis.reasoning.risk)
                filtered_at = datetime.now()
            else:
                # 有价值词：状态设为 pending_validation
                status = HotspotStatus.PENDING_VALIDATION.value
                is_filtered = False
                filter_reason = None
                filtered_at = None

            now = datetime.now()
            hotspot_id = await conn.fetchval(
                """
                INSERT INTO hotspots (
                    keyword, normalized_keyword, embedding, embedding_model,
                    cluster_id, first_seen_at, last_seen_at, appearance_count, platforms,
                    status, is_filtered, filter_reason, filtered_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING id
                """,
                analysis.title,
                analysis.title.lower().strip(),
                embedding,
                vector_service.EMBEDDING_MODEL,
                cluster_id,  # 添加cluster_id
                now,
                now,
                1,
                json.dumps(platforms),
                status,
                is_filtered,
                filter_reason,
                filtered_at,
            )

            action = "rejected" if analysis.is_remove else "created"
            status_text = "已拒绝" if analysis.is_remove else "创建成功"

            # 如果自动关联到了cluster，在消息中说明
            cluster_info = f"（已关联到簇 {cluster_id}）" if cluster_id else ""

            return {
                "hotspot_id": hotspot_id,
                "action": action,
                "message": f"热点 '{analysis.title}' {status_text} (ID: {hotspot_id}){cluster_info}",
            }

    async def check_hotspot_exists(self, keyword: str) -> Dict[str, Any]:
        """
        检查热词是否已存在（多维度判断）

        维度包括:
        1. 完全匹配
        2. 时间窗口内的相似匹配（最近7天）
        3. 向量相似度匹配

        Args:
            keyword: 热词名称

        Returns:
            包含 exists, action, hotspot_id, similar_hotspots, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            # 1. 检查完全匹配
            exact_match = await conn.fetchrow(
                """
                SELECT id, keyword, normalized_keyword, status,
                       first_seen_at, last_seen_at, appearance_count, cluster_id
                FROM hotspots
                WHERE keyword = $1 OR normalized_keyword = $2
                """,
                keyword,
                keyword.lower().strip(),
            )

            if exact_match:
                return {
                    "exists": True,
                    "action": "skip",
                    "hotspot_id": exact_match["id"],
                    "similar_hotspots": [],
                    "message": f"热词 '{keyword}' 已存在 (完全匹配)",
                }

            # 2. 生成向量进行相似度搜索
            embedding = await vector_service.generate_embedding(keyword)

            # 搜索相似热词（最近7天内）
            seven_days_ago = datetime.now() - timedelta(days=7)

            similar_records = await conn.fetch(
                """
                SELECT
                    id, keyword, normalized_keyword, status,
                    first_seen_at, last_seen_at, appearance_count, cluster_id,
                    (embedding <#> $1) * -1 as similarity
                FROM hotspots
                WHERE last_seen_at >= $2
                    AND embedding IS NOT NULL
                    AND (embedding <#> $1) < $3
                ORDER BY similarity DESC
                LIMIT 5
                """,
                embedding,
                seven_days_ago,
                -self.SIMILAR_THRESHOLD,  # 因为使用负内积，所以取负值
            )

            similar_hotspots = [
                SimilarHotspot(
                    id=r["id"],
                    keyword=r["keyword"],
                    normalized_keyword=r["normalized_keyword"],
                    status=HotspotStatus(r["status"]),
                    first_seen_at=r["first_seen_at"],
                    last_seen_at=r["last_seen_at"],
                    appearance_count=r["appearance_count"],
                    similarity=float(r["similarity"]),
                    cluster_id=r["cluster_id"],
                )
                for r in similar_records
            ]

            if not similar_hotspots:
                return {
                    "exists": False,
                    "action": "create",
                    "hotspot_id": None,
                    "similar_hotspots": [],
                    "message": f"热词 '{keyword}' 不存在，可以创建",
                }

            # 检查最高相似度
            max_similarity = similar_hotspots[0].similarity

            if max_similarity >= self.EXACT_MATCH_THRESHOLD:
                # 完全一致，更新时间
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET last_seen_at = CURRENT_TIMESTAMP,
                        appearance_count = appearance_count + 1
                    WHERE id = $1
                    """,
                    similar_hotspots[0].id,
                )

                return {
                    "exists": True,
                    "action": "update",
                    "hotspot_id": similar_hotspots[0].id,
                    "similar_hotspots": similar_hotspots[:1],
                    "message": f"发现完全一致的热词 (相似度 {max_similarity:.2%})，已更新",
                }

            elif max_similarity >= self.HIGH_SIMILARITY_THRESHOLD:
                # 高相似度，更新时间或状态
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET last_seen_at = CURRENT_TIMESTAMP,
                        appearance_count = appearance_count + 1
                    WHERE id = $1
                    """,
                    similar_hotspots[0].id,
                )

                return {
                    "exists": True,
                    "action": "update",
                    "hotspot_id": similar_hotspots[0].id,
                    "similar_hotspots": similar_hotspots[:1],
                    "message": f"发现高相似度热词 (相似度 {max_similarity:.2%})，已更新",
                }

            else:
                # 中等相似度，返回相似词组交给LLM判断
                return {
                    "exists": False,
                    "action": "ask_llm",
                    "hotspot_id": None,
                    "similar_hotspots": similar_hotspots,
                    "message": f"发现 {len(similar_hotspots)} 个相似热词，建议交给LLM判断",
                }

    async def add_business_report(
        self,
        hotspot_id: int,
        report: BusinessReportContent,
        score: float,
        priority: Priority,
        product_types: List[str],
    ) -> Dict[str, Any]:
        """
        添加商业报告

        Args:
            hotspot_id: 热点ID
            report: 报告内容
            score: 可行性分数
            priority: 优先级
            product_types: 商品类型

        Returns:
            包含 success, report_id, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 插入商业报告
                report_id = await conn.fetchval(
                    """
                    INSERT INTO business_reports (
                        hotspot_id, report, score, priority, product_types
                    )
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    hotspot_id,
                    report.model_dump_json(),
                    score,
                    priority.value,
                    json.dumps(product_types),
                )

                # 更新热点状态为 analyzed
                await conn.execute(
                    "UPDATE hotspots SET status = $1 WHERE id = $2",
                    HotspotStatus.ANALYZED.value,
                    hotspot_id,
                )

                return {
                    "success": True,
                    "report_id": report_id,
                    "message": f"商业报告创建成功 (ID: {report_id})",
                }

    async def add_to_push_queue(
        self, hotspot_id: int, report_id: int, channels: List[str]
    ) -> Dict[str, Any]:
        """
        添加到推送队列

        Args:
            hotspot_id: 热点ID
            report_id: 报告ID
            channels: 推送渠道

        Returns:
            包含 success, push_id, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            # 获取报告的优先级和分数
            report = await conn.fetchrow(
                "SELECT priority, score FROM business_reports WHERE id = $1", report_id
            )

            if not report:
                raise ValueError(f"报告 {report_id} 不存在")

            # 插入推送队列
            push_id = await conn.fetchval(
                """
                INSERT INTO push_queue (
                    hotspot_id, report_id, priority, score, channels, scheduled_at
                )
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                RETURNING id
                """,
                hotspot_id,
                report_id,
                report["priority"],
                report["score"],
                json.dumps(channels),
            )

            return {
                "success": True,
                "push_id": push_id,
                "message": f"已添加到推送队列 (ID: {push_id})",
            }

    async def get_pending_push_items(self, limit: int = 10) -> List[PushQueueItem]:
        """
        获取待推送的报告（按优先级和分数排序）

        Args:
            limit: 返回数量限制

        Returns:
            推送队列项列表
        """
        async with vector_session.pg_pool.acquire() as conn:
            # 获取上次推送时间，确保间隔 >= 2小时
            last_push = await conn.fetchval(
                """
                SELECT MAX(sent_at)
                FROM push_queue
                WHERE status = 'sent'
                """
            )

            two_hours_ago = datetime.now() - timedelta(hours=2)
            can_push = last_push is None or last_push < two_hours_ago

            if not can_push:
                return []

            # 查询待推送项
            records = await conn.fetch(
                """
                SELECT
                    pq.*,
                    h.keyword,
                    br.report
                FROM push_queue pq
                JOIN hotspots h ON pq.hotspot_id = h.id
                JOIN business_reports br ON pq.report_id = br.id
                WHERE pq.status = 'pending'
                ORDER BY
                    CASE pq.priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    pq.score DESC
                LIMIT $1
                """,
                limit,
            )

            return [
                PushQueueItem(
                    id=r["id"],
                    hotspot_id=r["hotspot_id"],
                    report_id=r["report_id"],
                    priority=Priority(r["priority"]),
                    score=float(r["score"]),
                    status=PushStatus(r["status"]),
                    channels=json.loads(r["channels"])
                    if isinstance(r["channels"], str)
                    else r["channels"],
                    scheduled_at=r["scheduled_at"],
                    sent_at=r["sent_at"],
                    retry_count=r["retry_count"],
                    error_message=r["error_message"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    keyword=r["keyword"],
                    report=BusinessReportContent.model_validate_json(r["report"])
                    if isinstance(r["report"], str)
                    else BusinessReportContent.model_validate(r["report"]),
                )
                for r in records
            ]

    async def list_hotspots(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[HotspotStatus] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        列出热点（分页）

        Args:
            page: 页码
            page_size: 每页数量
            status: 状态过滤
            keyword: 关键词搜索

        Returns:
            包含 total, page, page_size, items 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            # 构建查询条件
            conditions = []
            params = []
            param_idx = 1

            if status:
                conditions.append(f"status = ${param_idx}")
                params.append(status.value)
                param_idx += 1

            if keyword:
                conditions.append(
                    f"(keyword ILIKE ${param_idx} OR normalized_keyword ILIKE ${param_idx})"
                )
                params.append(f"%{keyword}%")
                param_idx += 1

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # 查询总数
            total = await conn.fetchval(
                f"SELECT COUNT(*) FROM hotspots WHERE {where_clause}", *params
            )

            # 查询数据
            offset = (page - 1) * page_size
            records = await conn.fetch(
                f"""
                SELECT * FROM hotspots
                WHERE {where_clause}
                ORDER BY last_seen_at DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
                """,
                *params,
                page_size,
                offset,
            )

            items = [
                HotspotDetail(
                    id=r["id"],
                    keyword=r["keyword"],
                    normalized_keyword=r["normalized_keyword"],
                    embedding_model=r["embedding_model"],
                    cluster_id=r["cluster_id"],
                    first_seen_at=r["first_seen_at"],
                    last_seen_at=r["last_seen_at"],
                    appearance_count=r["appearance_count"],
                    platforms=[
                        PlatformInfo(**p)
                        for p in (
                            json.loads(r["platforms"])
                            if isinstance(r["platforms"], str)
                            else r["platforms"]
                        )
                    ],
                    status=HotspotStatus(r["status"]),
                    last_crawled_at=r["last_crawled_at"],
                    crawl_count=r["crawl_count"],
                    crawl_started_at=r["crawl_started_at"],
                    crawl_failed_count=r["crawl_failed_count"],
                    is_filtered=r["is_filtered"],
                    filter_reason=r["filter_reason"],
                    filtered_at=r["filtered_at"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in records
            ]

            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": items,
            }

    async def delete_hotspot(self, hotspot_id: int) -> Dict[str, Any]:
        """
        删除热点

        Args:
            hotspot_id: 热点ID

        Returns:
            包含 success, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM hotspots WHERE id = $1", hotspot_id
            )

            deleted_count = int(result.split()[-1])
            if deleted_count == 0:
                raise ValueError(f"热点 {hotspot_id} 不存在")

            return {"success": True, "message": f"热点 {hotspot_id} 已删除"}

    async def get_hotspot_by_id(self, hotspot_id: int) -> Optional[HotspotDetail]:
        """
        根据ID获取热点详情

        Args:
            hotspot_id: 热点ID

        Returns:
            热点详情或 None
        """
        async with vector_session.pg_pool.acquire() as conn:
            r = await conn.fetchrow("SELECT * FROM hotspots WHERE id = $1", hotspot_id)

            if not r:
                return None

            return HotspotDetail(
                id=r["id"],
                keyword=r["keyword"],
                normalized_keyword=r["normalized_keyword"],
                embedding_model=r["embedding_model"],
                cluster_id=r["cluster_id"],
                first_seen_at=r["first_seen_at"],
                last_seen_at=r["last_seen_at"],
                appearance_count=r["appearance_count"],
                platforms=[
                    PlatformInfo(**p)
                    for p in (
                        json.loads(r["platforms"])
                        if isinstance(r["platforms"], str)
                        else r["platforms"]
                    )
                ],
                status=HotspotStatus(r["status"]),
                last_crawled_at=r["last_crawled_at"],
                crawl_count=r["crawl_count"],
                crawl_started_at=r["crawl_started_at"],
                crawl_failed_count=r["crawl_failed_count"],
                is_filtered=r["is_filtered"],
                filter_reason=r["filter_reason"],
                filtered_at=r["filtered_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )

    async def get_cluster_hotspots(self, cluster_id: int) -> List[HotspotDetail]:
        """
        获取同簇的所有热点

        Args:
            cluster_id: 簇ID

        Returns:
            热点列表
        """
        async with vector_session.pg_pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT * FROM hotspots
                WHERE cluster_id = $1
                ORDER BY last_seen_at DESC
                """,
                cluster_id,
            )

            return [
                HotspotDetail(
                    id=r["id"],
                    keyword=r["keyword"],
                    normalized_keyword=r["normalized_keyword"],
                    embedding_model=r["embedding_model"],
                    cluster_id=r["cluster_id"],
                    first_seen_at=r["first_seen_at"],
                    last_seen_at=r["last_seen_at"],
                    appearance_count=r["appearance_count"],
                    platforms=[
                        PlatformInfo(**p)
                        for p in (
                            json.loads(r["platforms"])
                            if isinstance(r["platforms"], str)
                            else r["platforms"]
                        )
                    ],
                    status=HotspotStatus(r["status"]),
                    last_crawled_at=r["last_crawled_at"],
                    crawl_count=r["crawl_count"],
                    crawl_started_at=r["crawl_started_at"],
                    crawl_failed_count=r["crawl_failed_count"],
                    is_filtered=r["is_filtered"],
                    filter_reason=r["filter_reason"],
                    filtered_at=r["filtered_at"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in records
            ]

    async def link_hotspot(
        self, keyword: str, source_hotspot_id: int
    ) -> Dict[str, Any]:
        """
        关联热点 - 复用已有热点的分析信息创建新热点

        Args:
            keyword: 新的关键词
            source_hotspot_id: 要复用信息的热点ID

        Returns:
            包含 success, hotspot_id, cluster_id, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 获取源热点信息
                source_hotspot = await conn.fetchrow(
                    """
                    SELECT keyword, normalized_keyword, cluster_id, platforms,
                           status, is_filtered, filter_reason
                    FROM hotspots
                    WHERE id = $1
                    """,
                    source_hotspot_id,
                )

                if not source_hotspot:
                    raise ValueError(f"源热点 {source_hotspot_id} 不存在")

                # 检查新关键词是否已存在
                existing = await conn.fetchrow(
                    "SELECT id FROM hotspots WHERE keyword = $1", keyword
                )

                if existing:
                    return {
                        "success": False,
                        "hotspot_id": existing["id"],
                        "cluster_id": source_hotspot["cluster_id"],
                        "message": f"关键词 '{keyword}' 已存在，无法关联",
                    }

                # 生成新的向量
                embedding = await vector_service.generate_embedding(keyword)

                # 获取或创建 cluster
                cluster_id = source_hotspot["cluster_id"]

                if cluster_id:
                    # 更新现有 cluster，添加新关键词
                    await conn.execute(
                        """
                        UPDATE hotspot_clusters
                        SET member_count = member_count + 1,
                            keywords = keywords || $1::jsonb,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                        """,
                        json.dumps([keyword]),
                        cluster_id,
                    )
                else:
                    # 创建新 cluster，包含源热点和新热点
                    cluster_id = await conn.fetchval(
                        """
                        INSERT INTO hotspot_clusters (cluster_name, member_count, keywords)
                        VALUES ($1, 2, $2)
                        RETURNING id
                        """,
                        source_hotspot["keyword"],  # 使用源热点作为 cluster 名称
                        json.dumps([source_hotspot["keyword"], keyword]),
                    )

                    # 更新源热点的 cluster_id
                    await conn.execute(
                        """
                        UPDATE hotspots
                        SET cluster_id = $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $2
                        """,
                        cluster_id,
                        source_hotspot_id,
                    )

                # 复用源热点的平台信息（作为初始值）
                platforms = (
                    json.loads(source_hotspot["platforms"])
                    if isinstance(source_hotspot["platforms"], str)
                    else source_hotspot["platforms"]
                )

                # 创建新热点
                now = datetime.now()
                new_hotspot_id = await conn.fetchval(
                    """
                    INSERT INTO hotspots (
                        keyword, normalized_keyword, embedding, embedding_model,
                        cluster_id, first_seen_at, last_seen_at, appearance_count,
                        platforms, status, is_filtered, filter_reason, filtered_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    RETURNING id
                    """,
                    keyword,
                    keyword.lower().strip(),
                    embedding,
                    vector_service.EMBEDDING_MODEL,
                    cluster_id,
                    now,
                    now,
                    1,
                    json.dumps(platforms),
                    source_hotspot["status"],
                    source_hotspot["is_filtered"],
                    source_hotspot["filter_reason"],
                    source_hotspot["filtered_at"]
                    if source_hotspot["is_filtered"]
                    else None,
                )

                return {
                    "success": True,
                    "hotspot_id": new_hotspot_id,
                    "cluster_id": cluster_id,
                    "message": f"成功创建关联热点 '{keyword}' (ID: {new_hotspot_id})，已关联到簇 {cluster_id}",
                }

    # ==================== 聚簇管理方法 ====================

    async def list_clusters(self) -> List[ClusterInfo]:
        """
        列出所有聚簇

        Returns:
            聚簇列表
        """
        async with vector_session.pg_pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT id, cluster_name, member_count, keywords, created_at, updated_at
                FROM hotspot_clusters
                ORDER BY updated_at DESC
                """
            )

            return [
                ClusterInfo(
                    id=r["id"],
                    cluster_name=r["cluster_name"],
                    member_count=r["member_count"],
                    keywords=json.loads(r["keywords"])
                    if isinstance(r["keywords"], str)
                    else r["keywords"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in records
            ]

    async def merge_clusters(
        self, source_cluster_ids: List[int], target_cluster_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        合并多个聚簇

        Args:
            source_cluster_ids: 要合并的源簇ID列表
            target_cluster_name: 目标簇名称（可选）

        Returns:
            包含 success, cluster_id, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 获取所有源簇信息
                clusters = await conn.fetch(
                    """
                    SELECT id, cluster_name, member_count, keywords
                    FROM hotspot_clusters
                    WHERE id = ANY($1)
                    """,
                    source_cluster_ids,
                )

                if len(clusters) < 2:
                    raise ValueError("至少需要2个聚簇才能合并")

                # 收集所有关键词和计算总成员数
                all_keywords = []
                total_members = 0
                for cluster in clusters:
                    keywords = (
                        json.loads(cluster["keywords"])
                        if isinstance(cluster["keywords"], str)
                        else cluster["keywords"]
                    )
                    all_keywords.extend(keywords)
                    total_members += cluster["member_count"]

                # 去重关键词
                unique_keywords = list(dict.fromkeys(all_keywords))

                # 使用第一个簇作为目标簇，或使用指定的名称
                target_cluster_id = source_cluster_ids[0]
                final_cluster_name = target_cluster_name or clusters[0]["cluster_name"]

                # 更新目标簇
                await conn.execute(
                    """
                    UPDATE hotspot_clusters
                    SET cluster_name = $1,
                        member_count = $2,
                        keywords = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $4
                    """,
                    final_cluster_name,
                    total_members,
                    json.dumps(unique_keywords),
                    target_cluster_id,
                )

                # 更新所有热点的cluster_id到目标簇
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET cluster_id = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE cluster_id = ANY($2)
                    """,
                    target_cluster_id,
                    source_cluster_ids,
                )

                # 删除其他源簇
                other_cluster_ids = [
                    cid for cid in source_cluster_ids if cid != target_cluster_id
                ]
                if other_cluster_ids:
                    await conn.execute(
                        "DELETE FROM hotspot_clusters WHERE id = ANY($1)",
                        other_cluster_ids,
                    )

                return {
                    "success": True,
                    "cluster_id": target_cluster_id,
                    "message": f"成功合并 {len(source_cluster_ids)} 个聚簇到簇 {target_cluster_id}",
                }

    async def split_cluster(
        self,
        cluster_id: int,
        hotspot_ids: List[int],
        new_cluster_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        拆分聚簇 - 从指定聚簇中移出部分热点

        Args:
            cluster_id: 要拆分的簇ID
            hotspot_ids: 要移出的热点ID列表
            new_cluster_name: 新簇名称（可选）

        Returns:
            包含 success, new_cluster_id, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 检查簇是否存在
                cluster = await conn.fetchrow(
                    "SELECT id, cluster_name, member_count, keywords FROM hotspot_clusters WHERE id = $1",
                    cluster_id,
                )

                if not cluster:
                    raise ValueError(f"聚簇 {cluster_id} 不存在")

                # 获取要移出的热点
                hotspots = await conn.fetch(
                    """
                    SELECT id, keyword, cluster_id
                    FROM hotspots
                    WHERE id = ANY($1) AND cluster_id = $2
                    """,
                    hotspot_ids,
                    cluster_id,
                )

                if not hotspots:
                    raise ValueError("没有找到要移出的热点或热点不属于该聚簇")

                # 获取移出的关键词
                removed_keywords = [h["keyword"] for h in hotspots]

                # 如果移出的热点数量大于1，创建新簇
                new_cluster_id = None
                if len(hotspots) > 1:
                    # 确定新簇名称
                    final_new_cluster_name = new_cluster_name or removed_keywords[0]

                    # 创建新簇
                    new_cluster_id = await conn.fetchval(
                        """
                        INSERT INTO hotspot_clusters (cluster_name, member_count, keywords)
                        VALUES ($1, $2, $3)
                        RETURNING id
                        """,
                        final_new_cluster_name,
                        len(hotspots),
                        json.dumps(removed_keywords),
                    )

                    # 更新移出的热点到新簇
                    await conn.execute(
                        """
                        UPDATE hotspots
                        SET cluster_id = $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ANY($2)
                        """,
                        new_cluster_id,
                        hotspot_ids,
                    )
                else:
                    # 只有一个热点，直接清除其cluster_id
                    await conn.execute(
                        """
                        UPDATE hotspots
                        SET cluster_id = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                        """,
                        hotspot_ids[0],
                    )

                # 更新原簇的成员数量和关键词列表
                old_keywords = (
                    json.loads(cluster["keywords"])
                    if isinstance(cluster["keywords"], str)
                    else cluster["keywords"]
                )
                remaining_keywords = [
                    kw for kw in old_keywords if kw not in removed_keywords
                ]
                remaining_count = cluster["member_count"] - len(hotspots)

                if remaining_count > 0:
                    # 更新原簇
                    await conn.execute(
                        """
                        UPDATE hotspot_clusters
                        SET member_count = $1,
                            keywords = $2,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $3
                        """,
                        remaining_count,
                        json.dumps(remaining_keywords),
                        cluster_id,
                    )
                else:
                    # 如果原簇没有成员了，删除该簇
                    await conn.execute(
                        "DELETE FROM hotspot_clusters WHERE id = $1", cluster_id
                    )

                message = f"成功从簇 {cluster_id} 中移出 {len(hotspots)} 个热点"
                if new_cluster_id:
                    message += f"，并创建新簇 {new_cluster_id}"

                return {
                    "success": True,
                    "new_cluster_id": new_cluster_id,
                    "message": message,
                }

    async def update_cluster(
        self, cluster_id: int, cluster_name: str
    ) -> Dict[str, Any]:
        """
        更新聚簇信息

        Args:
            cluster_id: 簇ID
            cluster_name: 新的簇名称

        Returns:
            包含 success, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE hotspot_clusters
                SET cluster_name = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                cluster_name,
                cluster_id,
            )

            updated_count = int(result.split()[-1])
            if updated_count == 0:
                raise ValueError(f"聚簇 {cluster_id} 不存在")

            return {"success": True, "message": f"聚簇 {cluster_id} 已更新"}

    async def delete_cluster(self, cluster_id: int) -> Dict[str, Any]:
        """
        删除聚簇

        Args:
            cluster_id: 簇ID

        Returns:
            包含 success, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 将所有相关热点的cluster_id设为NULL
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET cluster_id = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE cluster_id = $1
                    """,
                    cluster_id,
                )

                # 删除聚簇
                result = await conn.execute(
                    "DELETE FROM hotspot_clusters WHERE id = $1", cluster_id
                )

                deleted_count = int(result.split()[-1])
                if deleted_count == 0:
                    raise ValueError(f"聚簇 {cluster_id} 不存在")

                return {"success": True, "message": f"聚簇 {cluster_id} 已删除"}

    async def remove_hotspot_from_cluster(
        self, cluster_id: int, hotspot_id: int
    ) -> Dict[str, Any]:
        """
        从聚簇中移除单个热点

        Args:
            cluster_id: 簇ID
            hotspot_id: 热点ID

        Returns:
            包含 success, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 获取热点信息
                hotspot = await conn.fetchrow(
                    "SELECT id, keyword, cluster_id FROM hotspots WHERE id = $1",
                    hotspot_id,
                )

                if not hotspot:
                    raise ValueError(f"热点 {hotspot_id} 不存在")

                if hotspot["cluster_id"] != cluster_id:
                    raise ValueError(f"热点 {hotspot_id} 不属于聚簇 {cluster_id}")

                # 将热点的cluster_id设为NULL
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET cluster_id = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                    """,
                    hotspot_id,
                )

                # 获取簇信息
                cluster = await conn.fetchrow(
                    "SELECT id, member_count, keywords FROM hotspot_clusters WHERE id = $1",
                    cluster_id,
                )

                if cluster:
                    # 更新簇的成员数量和关键词列表
                    old_keywords = (
                        json.loads(cluster["keywords"])
                        if isinstance(cluster["keywords"], str)
                        else cluster["keywords"]
                    )
                    new_keywords = [
                        kw for kw in old_keywords if kw != hotspot["keyword"]
                    ]
                    new_member_count = cluster["member_count"] - 1

                    if new_member_count > 0:
                        await conn.execute(
                            """
                            UPDATE hotspot_clusters
                            SET member_count = $1,
                                keywords = $2,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = $3
                            """,
                            new_member_count,
                            json.dumps(new_keywords),
                            cluster_id,
                        )
                    else:
                        # 如果簇没有成员了，删除该簇
                        await conn.execute(
                            "DELETE FROM hotspot_clusters WHERE id = $1", cluster_id
                        )

                return {
                    "success": True,
                    "message": f"成功从簇 {cluster_id} 中移除热点 {hotspot_id}",
                }


# 全局热点服务实例
hotspot_service = HotspotService()
