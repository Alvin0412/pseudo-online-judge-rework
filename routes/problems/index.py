from fastapi import APIRouter, Query, Path, Depends
from models.problem import Problem
from models.test_sample import TestSample
from typing import Annotated, List
from .schemas import ProblemSchema, AddProblemRequest, \
    GetProblemResponse, TestSampleSchema, AddProblemResponse, ProblemListRequest
from utils.index import digitalize_problem_id, cheerful_messages

import database
import math
import random

router = APIRouter(
    prefix="/problems"
)
PAGE_SIZE_LIMIT = 200


@router.get("/problem/{pid}/has_test_data")
async def has_test_samples(
        pid: Annotated[str, Path()],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    pid = digitalize_problem_id(pid)
    result = False
    if pid is None:
        return {"error": "Invalid pid!"}
    try:
        samples = session.query(TestSample).where(TestSample.problem_id == pid).all()
        if len(samples) > 0:
            result = True
    except Exception as e:
        return {
            "result": "failed",
            "details": e.args
        }
    return {
        "exists": result
    }


@router.get('/problem/exists')
async def is_problem_exist(
        pid: Annotated[str, Query(...)],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    pid = digitalize_problem_id(pid)
    result = False
    if pid is None:
        return {"error": "Invalid pid!"}
    try:
        obj = session.query(Problem).get(pid)
        if obj is not None:
            result = True
    except Exception as e:
        return {
            "result": "failed",
            "details": e
        }
    return {
        "exists": result
    }


@router.post('/list')
async def get_problem_list(
        page_config: ProblemListRequest,
        session: Annotated[database.Session, Depends(database.make_session)]
):
    offset = page_config.page_size * (page_config.page_num - 1)
    query = session.query(Problem).offset(offset).limit(page_config.page_size)
    problem_list = query.all()
    total_records = session.query(Problem).count()
    total_pages = math.ceil(total_records / page_config.page_size)

    return {
        "total_pages": total_pages,
        "current_page": page_config.page_num,
        "page_size": page_config.page_size,
        "store": [{
            "pid": problem.pid,
            "title": problem.title,
            "source": problem.source,
            "difficulty": problem.difficulty,
            "labels": problem.labels,
            "msg": random.choice(cheerful_messages)
        } for problem in problem_list]
    }


@router.post('/add_problem', response_model=AddProblemResponse)
async def add_problem(
        problem: ProblemSchema,
        test_samples: List[TestSampleSchema],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    try:
        orm_problem = Problem(
            **problem.model_dump()
        )
        session.add(orm_problem)
        session.flush()
        new_pid = orm_problem.pid
        for i, sample_data in enumerate(test_samples):
            test_sample = TestSample(
                num=i + 1,
                input=sample_data.input,
                output=sample_data.output,
                problem_id=new_pid
            )
            session.add(test_sample)
        session.commit()
    except Exception as e:
        session.rollback()
        return {
            "result": "failed",
            "details": e
        }
    return {
        "result": "success",
        "code": "",
        "message": "Problem and test samples added successfully"
    }


# TODO: sort out a way to make generic response model to include both success/failed necessary information
@router.get('/problem/{pid}')
async def get_problem(
        pid: Annotated[str, Path(title="the pid of a problem")],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    # prob: Problem = Problem.query.where(Problem.pid == pid).one_or_none()

    pid = digitalize_problem_id(pid)
    if pid is None:
        return {"error": "Invalid pid!"}
    prob: Problem = session.query(Problem).get(pid)
    resp = {}
    if prob is None:
        return resp | {"result": "None"}
    if prob.defunct:
        return resp | {"result": "defunct problem"}
    # TODO: synchronise the request handling part of frontend to adapt new return value
    return {
        "pid": prob.pid,
        "title": prob.title,
        "description": prob.description,
        "input": prob.input,
        "output": prob.output,
        "sample_input": prob.sample_input,
        "sample_output": prob.sample_output,
        "source": prob.source,
        "labels": prob.labels,
        "time_limit": prob.time_limit,
        "memory_limit": prob.memory_limit,
        "accepted": prob.accepted,
        "submit": prob.submit,
        "solved": prob.solved,
        "hint": prob.hint
    }
