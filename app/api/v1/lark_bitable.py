from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import (
    ListAppTableRecordRequest,
    ListAppTableRecordResponse,
)
from app.schemas.common import APIResponse
from app.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class GetBitableRequest(BaseModel):
    """获取多维表格请求参数"""

    app_token: str  # 多维表格的 app_token
    table_id: str  # 数据表的 table_id
    page_size: int = 500  # 每页记录数，默认 500


def get_lark_client() -> lark.Client:
    """创建飞书客户端"""
    if not settings.LARK_APP_ID or not settings.LARK_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="飞书配置缺失，请设置 LARK_APP_ID 和 LARK_APP_SECRET 环境变量",
        )

    return (
        lark.Client.builder()
        .app_id(settings.LARK_APP_ID)
        .app_secret(settings.LARK_APP_SECRET)
        .build()
    )


@router.post("/bitable/records")
async def get_bitable_records(request: GetBitableRequest):
    """
    获取飞书多维表格数据

    - **app_token**: 多维表格的唯一标识，可以从多维表格 URL 中获取
      - 例如：https://xxx.feishu.cn/base/YourAppToken
    - **table_id**: 数据表的唯一标识，可以从数据表 URL 中获取
      - 例如：https://xxx.feishu.cn/base/YourAppToken?table=YourTableId
    - **page_size**: 每页记录数，默认 500，最大 500
    """
    try:
        client = get_lark_client()

        logger.info(
            f"开始获取飞书多维表格数据: app_token={request.app_token}, "
            f"table_id={request.table_id}, page_size={request.page_size}"
        )

        all_records = []
        page_token = None

        # 分页获取所有记录
        while True:
            # 构建请求
            req_builder = (
                ListAppTableRecordRequest.builder()
                .app_token(request.app_token)
                .table_id(request.table_id)
                .page_size(request.page_size)
            )

            # 只在有 page_token 时才设置
            if page_token:
                req_builder = req_builder.page_token(page_token)

            req = req_builder.build()

            # 发起请求
            response: ListAppTableRecordResponse = (
                client.bitable.v1.app_table_record.list(req)
            )

            # 检查响应
            if not response.success():
                error_msg = f"获取飞书多维表格数据失败: code={response.code}, msg={response.msg}"
                logger.error(error_msg)

                # 提供更友好的错误提示
                if response.code == 1254070:
                    error_msg = "权限不足，请确保飞书应用已添加 'bitable:app' 或 'bitable:app:readonly' 权限，并将应用添加到多维表格的协作者中"
                elif response.code == 99991400:
                    error_msg = "app_token 或 table_id 无效，请检查多维表格链接是否正确"

                raise HTTPException(status_code=500, detail=error_msg)

            # 收集数据
            if response.data and response.data.items:
                for item in response.data.items:
                    record = {
                        "record_id": item.record_id,
                        "fields": item.fields if item.fields else {},
                    }
                    all_records.append(record)

                logger.info(f"获取到 {len(response.data.items)} 条记录")

            # 检查是否还有下一页
            if not response.data.has_more:
                break

            page_token = response.data.page_token

        logger.info(
            f"成功获取飞书多维表格数据: app_token={request.app_token}, "
            f"table_id={request.table_id}, total={len(all_records)}"
        )

        return APIResponse(
            code=0,
            message="success",
            data={"total": len(all_records), "records": all_records},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取飞书多维表格数据异常: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"获取飞书多维表格数据异常: {str(e)}"
        )
