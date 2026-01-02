from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import aiomysql
from datetime import datetime

from app.schemas.account import (
    AccountCreateRequest,
    AccountUpdateRequest,
    AccountResponse,
    AccountListResponse
)
from app.schemas.common import APIResponse
from app.dependencies import get_db

router = APIRouter()


@router.post("", response_model=APIResponse[AccountResponse])
async def create_account(
    request: AccountCreateRequest,
    conn: aiomysql.Connection = Depends(get_db)
):
    """
    创建账号配置

    - **account_name**: 账号名称
    - **platform_name**: 平台名称 (xhs|dy|ks|bili|wb|tieba|zhihu)
    - **cookies**: 登录 cookies

    新创建的账号默认状态为 0（正常）
    """
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            sql = """
                INSERT INTO crawler_cookies_account
                (account_name, platform_name, cookies, status)
                VALUES (%s, %s, %s, 0)
            """
            await cursor.execute(sql, (
                request.account_name,
                request.platform_name,
                request.cookies
            ))
            account_id = cursor.lastrowid

            # 查询刚创建的账号
            await cursor.execute(
                "SELECT * FROM crawler_cookies_account WHERE id = %s",
                (account_id,)
            )
            account = await cursor.fetchone()

            return APIResponse(
                code=0,
                message="Account created successfully",
                data=AccountResponse(**account)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")


@router.get("", response_model=APIResponse[AccountListResponse])
async def list_accounts(
    platform: Optional[str] = Query(None, description="平台名称"),
    status: Optional[int] = Query(None, description="账号状态 (0:正常, -1:失效)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    conn: aiomysql.Connection = Depends(get_db)
):
    """
    查询账号列表

    支持按平台和状态过滤，分页返回
    """
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 构建查询条件
            where_clauses = []
            params = []

            if platform:
                where_clauses.append("platform_name = %s")
                params.append(platform)
            if status is not None:
                where_clauses.append("status = %s")
                params.append(status)

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM crawler_cookies_account WHERE {where_sql}"
            await cursor.execute(count_sql, params)
            total_result = await cursor.fetchone()
            total = total_result['total']

            # 查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM crawler_cookies_account
                WHERE {where_sql}
                ORDER BY update_time DESC
                LIMIT %s OFFSET %s
            """
            await cursor.execute(data_sql, params + [page_size, offset])
            accounts = await cursor.fetchall()

            return APIResponse(
                code=0,
                message="success",
                data=AccountListResponse(
                    total=total,
                    page=page,
                    page_size=page_size,
                    items=[AccountResponse(**acc) for acc in accounts]
                )
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list accounts: {str(e)}")


@router.get("/{account_id}", response_model=APIResponse[AccountResponse])
async def get_account(
    account_id: int,
    conn: aiomysql.Connection = Depends(get_db)
):
    """获取单个账号详情"""
    try:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM crawler_cookies_account WHERE id = %s",
                (account_id,)
            )
            account = await cursor.fetchone()

            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            return APIResponse(
                code=0,
                message="success",
                data=AccountResponse(**account)
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{account_id}", response_model=APIResponse[dict])
async def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    conn: aiomysql.Connection = Depends(get_db)
):
    """
    更新账号配置

    - **account_name**: 账号名称(可选)
    - **cookies**: 新的 cookies(可选)
    - **status**: 账号状态(可选,0:正常, -1:失效)
    """
    try:
        async with conn.cursor() as cursor:
            update_fields = []
            params = []

            if request.account_name is not None:
                update_fields.append("account_name = %s")
                params.append(request.account_name)
            if request.cookies is not None:
                update_fields.append("cookies = %s")
                params.append(request.cookies)
            if request.status is not None:
                update_fields.append("status = %s")
                params.append(request.status)
                # 如果设置为失效状态，记录失效时间
                if request.status == -1:
                    update_fields.append("invalid_timestamp = %s")
                    params.append(int(datetime.now().timestamp()))

            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")

            params.append(account_id)
            sql = f"""
                UPDATE crawler_cookies_account
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            await cursor.execute(sql, params)

            return APIResponse(
                code=0,
                message="Account updated successfully",
                data={"account_id": account_id}
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update account: {str(e)}")


@router.delete("/{account_id}", response_model=APIResponse[dict])
async def delete_account(
    account_id: int,
    conn: aiomysql.Connection = Depends(get_db)
):
    """
    删除账号配置

    警告：此操作不可逆
    """
    try:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM crawler_cookies_account WHERE id = %s",
                (account_id,)
            )
            return APIResponse(
                code=0,
                message="Account deleted successfully",
                data={"account_id": account_id}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")
