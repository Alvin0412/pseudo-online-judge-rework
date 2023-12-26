from pydantic import BaseModel, Field
from typing import List, Optional


# TODO: (Reminder) solve the naming issue
class SourceCodeSchema(BaseModel):
    language: str = "pseudocode"
    code: str
    pid: str

