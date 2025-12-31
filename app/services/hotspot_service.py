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

            # 平台名称映射
            platform_name_map = {
                'xhs': '小红书',
                'dy': '抖音',
                'bili': '哔哩哔哩',
                'ks': '快手',
                'wb': '微博',
                'tieba': '贴吧',
                'zhihu': '知乎'
            }

            # 构建平台信息（从传入的平台数据中提取）
            if platform_data:
                platform_type = platform_data.get("type", "unknown")
                platform_name = platform_name_map.get(platform_type, platform_type)

                # 解析热度值（去除万、亿等单位）
                viewnum_str = platform_data.get("viewnum", "0")
                heat_score = self._parse_viewnum(viewnum_str)

                platforms = [
                    {
                        "platform": platform_name,
                        "rank": int(platform_data.get("rank", 0)),
                        "heat_score": heat_score,
                        "seen_at": platform_data.get("date", datetime.now().isoformat()),
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

    async def link_hotspots(
        self, source_hotspot_id: int, target_hotspot_id: int
    ) -> Dict[str, Any]:
        """
        标识词组有关联（将两个热词关联到同一个簇）

        Args:
            source_hotspot_id: 源热点ID
            target_hotspot_id: 目标热点ID（要关联到的簇）

        Returns:
            包含 success, message, cluster_id 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 获取目标热点的簇ID
                target_hotspot = await conn.fetchrow(
                    "SELECT cluster_id, keyword FROM hotspots WHERE id = $1",
                    target_hotspot_id,
                )

                if not target_hotspot:
                    raise ValueError(f"目标热点 {target_hotspot_id} 不存在")

                source_hotspot = await conn.fetchrow(
                    "SELECT cluster_id, keyword FROM hotspots WHERE id = $1",
                    source_hotspot_id,
                )

                if not source_hotspot:
                    raise ValueError(f"源热点 {source_hotspot_id} 不存在")

                cluster_id = target_hotspot["cluster_id"]

                # 如果目标热点没有簇，创建新簇
                if cluster_id is None:
                    cluster_id = await conn.fetchval(
                        """
                        INSERT INTO hotspot_clusters (cluster_name, member_count, keywords)
                        VALUES ($1, $2, $3)
                        RETURNING id
                        """,
                        target_hotspot["keyword"],
                        2,
                        json.dumps(
                            [target_hotspot["keyword"], source_hotspot["keyword"]]
                        ),
                    )

                    # 更新目标热点的 cluster_id
                    await conn.execute(
                        "UPDATE hotspots SET cluster_id = $1 WHERE id = $2",
                        cluster_id,
                        target_hotspot_id,
                    )
                else:
                    # 更新现有簇
                    await conn.execute(
                        """
                        UPDATE hotspot_clusters
                        SET member_count = member_count + 1,
                            keywords = keywords || $1::jsonb
                        WHERE id = $2
                        """,
                        json.dumps([source_hotspot["keyword"]]),
                        cluster_id,
                    )

                # 更新源热点的 cluster_id
                await conn.execute(
                    "UPDATE hotspots SET cluster_id = $1 WHERE id = $2",
                    cluster_id,
                    source_hotspot_id,
                )

                return {
                    "success": True,
                    "message": f"热点 {source_hotspot_id} 已关联到簇 {cluster_id}",
                    "cluster_id": cluster_id,
                }

    async def update_hotspot_status(
        self, hotspot_id: int, status: HotspotStatus
    ) -> Dict[str, Any]:
        """
        更新热点状态

        Args:
            hotspot_id: 热点ID
            status: 新状态

        Returns:
            包含 success, message 的字典
        """
        async with vector_session.pg_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE hotspots SET status = $1 WHERE id = $2",
                status.value,
                hotspot_id,
            )

            deleted_count = int(result.split()[-1])
            if deleted_count == 0:
                raise ValueError(f"热点 {hotspot_id} 不存在")

            return {
                "success": True,
                "message": f"热点 {hotspot_id} 状态已更新为 {status.value}",
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


# 全局热点服务实例
hotspot_service = HotspotService()
