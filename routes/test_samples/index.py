from fastapi import APIRouter, Query, Path, Depends, HTTPException, Body, status
from models.problem import Problem
from models.test_sample import TestSample
from typing import Annotated, List
from .schemas import GetAllTestSamplesFromPidResponse, TestSampleSchema,\
    RawTestSampleSchema, CreateTestSampleFromPid
from utils.index import digitalize_problem_id, cheerful_messages

import database
import math
import random

router = APIRouter(
    prefix="/test_samples"
)


@router.get("/test_sample/{sample_id}", response_model=TestSampleSchema)
async def get_test_sample_from_sid(
        sample_id: Annotated[int, Path()],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    try:
        sample = session.query(TestSample).where(TestSample.sid == sample_id).one()
    except Exception as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"error": e.args})
    return {
        "sample": {
            "input": sample.input,
            "output": sample.output,
            "num": sample.num
        }
    }

@router.get("/{pid}/all", response_model=GetAllTestSamplesFromPidResponse)
async def get_all_test_samples_from_pid(
        pid: Annotated[str, Path()],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    try:
        pid = digitalize_problem_id(pid)
        problem = session.query(Problem).where(Problem.pid == pid).one_or_none()
        samples = problem.samples
    except Exception as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"error": e.args})
    return {
        "samples": [
            {
                "input": sample.input,
                "output": sample.output,
                "num": sample.num
            }
            for sample in samples
        ]
    }


@router.get("/{pid}/{sample_num}",response_model=TestSampleSchema)
async def get_test_sample_from_pid(
        pid: Annotated[str, Path()],
        sample_num: Annotated[int, Path()],
        session: Annotated[database.Session, Depends(database.make_session)]
):
    try:
        pid = digitalize_problem_id(pid)
        sample = session.query(TestSample).where(TestSample.problem_id == pid,
                                                 TestSample.num == sample_num).one_or_none()
    except Exception as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"error": e.args})
    return {
        "sample": {
            "input": sample.input,
            "output": sample.output,
            "num": sample.num
        }
    }


# TODO: add unique-value verification here
@router.post("/test_sample", response_model=CreateTestSampleFromPid, status_code=status.HTTP_201_CREATED)
async def create_test_sample_from_pid(
        pid: Annotated[str, Body(...)],
        test_sample: RawTestSampleSchema,
        session: Annotated[database.Session, Depends(database.make_session)]
):
    try:
        pid = digitalize_problem_id(pid)
        if pid is None:
            raise ValueError("Invalid pid!")
        problem = session.query(Problem).where(Problem.pid == pid).one_or_none()
        if problem is None:
            raise ValueError("Invalid problem!")
        sample = TestSample(**{
            "input": test_sample.input,
            "output": test_sample.output,
            "problem_id": pid,
            "num": len(problem.samples)
        })
        session.add(sample)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, {"Success": False, "error": e.args})
    return {"success": True}

