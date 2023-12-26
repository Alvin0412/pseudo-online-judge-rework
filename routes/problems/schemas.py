from pydantic import BaseModel, Field
from typing import List, Optional


# TODO: check these definition is correct or not
class ProblemSchema(BaseModel):
    title: str
    description: str
    input: str
    output: str
    sample_input: str
    sample_output: str
    labels: Optional[str] = None
    source: Optional[str] = None
    hint: Optional[str] = None
    difficulty: str = 'easy'
    time_limit: str = '1'
    memory_limit: str = '16'
    accepted: int = 0
    submit: int = 0
    solved: int = 0
    defunct: bool = False


class TestSampleSchema(BaseModel):
    input: str
    output: str


class AddProblemRequest(BaseModel):
    problem: ProblemSchema
    test_samples: List[TestSampleSchema]


class GetProblemResponse(ProblemSchema):
    pid: int | None


class AddProblemResponse(ProblemSchema):
    pid: int | None

    class Config:
        from_attributes = True


class ProblemListRequest(BaseModel):
    page_size: int
    page_num: int
