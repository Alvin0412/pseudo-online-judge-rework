from pydantic import BaseModel, UUID4
from typing import List, Optional, Literal


class ConnectionData(BaseModel):
    connection_id: UUID4


class OutputData(BaseModel):
    output: str


class ReceivedData(BaseModel):
    type: Literal["input", "operation"]
    data: Optional[str]
    operation: Optional[str]

    class Config:
        from_attributes = True
