import time
from celery import Celery
from services.config import REDIS_SERVER_IP, REDIS_PORT

broker_url = f"redis://{REDIS_SERVER_IP}:{REDIS_PORT}/{0}"

app = Celery('services.main',
             broker=broker_url,
             backend=broker_url)

def start_celery(concurrency=10):
    argv = [
        'worker',
        '--loglevel=INFO',
        '--pool=solo',
        f'--concurrency={concurrency}'
    ]
    app.autodiscover_tasks()
    app.worker_main(argv)


if __name__ == "__main__":
    start_celery()
    from utils.logger import logger

# 1. 需要一个cycle来根据条件来handle各种事件 beater
# 2. 需要伪代码执行器 来管理代码执行资源和流程 作为worker
# 3. 需要管理伪代码执行器的manager 作为与beater交互的中枢
