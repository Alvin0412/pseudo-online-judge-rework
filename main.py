from utils.logger import logger

from fastapi import FastAPI
from database import Base, engine
from models import user, test_sample, problem, runtime_info, source_code, submission
from routes.problems.index import router as problems_router
from routes.test_samples.index import router as test_samples_router
from routes.submissions.index import router as submissions_router
from routes.auth.index import router as auth_router

# TODO:  2. error handling mechanism

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(test_samples_router)
app.include_router(submissions_router)

