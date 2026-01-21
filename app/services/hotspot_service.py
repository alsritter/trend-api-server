from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.db import session
from app.services.vector_service import vector_service
from app.schemas.hotspot import (
    KeywordAnalysis,
    SimilarHotspot,
    HotspotStatus,
    HotspotDetail,
    PlatformInfo,
    PlatformDataInput,
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
        self,
        analysis: KeywordAnalysis,
        platform_data: Optional[PlatformDataInput] = None,
    ) -> Dict[str, Any]:
        """
        根据AI分析结果添加热词

        Args:
            analysis: AI返回的热词分析结果
            platform_data: 平台原始数据(包含 type, rank, viewnum, url 等)

        Returns:
            包含 hotspot_id, action, message 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 检查是否已存在（无论是低价值词还是有价值词都添加到热点表）
            existing_hotspot = await conn.fetchrow(
                "SELECT id, status, last_seen_at FROM hotspots WHERE keyword = $1",
                analysis.title,
            )

            if existing_hotspot:
                # 提取平台 URL 和 word_cover（如果有）
                platform_url = platform_data.url if platform_data else None
                word_cover = platform_data.word_cover if platform_data else None

                # 更新现有热点的 AI 分析信息、平台 URL 和 word_cover
                await conn.execute(
                    """
                    UPDATE hotspots
                    SET last_seen_at = CURRENT_TIMESTAMP,
                        appearance_count = appearance_count + 1,
                        updated_at = CURRENT_TIMESTAMP,
                        tags = $2,
                        confidence = $3,
                        opportunities = $4,
                        reasoning_keep = $5,
                        reasoning_risk = $6,
                        primary_category = $7,
                        platform_url = COALESCE($8, platform_url),
                        word_cover = COALESCE($9, word_cover)
                    WHERE id = $1
                    """,
                    existing_hotspot["id"],
                    analysis.tags if analysis.tags else [],
                    analysis.confidence,
                    analysis.opportunities if analysis.opportunities else [],
                    analysis.reasoning.keep if analysis.reasoning.keep else [],
                    analysis.reasoning.risk if analysis.reasoning.risk else [],
                    analysis.primary_category,
                    platform_url,
                    json.dumps(word_cover) if word_cover else None,
                )

                return {
                    "hotspot_id": existing_hotspot["id"],
                    "action": "updated",
                    "message": f"热点 '{analysis.title}' 已更新（包括 AI 分析信息）",
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
                            SET keywords = keywords || $1::jsonb,
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
                            INSERT INTO hotspot_clusters (cluster_name, keywords)
                            VALUES ($1, $2)
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
            # 注意：selected_hotspot_id 将在创建热点后设置
            create_new_cluster = cluster_id is None
            if create_new_cluster:
                cluster_id = await conn.fetchval(
                    """
                    INSERT INTO hotspot_clusters (cluster_name, keywords)
                    VALUES ($1, $2)
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
                platform_type = platform_data.type
                platform_name = platform_name_map.get(platform_type, platform_type)

                # 解析热度值（去除万、亿等单位）
                viewnum_str = platform_data.viewnum or "0"
                heat_score = self._parse_viewnum(viewnum_str)

                # 安全地转换 rank,处理空字符串的情况
                rank_value = platform_data.rank
                rank = int(rank_value) if rank_value and str(rank_value).strip() else 0

                platforms = [
                    {
                        "platform": platform_name,
                        "rank": rank,
                        "heat_score": heat_score,
                        "seen_at": platform_data.date or datetime.now().isoformat(),
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

            # 提取平台 URL 和 word_cover
            platform_url = platform_data.url if platform_data else None
            word_cover = platform_data.word_cover if platform_data else None

            now = datetime.now()
            hotspot_id = await conn.fetchval(
                """
                INSERT INTO hotspots (
                    keyword, normalized_keyword, embedding, embedding_model,
                    cluster_id, first_seen_at, last_seen_at, appearance_count, platforms,
                    status, is_filtered, filter_reason, filtered_at,
                    tags, confidence, opportunities, reasoning_keep, reasoning_risk, 
                    platform_url, primary_category, word_cover
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
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
                # AI 分析详细信息
                analysis.tags if analysis.tags else [],
                analysis.confidence,
                analysis.opportunities if analysis.opportunities else [],
                analysis.reasoning.keep if analysis.reasoning.keep else [],
                analysis.reasoning.risk if analysis.reasoning.risk else [],
                platform_url,
                analysis.primary_category,
                json.dumps(word_cover) if word_cover else None,
            )

            # 如果创建了新的聚簇，将当前热点设置为该聚簇的代表热点
            if create_new_cluster and cluster_id:
                await conn.execute(
                    """
                    UPDATE hotspot_clusters
                    SET selected_hotspot_id = $1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                    """,
                    hotspot_id,
                    cluster_id,
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

        --- 热词状态说明 ---

        'pending_validation',    -- 等待持续性验证（首次出现）
        'validated',             -- 已验证有持续性（3小时后二次出现）
        'rejected',              -- 已过滤（无商业价值）
        'crawling',              -- 爬虫进行中
        'crawled',               -- 爬取完成，等待分析
        'analyzing',             -- 商业分析中
        'analyzed',              -- 分析完成
        'archived'               -- 已归档

        这里的额外逻辑，需要检查完全匹配或者高相似度 last_seen_at 和 status 状态，
        如果 status 状态为 pending_validation，且 last_seen_at 大于 3 小时（低于 3 天）的
        热词，则更新这个热词的 last_seen_at 以及 status 为 validated

        注意：如果这个热词的 cluster_id 不为空，则需要将该 cluster 下的所有热词都更新为 validated

        Args:
            keyword: 热词名称

        Returns:
            包含 exists, action, hotspot_id, similar_hotspots, message 的字典
        """
        async with session.pg_pool.acquire() as conn:
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
                # 高相似度，更新时间和出现次数
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

    async def list_hotspots(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[HotspotStatus] = None,
        keyword: Optional[str] = None,
        similarity_search: Optional[str] = None,
        similarity_threshold: float = 0.7,
        hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        列出热点（分页）

        Args:
            page: 页码
            page_size: 每页数量
            status: 状态过滤
            keyword: 关键词模糊搜索
            similarity_search: 相似度搜索关键词
            similarity_threshold: 相似度阈值 (0.0-1.0)
            hours: 时间范围（小时），过滤最近更新的热点

        Returns:
            包含 total, page, page_size, items 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 如果使用相似度搜索
            if similarity_search:
                # 生成搜索词的向量
                from app.services.vector_service import vector_service

                search_embedding = await vector_service.generate_embedding(
                    similarity_search
                )

                # 构建查询条件
                conditions = []
                params = [search_embedding]  # $1 是搜索向量
                param_idx = 2

                if status:
                    conditions.append(f"status = ${param_idx}")
                    params.append(status.value)
                    param_idx += 1

                # 添加时间过滤
                if hours:
                    conditions.append(
                        f"updated_at >= NOW() - INTERVAL '1 hour' * ${param_idx}"
                    )
                    params.append(hours)
                    param_idx += 1

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                # 使用向量相似度搜索
                query = f"""
                    WITH similar_hotspots AS (
                        SELECT *,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM hotspots
                        WHERE {where_clause}
                            AND embedding IS NOT NULL
                            AND 1 - (embedding <=> $1::vector) >= ${param_idx}
                    )
                    SELECT COUNT(*) OVER() as total_count, *
                    FROM similar_hotspots
                    ORDER BY similarity DESC, last_seen_at DESC
                    LIMIT ${param_idx + 1} OFFSET ${param_idx + 2}
                """
                params.extend([similarity_threshold, page_size, (page - 1) * page_size])

                records = await conn.fetch(query, *params)
                total = records[0]["total_count"] if records else 0

            else:
                # 普通查询（原有逻辑）
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

                # 添加时间过滤
                if hours:
                    conditions.append(
                        f"last_seen_at >= NOW() - INTERVAL '1 hour' * ${param_idx}"
                    )
                    params.append(hours)
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
                    rejection_reason=r.get("rejection_reason"),
                    rejected_at=r.get("rejected_at"),
                    second_stage_rejection_reason=r.get(
                        "second_stage_rejection_reason"
                    ),
                    second_stage_rejected_at=r.get("second_stage_rejected_at"),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    # AI 分析详细信息
                    tags=r.get("tags"),
                    confidence=r.get("confidence"),
                    opportunities=r.get("opportunities"),
                    reasoning_keep=r.get("reasoning_keep"),
                    reasoning_risk=r.get("reasoning_risk"),
                    platform_url=r.get("platform_url"),
                    primary_category=r.get("primary_category"),
                    word_cover=(
                        json.loads(r.get("word_cover"))
                        if r.get("word_cover") and isinstance(r.get("word_cover"), str)
                        else r.get("word_cover")
                    ),
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
        async with session.pg_pool.acquire() as conn:
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
        async with session.pg_pool.acquire() as conn:
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
                rejection_reason=r.get("rejection_reason"),
                rejected_at=r.get("rejected_at"),
                second_stage_rejection_reason=r.get("second_stage_rejection_reason"),
                second_stage_rejected_at=r.get("second_stage_rejected_at"),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                # AI 分析详细信息
                tags=r.get("tags"),
                confidence=r.get("confidence"),
                opportunities=r.get("opportunities"),
                reasoning_keep=r.get("reasoning_keep"),
                reasoning_risk=r.get("reasoning_risk"),
                platform_url=r.get("platform_url"),
                primary_category=r.get("primary_category"),
                word_cover=(
                    json.loads(r.get("word_cover"))
                    if r.get("word_cover") and isinstance(r.get("word_cover"), str)
                    else r.get("word_cover")
                ),
            )

    async def get_cluster_hotspots(self, cluster_id: int) -> List[HotspotDetail]:
        """
        获取同簇的所有热点

        Args:
            cluster_id: 簇ID

        Returns:
            热点列表
        """
        async with session.pg_pool.acquire() as conn:
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
                    rejection_reason=r.get("rejection_reason"),
                    rejected_at=r.get("rejected_at"),
                    second_stage_rejection_reason=r.get(
                        "second_stage_rejection_reason"
                    ),
                    second_stage_rejected_at=r.get("second_stage_rejected_at"),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    # AI 分析详细信息
                    tags=r.get("tags"),
                    confidence=r.get("confidence"),
                    opportunities=r.get("opportunities"),
                    reasoning_keep=r.get("reasoning_keep"),
                    reasoning_risk=r.get("reasoning_risk"),
                    platform_url=r.get("platform_url"),
                    primary_category=r.get("primary_category"),
                    word_cover=(
                        json.loads(r.get("word_cover"))
                        if r.get("word_cover") and isinstance(r.get("word_cover"), str)
                        else r.get("word_cover")
                    ),
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
        async with session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 获取源热点信息
                source_hotspot = await conn.fetchrow(
                    """
                    SELECT keyword, normalized_keyword, cluster_id, platforms,
                           status, is_filtered, filter_reason, filtered_at
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
                        SET keywords = keywords || $1::jsonb,
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
                        INSERT INTO hotspot_clusters (cluster_name, keywords)
                        VALUES ($1, $2)
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

    async def list_validated_hotspots(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取所有 validated 状态的热词列表，每个 cluster 只返回一个热词

        规则：
        1. 如果 cluster 有 selected_hotspot_id，返回该热词
        2. 如果 cluster 没有 selected_hotspot_id，自动选择该 cluster 下第一个 validated 热词并设置
        3. 对于没有 cluster_id 的热词，直接返回
        4. 默认只返回最近 24 小时内更新的热词

        Args:
            hours: 时间范围（小时），默认 24 小时

        Returns:
            包含 total, items 的字典
        """
        async with session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 计算时间阈值
                time_threshold = datetime.now() - timedelta(hours=hours)

                # 1. 获取所有有 cluster 且有 selected_hotspot_id 的热词
                selected_hotspots = await conn.fetch(
                    """
                    SELECT DISTINCT ON (h.cluster_id)
                        h.id,
                        h.keyword,
                        h.cluster_id,
                        h.first_seen_at,
                        h.last_seen_at,
                        h.appearance_count,
                        h.platforms,
                        h.created_at,
                        h.updated_at
                    FROM hotspots h
                    INNER JOIN hotspot_clusters c ON h.cluster_id = c.id
                    WHERE h.status = $1
                        AND c.selected_hotspot_id IS NOT NULL
                        AND h.id = c.selected_hotspot_id
                        AND h.last_seen_at >= $2
                    ORDER BY h.cluster_id, h.last_seen_at DESC
                    """,
                    HotspotStatus.VALIDATED.value,
                    time_threshold,
                )

                # 2. 获取所有有 cluster 但没有 selected_hotspot_id 的 cluster
                clusters_without_selection = await conn.fetch(
                    """
                    SELECT DISTINCT c.id as cluster_id
                    FROM hotspot_clusters c
                    INNER JOIN hotspots h ON h.cluster_id = c.id
                    WHERE c.selected_hotspot_id IS NULL
                        AND h.status = $1
                        AND h.last_seen_at >= $2
                    """,
                    HotspotStatus.VALIDATED.value,
                    time_threshold,
                )

                # 为这些 cluster 选择并设置 selected_hotspot_id
                newly_selected_hotspots = []
                for cluster_record in clusters_without_selection:
                    cluster_id = cluster_record["cluster_id"]

                    # 获取该 cluster 下第一个 validated 热词（在时间范围内）
                    first_hotspot = await conn.fetchrow(
                        """
                        SELECT
                            h.id,
                            h.keyword,
                            h.cluster_id,
                            h.first_seen_at,
                            h.last_seen_at,
                            h.appearance_count,
                            h.platforms,
                            h.created_at,
                            h.updated_at
                        FROM hotspots h
                        WHERE h.cluster_id = $1
                            AND h.status = $2
                            AND h.last_seen_at >= $3
                        ORDER BY h.last_seen_at DESC
                        LIMIT 1
                        """,
                        cluster_id,
                        HotspotStatus.VALIDATED.value,
                        time_threshold,
                    )

                    if first_hotspot:
                        # 更新 cluster 的 selected_hotspot_id
                        await conn.execute(
                            """
                            UPDATE hotspot_clusters
                            SET selected_hotspot_id = $1,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = $2
                            """,
                            first_hotspot["id"],
                            cluster_id,
                        )
                        newly_selected_hotspots.append(first_hotspot)

                # 3. 获取所有没有 cluster_id 的 validated 热词（在时间范围内）
                no_cluster_hotspots = await conn.fetch(
                    """
                    SELECT
                        h.id,
                        h.keyword,
                        h.cluster_id,
                        h.first_seen_at,
                        h.last_seen_at,
                        h.appearance_count,
                        h.platforms,
                        h.created_at,
                        h.updated_at
                    FROM hotspots h
                    WHERE h.status = $1
                        AND h.cluster_id IS NULL
                        AND h.last_seen_at >= $2
                    ORDER BY h.last_seen_at DESC
                    """,
                    HotspotStatus.VALIDATED.value,
                    time_threshold,
                )

                # 合并所有结果
                all_hotspots = (
                    list(selected_hotspots)
                    + newly_selected_hotspots
                    + list(no_cluster_hotspots)
                )

                from app.schemas.hotspot import ValidatedHotspotItem, PlatformInfo

                items = [
                    ValidatedHotspotItem(
                        id=r["id"],
                        keyword=r["keyword"],
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
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                    )
                    for r in all_hotspots
                ]

                return {
                    "total": len(items),
                    "items": items,
                }

    async def update_hotspot_status(
        self, hotspot_id: int, new_status: HotspotStatus
    ) -> Dict[str, Any]:
        """
        更新热词状态

        Args:
            hotspot_id: 热词ID
            new_status: 新的状态

        Returns:
            包含 success, message, old_status, new_status 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 获取当前状态
            current = await conn.fetchrow(
                "SELECT id, keyword, status FROM hotspots WHERE id = $1", hotspot_id
            )

            if not current:
                raise ValueError(f"热词 {hotspot_id} 不存在")

            old_status = current["status"]

            # 如果状态相同，直接返回
            if old_status == new_status.value:
                return {
                    "success": True,
                    "message": f"热词 '{current['keyword']}' 状态未改变",
                    "old_status": old_status,
                    "new_status": new_status.value,
                }

            # 更新状态
            await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                new_status.value,
                hotspot_id,
            )

            return {
                "success": True,
                "message": f"热词 '{current['keyword']}' 状态已从 {old_status} 更新为 {new_status.value}",
                "old_status": old_status,
                "new_status": new_status.value,
            }

    async def update_hotspot_status_and_set_representative(
        self,
        hotspot_id: int,
        new_status: HotspotStatus,
        set_as_representative: bool = True,
    ) -> Dict[str, Any]:
        """
        更新热词状态，并可选设置为聚簇代表

        Args:
            hotspot_id: 热词ID
            new_status: 新的状态
            set_as_representative: 是否设置为聚簇代表（如果有cluster_id）

        Returns:
            包含 success, message, old_status, new_status, cluster_id, is_cluster_representative 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 1. 获取当前热词信息
            hotspot_record = await conn.fetchrow(
                "SELECT id, keyword, status, cluster_id FROM hotspots WHERE id = $1",
                hotspot_id,
            )

            if not hotspot_record:
                raise ValueError(f"热词 {hotspot_id} 不存在")

            old_status = hotspot_record["status"]
            cluster_id = hotspot_record["cluster_id"]
            is_cluster_representative = False

            # 2. 更新热词状态
            await conn.execute(
                "UPDATE hotspots SET status = $1, updated_at = NOW() WHERE id = $2",
                new_status.value,
                hotspot_id,
            )

            # 3. 如果有 cluster_id 且需要设置为代表，则更新 cluster 的 selected_hotspot_id
            if cluster_id and set_as_representative:
                await conn.execute(
                    "UPDATE hotspot_clusters SET selected_hotspot_id = $1, updated_at = NOW() WHERE id = $2",
                    hotspot_id,
                    cluster_id,
                )
                is_cluster_representative = True

            message = f"热词 '{hotspot_record['keyword']}' 状态已更新: {old_status} -> {new_status.value}"
            if is_cluster_representative:
                message += f"，并已设置为聚簇 {cluster_id} 的代表热词"

            return {
                "success": True,
                "message": message,
                "old_status": old_status,
                "new_status": new_status.value,
                "cluster_id": cluster_id,
                "is_cluster_representative": is_cluster_representative,
            }

    async def mark_outdated_hotspots(self, days: int = 2) -> Dict[str, Any]:
        """
        标记过时的热词（超过指定天数未更新的热词）

        Args:
            days: 天数阈值，默认 2 天

        Returns:
            包含 success, message, marked_count, hotspot_ids 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 计算时间阈值
            time_threshold = datetime.now() - timedelta(days=days)

            # 查找需要标记为过时的热词
            # 只标记那些不是 rejected、archived、outdated 状态的热词
            outdated_hotspots = await conn.fetch(
                """
                SELECT id, keyword
                FROM hotspots
                WHERE last_seen_at < $1
                    AND status NOT IN ($2, $3, $4)
                """,
                time_threshold,
                HotspotStatus.REJECTED.value,
                HotspotStatus.ARCHIVED.value,
                HotspotStatus.OUTDATED.value,
            )

            if not outdated_hotspots:
                return {
                    "success": True,
                    "message": f"没有发现超过 {days} 天未更新的热词",
                    "marked_count": 0,
                    "hotspot_ids": [],
                }

            # 提取热词ID列表
            hotspot_ids = [r["id"] for r in outdated_hotspots]

            # 批量更新状态为 outdated
            await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ANY($2::int[])
                """,
                HotspotStatus.OUTDATED.value,
                hotspot_ids,
            )

            return {
                "success": True,
                "message": f"成功标记 {len(hotspot_ids)} 个过时热词",
                "marked_count": len(hotspot_ids),
                "hotspot_ids": hotspot_ids,
            }

    async def trigger_crawl_for_hotspot(
        self,
        hotspot_id: int,
        platforms: List[str],
        crawler_type: str = "search",
        max_notes_count: int = 50,
        enable_comments: bool = True,
        enable_sub_comments: bool = False,
        max_comments_count: int = 20,
    ) -> Dict[str, Any]:
        """
        为指定热点触发爬虫任务

        Args:
            hotspot_id: 热点ID
            platforms: 平台列表 (如 ['xhs', 'dy', 'bili'])
            crawler_type: 爬虫类型
            max_notes_count: 每个平台最大爬取数量
            enable_comments: 是否爬取评论
            enable_sub_comments: 是否爬取二级评论
            max_comments_count: 每条内容最大评论数量

        Returns:
            包含 success, task_ids, total_tasks 的字典
        """
        from app.celery_app.tasks.crawler_tasks import run_crawler

        async with session.pg_pool.acquire() as conn:
            # 验证热点是否存在
            hotspot = await conn.fetchrow(
                "SELECT id, keyword, status FROM hotspots WHERE id = $1",
                hotspot_id,
            )

            if not hotspot:
                raise ValueError(f"热点 {hotspot_id} 不存在")

            keyword = hotspot["keyword"]

            # 创建爬虫任务列表
            task_ids = []

            # 为每个平台创建一个爬虫任务
            for platform in platforms:
                # 调用 Celery 任务
                task = run_crawler.apply_async(
                    kwargs={
                        "platform": platform,
                        "crawler_type": crawler_type,
                        "keywords": keyword,  # 使用热点关键词
                        "enable_checkpoint": True,
                        "checkpoint_id": "",
                        "max_notes_count": max_notes_count,
                        "enable_comments": enable_comments,
                        "enable_sub_comments": enable_sub_comments,
                        "max_comments_count": max_comments_count,
                        "hotspot_id": str(hotspot_id),  # 传递热点ID到爬虫
                        # 平台特定参数留空，由爬虫自动搜索
                        "xhs_note_url_list": None,
                        "xhs_creator_url_list": None,
                        "weibo_specified_id_list": None,
                        "weibo_creator_id_list": None,
                        "tieba_specified_id_list": None,
                        "tieba_name_list": None,
                        "tieba_creator_url_list": None,
                        "bili_creator_id_list": None,
                        "bili_specified_id_list": None,
                        "dy_specified_id_list": None,
                        "dy_creator_id_list": None,
                        "ks_specified_id_list": None,
                        "ks_creator_id_list": None,
                        "zhihu_creator_url_list": None,
                        "zhihu_specified_id_list": None,
                    }
                )

                task_ids.append(task.id)

                # 保存任务到数据库（需要通过 MySQL 连接）
                # 这里需要调用 task_repo，但由于是异步的，我们在 API 层处理
                # 所以这里返回任务ID，让 API 层保存

            # 更新热点状态为 crawling
            await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    crawl_started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                HotspotStatus.CRAWLING.value,
                hotspot_id,
            )

            return {
                "success": True,
                "hotspot_id": hotspot_id,
                "keyword": keyword,
                "task_ids": task_ids,
                "total_tasks": len(task_ids),
                "platforms": platforms,
            }

    async def list_crawled_hotspots(
        self, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取所有已爬取状态的热点列表

        Args:
            page: 页码
            page_size: 每页数量

        Returns:
            包含 total, page, page_size, items 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 查询总数
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM hotspots WHERE status = $1",
                HotspotStatus.CRAWLED.value,
            )

            # 查询数据
            offset = (page - 1) * page_size
            records = await conn.fetch(
                """
                SELECT
                    id, keyword, cluster_id, status, last_seen_at,
                    last_crawled_at, crawl_count, platforms,
                    created_at, updated_at
                FROM hotspots
                WHERE status = $1
                ORDER BY last_crawled_at DESC, updated_at DESC
                LIMIT $2 OFFSET $3
                """,
                HotspotStatus.CRAWLED.value,
                page_size,
                offset,
            )

            from app.schemas.hotspot import CrawledHotspotItem

            items = [
                CrawledHotspotItem(
                    id=r["id"],
                    keyword=r["keyword"],
                    cluster_id=r["cluster_id"],
                    status=HotspotStatus(r["status"]),
                    last_seen_at=r["last_seen_at"],
                    last_crawled_at=r["last_crawled_at"],
                    crawl_count=r["crawl_count"],
                    platforms=[
                        PlatformInfo(**p)
                        for p in (
                            json.loads(r["platforms"])
                            if isinstance(r["platforms"], str)
                            else r["platforms"]
                        )
                    ],
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

    async def reject_hotspot(
        self, hotspot_id: int, rejection_reason: str
    ) -> Dict[str, Any]:
        """
        拒绝热点并记录拒绝原因（第一阶段 - AI初筛）

        Args:
            hotspot_id: 热点ID
            rejection_reason: 拒绝原因

        Returns:
            包含 success, message, hotspot_id, old_status 的字典

        Raises:
            ValueError: 如果热点不存在
        """
        async with session.pg_pool.acquire() as conn:
            # 获取当前热点状态
            record = await conn.fetchrow(
                "SELECT status FROM hotspots WHERE id = $1", hotspot_id
            )

            if not record:
                raise ValueError(f"热点 {hotspot_id} 不存在")

            old_status = record["status"]

            # 更新为 rejected 状态并记录拒绝原因和时间
            await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    filter_reason = $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
                """,
                HotspotStatus.REJECTED.value,
                rejection_reason,
                hotspot_id,
            )

            return {
                "success": True,
                "message": f"热点已拒绝: {rejection_reason}",
                "hotspot_id": hotspot_id,
                "old_status": old_status,
            }

    async def reject_second_stage(
        self, hotspot_id: int, rejection_reason: str
    ) -> Dict[str, Any]:
        """
        第二阶段拒绝热点并记录拒绝原因（深度分析后）

        用于热点通过了第一阶段初筛，但在第二阶段深度分析后被拒绝的场景

        Args:
            hotspot_id: 热点ID
            rejection_reason: 第二阶段拒绝原因

        Returns:
            包含 success, message, hotspot_id, old_status 的字典

        Raises:
            ValueError: 如果热点不存在
        """
        async with session.pg_pool.acquire() as conn:
            # 获取当前热点状态
            record = await conn.fetchrow(
                "SELECT status FROM hotspots WHERE id = $1", hotspot_id
            )

            if not record:
                raise ValueError(f"热点 {hotspot_id} 不存在")

            old_status = record["status"]

            # 更新为 second_stage_rejected 状态并记录拒绝原因和时间
            await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    second_stage_rejection_reason = $2,
                    second_stage_rejected_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $3
                """,
                HotspotStatus.SECOND_STAGE_REJECTED.value,
                rejection_reason,
                hotspot_id,
            )

            return {
                "success": True,
                "message": f"热点已在第二阶段被拒绝: {rejection_reason}",
                "hotspot_id": hotspot_id,
                "old_status": old_status,
            }

    async def update_outdated_pending_validation_hotspots(
        self, cutoff_datetime: datetime
    ) -> int:
        """
        更新三天前仍为 pending_validation 状态的热点为 rejected

        Args:
            cutoff_datetime: 截止时间，早于此时间创建的 pending_validation 热点将被拒绝

        Returns:
            更新的热点数量
        """
        async with session.pg_pool.acquire() as conn:
            # 更新所有在 cutoff_datetime 之前创建且仍为 pending_validation 状态的热点
            result = await conn.execute(
                """
                UPDATE hotspots
                SET status = $1,
                    is_filtered = TRUE,
                    filter_reason = $2,
                    filtered_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE status = $3
                  AND created_at < $4
                """,
                HotspotStatus.REJECTED.value,
                "超时未更新",
                HotspotStatus.PENDING_VALIDATION.value,
                cutoff_datetime,
            )

            # 从 result 字符串中提取更新数量，格式类似 "UPDATE 5"
            updated_count = int(result.split()[-1]) if result else 0
            return updated_count


# 全局热点服务实例
hotspot_service = HotspotService()
