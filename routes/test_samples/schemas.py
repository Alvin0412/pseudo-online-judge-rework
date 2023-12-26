from pydantic import BaseModel, Field
from typing import List, Optional


class RawTestSampleSchema(BaseModel):
    input: str
    output: str

class TestSampleSchema(RawTestSampleSchema):
    num: int

    class Config:
        from_attributes = True


class GetAllTestSamplesFromPidResponse(BaseModel):
    samples: Optional[List[TestSampleSchema]]

class GetTestSampleFromPidResponse(BaseModel):
    sample: TestSampleSchema | None

class CreateTestSampleFromPid(BaseModel):
    success: bool

