import typing
import uuid

import pydantic
from fastapi import APIRouter
from starlette.websockets import WebSocket
from .schemas import ConnectionData, ReceivedData
from utils.logger import logger
from typing import Type

import database

router = APIRouter(
    prefix="/runner"
)

"""
1. 前端ws连接后端，获取client_id
2. 前端等待后端发送正在执行
3. 后端会不断的发送程序输出的数据
4. 前端会向后端发送输入参数
"""


# The ONLY VALID data format for client socket to transfer is JSON
async def parse_json(model_type: Type[pydantic.BaseModel], json_data: dict) -> pydantic.BaseModel | Exception:
    try:
        message = model_type.from_orm(json_data)
    except pydantic.ValidationError as e:
        return e
    return message


@router.websocket("/runner/start")
async def connection(socket: WebSocket):
    await socket.accept()
    connection_data = ConnectionData(
        connection_id=uuid.uuid4(),
    )

    await socket.send_text(  # To send data needed for connection establishment
        connection_data.model_dump_json())  # assume that the .send_json method can't deserialize uuid
    # 0. 确保redis队列正确
    # 1. 启动code_manager
    while True:
        message: ReceivedData | Exception = await parse_json(ReceivedData, await socket.receive_json())
        if isinstance(message, Exception):
            logger.error(message)
            continue
