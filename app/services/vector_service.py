from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from app.config import settings
from app.db import vector_session


class VectorService:
    """向量服务类 - 提供向量的添加、召回、删除功能"""

    # 当前使用的向量模型
    EMBEDDING_MODEL = "qwen3-embedding-8b"

    def __init__(self):
        """初始化向量服务"""
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """
        使用 OpenAI 生成文本向量

        Args:
            text: 要生成向量的文本

        Returns:
            向量数组
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")

    async def add_vector(
        self,
        text: str,
        collection_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        添加向量

        Args:
            text: 要向量化的文本
            collection_id: 集合ID，用于区分不同的聚合
            metadata: 元数据（JSON格式），存储与该向量相关的扩展信息

        Returns:
            插入的向量 ID
        """
        # 生成向量
        vector = await self.generate_embedding(text)

        # 插入数据库
        async with vector_session.pg_pool.acquire() as conn:
            record_id = await conn.fetchval(
                """
                INSERT INTO modeldata (vector, collection_id, content, metadata, model_name)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                vector,
                collection_id,
                text,
                metadata,
                self.EMBEDDING_MODEL,
            )
            return record_id

    async def search_vectors(
        self,
        query_text: str,
        collection_id: Optional[str] = None,
        top_k: int = 10,
        threshold: Optional[float] = None,
        ef_search: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        向量召回（相似性搜索）

        Args:
            query_text: 查询文本
            collection_id: 可选的集合ID过滤
            top_k: 返回最相似的前 k 个结果
            threshold: 可选的相似度阈值（0-1），只返回相似度大于此值的结果
            ef_search: HNSW 索引搜索参数，值越大搜索越精确但速度越慢，默认 100

        Returns:
            相似向量列表，包含 id, collection_id, metadata, similarity, createtime
        """
        # 生成查询向量
        query_vector = await self.generate_embedding(query_text)

        # 确保 ef_search 至少为 1
        ef_search = max(ef_search, 1)

        async with vector_session.pg_pool.acquire() as conn:
            # 在事务中执行所有操作
            async with conn.transaction():
                # 设置 HNSW 搜索参数（在事务内部）
                await conn.execute(f"SET LOCAL hnsw.ef_search = {ef_search}")

                # 构建查询
                # 使用内积运算符 <#> （负内积）
                # 对于归一化向量（如 OpenAI embeddings），内积 = 余弦相似度
                # similarity = -(vector <#> query_vector) 将负内积转为正相似度 [0, 1]
                params = [query_vector]
                param_idx = 2  # 从 $2 开始，$1 是 query_vector
                conditions = []

                # 只搜索相同模型的向量
                conditions.append(f"model_name = ${param_idx}")
                params.append(self.EMBEDDING_MODEL)
                param_idx += 1

                # 添加集合ID过滤
                if collection_id:
                    conditions.append(f"collection_id = ${param_idx}")
                    params.append(collection_id)
                    param_idx += 1

                # 添加相似度阈值过滤
                # vector <#> $1 < -threshold （因为 <#> 返回负内积）
                if threshold is not None:
                    conditions.append(f"(vector <#> $1) < -{threshold}")

                # 构建完整查询
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                query = f"""
                    SELECT
                        id,
                        collection_id,
                        content,
                        metadata,
                        model_name,
                        createtime,
                        (vector <#> $1) * -1 as similarity
                    FROM modeldata
                    WHERE {where_clause}
                    ORDER BY similarity DESC
                    LIMIT {top_k}
                """

                # 执行查询
                records = await conn.fetch(query, *params)
                return [
                    {
                        "id": record["id"],
                        "collection_id": record["collection_id"],
                        "content": record["content"],
                        "metadata": record["metadata"],
                        "model_name": record["model_name"],
                        "similarity": float(record["similarity"]),
                        "createtime": record["createtime"].isoformat(),
                    }
                    for record in records
                ]

    async def delete_vector(self, vector_id: int) -> bool:
        """
        删除指定ID的向量

        Args:
            vector_id: 向量ID

        Returns:
            是否删除成功
        """
        async with vector_session.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM modeldata WHERE id = $1",
                vector_id,
            )
            # result 格式为 "DELETE n"，n 是删除的行数
            deleted_count = int(result.split()[-1])
            return deleted_count > 0

    async def delete_vectors_by_collection(self, collection_id: str) -> int:
        """
        删除指定集合的所有向量

        Args:
            collection_id: 集合ID

        Returns:
            删除的向量数量
        """
        async with vector_session.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM modeldata WHERE collection_id = $1",
                collection_id,
            )
            deleted_count = int(result.split()[-1])
            return deleted_count

    async def get_vector_by_id(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取向量信息

        Args:
            vector_id: 向量ID

        Returns:
            向量信息，包含 id, collection_id, metadata, createtime
        """
        async with vector_session.pg_pool.acquire() as conn:
            record = await conn.fetchrow(
                """
                SELECT id, collection_id, content, metadata, model_name, createtime
                FROM modeldata
                WHERE id = $1
                """,
                vector_id,
            )
            if record:
                return {
                    "id": record["id"],
                    "collection_id": record["collection_id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "model_name": record["model_name"],
                    "createtime": record["createtime"].isoformat(),
                }
            return None

    async def list_collections(self) -> List[Dict[str, Any]]:
        """
        列出所有集合及其完整的向量数据

        Returns:
            集合列表，每个集合包含 collection_id 和 vectors（向量列表）
        """
        async with vector_session.pg_pool.acquire() as conn:
            # 获取所有向量数据
            records = await conn.fetch(
                """
                SELECT id, collection_id, content, metadata, model_name, createtime
                FROM modeldata
                ORDER BY collection_id, createtime DESC
                """
            )

            # 按 collection_id 分组
            collections_dict: Dict[str, List[Dict[str, Any]]] = {}
            for record in records:
                collection_id = record["collection_id"]
                if collection_id not in collections_dict:
                    collections_dict[collection_id] = []

                collections_dict[collection_id].append(
                    {
                        "id": record["id"],
                        "content": record["content"],
                        "metadata": record["metadata"],
                        "model_name": record["model_name"],
                        "createtime": record["createtime"].isoformat(),
                    }
                )

            # 转换为列表格式
            return [
                {
                    "collection_id": collection_id,
                    "count": len(vectors),
                    "vectors": vectors,
                }
                for collection_id, vectors in collections_dict.items()
            ]


# 全局向量服务实例
vector_service = VectorService()
