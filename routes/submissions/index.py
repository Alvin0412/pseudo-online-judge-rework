from fastapi import APIRouter, Query, Path, Depends
from typing import Annotated, List
import database

router = APIRouter(
    prefix="/submission"
)


@router.post("/")
async def create_submission(

    session: Annotated[database.Session, Depends(database.make_session)]
):
    ...
