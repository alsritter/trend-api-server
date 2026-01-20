from typing import List, Optional, Dict, Any
from app.db import session
from app.schemas.hotspot import ClusterInfo, PlatformStat
import json
from datetime import datetime


class ClusterService:
    """聚簇服务类 - 提供聚簇管理的完整业务逻辑"""

    def __init__(self):
        """初始化聚簇服务"""
        pass

    async def list_clusters(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[List[str]] = None,
        exclude_status: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        列出所有聚簇

        Args:
            page: 页码，从1开始
            page_size: 每页数量
            status: 热点状态列表过滤
            exclude_status: 排除的热点状态列表
            platforms: 平台列表过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            keyword: 搜索关键词，用于搜索聚簇名称和关键词

        Returns:
            包含 items 和 total 的字典
        """
        async with session.pg_pool.acquire() as conn:
            # 构建查询条件
            conditions = []
            params = []
            param_counter = 1

            if status:
                # 状态过滤：支持多个状态
                status_placeholders = ",".join(
                    [f"${param_counter + i}" for i in range(len(status))]
                )
                conditions.append(f"h.status IN ({status_placeholders})")
                params.extend(status)
                param_counter += len(status)

            if exclude_status:
                # 排除状态：使用 NOT IN
                exclude_placeholders = ",".join(
                    [f"${param_counter + i}" for i in range(len(exclude_status))]
                )
                conditions.append(f"h.status NOT IN ({exclude_placeholders})")
                params.extend(exclude_status)
                param_counter += len(exclude_status)

            if platforms:
                # 平台过滤：使用 JSONB 操作符检查 platforms 数组中是否存在指定平台
                # platforms 是一个 JSONB 数组，每个元素包含 platform 字段
                # 使用 EXISTS 子查询检查数组中是否有匹配的 platform
                platform_conditions = " OR ".join(
                    [
                        f"EXISTS (SELECT 1 FROM jsonb_array_elements(h.platforms) AS p WHERE p->>'platform' = ${param_counter + i})"
                        for i in range(len(platforms))
                    ]
                )
                conditions.append(f"({platform_conditions})")
                params.extend(platforms)
                param_counter += len(platforms)

            if start_time:
                conditions.append(f"h.updated_at >= ${param_counter}")
                # 解析 ISO 格式时间字符串，去掉时区信息以匹配数据库的 TIMESTAMP 类型
                params.append(datetime.fromisoformat(start_time.replace("Z", "")))
                param_counter += 1

            if end_time:
                conditions.append(f"h.updated_at <= ${param_counter}")
                # 解析 ISO 格式时间字符串，去掉时区信息以匹配数据库的 TIMESTAMP 类型
                params.append(datetime.fromisoformat(end_time.replace("Z", "")))
                param_counter += 1

            if keyword:
                # 关键词搜索：搜索聚簇名称或关键词列表
                conditions.append(
                    f"(c.cluster_name ILIKE ${param_counter} OR c.keywords::text ILIKE ${param_counter})"
                )
                params.append(f"%{keyword}%")
                param_counter += 1

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # 先查询总数
            count_query = f"""
                SELECT COUNT(DISTINCT c.id)
                FROM hotspot_clusters c
                LEFT JOIN hotspots h ON h.cluster_id = c.id
                {where_clause}
            """
            total_count = await conn.fetchval(count_query, *params)

            # 计算分页偏移量
            offset = (page - 1) * page_size

            # 查询聚簇及其热点的平台统计
            query = f"""
                SELECT
                    c.id,
                    c.cluster_name,
                    c.member_count,
                    c.keywords,
                    c.selected_hotspot_id,
                    c.created_at,
                    c.updated_at,
                    -- 聚合聚簇中所有热点的状态
                    COALESCE(
                        json_agg(DISTINCT h.status) FILTER (WHERE h.status IS NOT NULL),
                        '[]'::json
                    ) as statuses,
                    -- 获取聚簇中最晚的更新时间
                    COALESCE(MAX(h.updated_at), c.updated_at) as last_hotspot_update,
                    -- 聚合平台统计信息
                    COALESCE(
                        (
                            SELECT json_agg(platform_stat)
                            FROM (
                                SELECT
                                    (platform_info->>'platform') as platform,
                                    COUNT(*) as count
                                FROM hotspots h2
                                CROSS JOIN LATERAL jsonb_array_elements(h2.platforms::jsonb) as platform_info
                                WHERE h2.cluster_id = c.id
                                GROUP BY (platform_info->>'platform')
                            ) as platform_stat
                        ),
                        '[]'::json
                    ) as platforms
                FROM hotspot_clusters c
                LEFT JOIN hotspots h ON h.cluster_id = c.id
                {where_clause}
                GROUP BY c.id, c.cluster_name, c.member_count, c.keywords, c.selected_hotspot_id, c.created_at, c.updated_at
                ORDER BY COALESCE(MAX(h.updated_at), c.updated_at) DESC
                LIMIT ${param_counter} OFFSET ${param_counter + 1}
            """
            params.extend([page_size, offset])

            records = await conn.fetch(query, *params)

            result = []
            for r in records:
                # 解析平台统计数据
                platforms_data = r["platforms"]
                if isinstance(platforms_data, str):
                    platforms_data = json.loads(platforms_data)

                platform_stats = (
                    [
                        PlatformStat(platform=p["platform"], count=p["count"])
                        for p in platforms_data
                    ]
                    if platforms_data
                    else []
                )

                result.append(
                    ClusterInfo(
                        id=r["id"],
                        cluster_name=r["cluster_name"],
                        member_count=r["member_count"],
                        keywords=json.loads(r["keywords"])
                        if isinstance(r["keywords"], str)
                        else r["keywords"],
                        selected_hotspot_id=r["selected_hotspot_id"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        statuses=r["statuses"]
                        if isinstance(r["statuses"], list)
                        else json.loads(r["statuses"]),
                        last_hotspot_update=r["last_hotspot_update"],
                        platforms=platform_stats,
                    )
                )

            return {"items": result, "total": total_count}

    async def get_cluster_by_id(self, cluster_id: int) -> Optional[ClusterInfo]:
        """
        根据ID获取聚簇详情

        Args:
            cluster_id: 聚簇ID

        Returns:
            聚簇详情或 None
        """
        async with session.pg_pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                SELECT
                    c.id,
                    c.cluster_name,
                    c.member_count,
                    c.keywords,
                    c.selected_hotspot_id,
                    c.created_at,
                    c.updated_at,
                    -- 聚合聚簇中所有热点的状态
                    COALESCE(
                        json_agg(DISTINCT h.status) FILTER (WHERE h.status IS NOT NULL),
                        '[]'::json
                    ) as statuses,
                    -- 获取聚簇中最晚的更新时间
                    COALESCE(MAX(h.updated_at), c.updated_at) as last_hotspot_update,
                    -- 聚合平台统计信息
                    COALESCE(
                        (
                            SELECT json_agg(platform_stat)
                            FROM (
                                SELECT
                                    (platform_info->>'platform') as platform,
                                    COUNT(*) as count
                                FROM hotspots h2
                                CROSS JOIN LATERAL jsonb_array_elements(h2.platforms::jsonb) as platform_info
                                WHERE h2.cluster_id = c.id
                                GROUP BY (platform_info->>'platform')
                            ) as platform_stat
                        ),
                        '[]'::json
                    ) as platforms
                FROM hotspot_clusters c
                LEFT JOIN hotspots h ON h.cluster_id = c.id
                WHERE c.id = $1
                GROUP BY c.id, c.cluster_name, c.member_count, c.keywords, c.selected_hotspot_id, c.created_at, c.updated_at
                """,
                cluster_id,
            )

            if not r:
                return None

            # 解析平台统计数据
            platforms_data = r["platforms"]
            if isinstance(platforms_data, str):
                platforms_data = json.loads(platforms_data)

            platform_stats = (
                [
                    PlatformStat(platform=p["platform"], count=p["count"])
                    for p in platforms_data
                ]
                if platforms_data
                else []
            )

            return ClusterInfo(
                id=r["id"],
                cluster_name=r["cluster_name"],
                member_count=r["member_count"],
                keywords=json.loads(r["keywords"])
                if isinstance(r["keywords"], str)
                else r["keywords"],
                selected_hotspot_id=r["selected_hotspot_id"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                statuses=r["statuses"]
                if isinstance(r["statuses"], list)
                else json.loads(r["statuses"]),
                last_hotspot_update=r["last_hotspot_update"],
                platforms=platform_stats,
            )

    async def create_cluster(
        self, cluster_name: str, hotspot_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        创建新聚簇

        Args:
            cluster_name: 聚簇名称
            hotspot_ids: 初始热点ID列表（可选）

        Returns:
            包含 success, cluster_id, message 的字典
        """
        async with session.pg_pool.acquire() as conn:
            async with conn.transaction():
                # 如果提供了热点ID，验证它们存在
                keywords = []
                member_count = 0

                if hotspot_ids:
                    # 获取热点信息
                    hotspots = await conn.fetch(
                        """
                        SELECT id, keyword FROM hotspots
                        WHERE id = ANY($1)
                        """,
                        hotspot_ids,
                    )

                    if len(hotspots) != len(hotspot_ids):
                        raise ValueError("部分热点ID不存在")

                    keywords = [h["keyword"] for h in hotspots]
                    member_count = len(hotspots)

                # 创建聚簇
                cluster_id = await conn.fetchval(
                    """
                    INSERT INTO hotspot_clusters (cluster_name, member_count, keywords)
                    VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    cluster_name,
                    member_count,
                    json.dumps(keywords, ensure_ascii=False),
                )

                # 如果提供了热点ID，更新它们的cluster_id
                if hotspot_ids:
                    await conn.execute(
                        """
                        UPDATE hotspots
                        SET cluster_id = $1, updated_at = NOW()
                        WHERE id = ANY($2)
                        """,
                        cluster_id,
                        hotspot_ids,
                    )

                return {
                    "success": True,
                    "cluster_id": cluster_id,
                    "message": f"聚簇创建成功，ID: {cluster_id}",
                }

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
        async with session.pg_pool.acquire() as conn:
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
        async with session.pg_pool.acquire() as conn:
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
        async with session.pg_pool.acquire() as conn:
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
        async with session.pg_pool.acquire() as conn:
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
        async with session.pg_pool.acquire() as conn:
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


# 全局聚簇服务实例
cluster_service = ClusterService()
