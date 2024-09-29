from utils.logger import logger

from fastapi import FastAPI
from database import Base, engine
from models import user, test_sample, problem, runtime_info, source_code, submission
from routes.problems.index import router as problems_router
from routes.test_samples.index import router as test_samples_router
from routes.submissions.index import router as submissions_router
from routes.auth.index import router as auth_router
import utils.dependencies as dependencies  # strange

import uvicorn

dependencies.start_redis_server()
dependencies.redis_pool = dependencies.create_redis()

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth_router)
app.include_router(problems_router)
app.include_router(test_samples_router)
app.include_router(submissions_router)

# directly run within main file
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8251,
        reload=True,
        workers=5
    )
