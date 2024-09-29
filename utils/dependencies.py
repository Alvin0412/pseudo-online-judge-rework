import pathlib

import redis
from .settings import REDIS_HOST_PORT, SERVER_IP_ADDRESS, REDIS_DEFAULT_DB_NUM
from utils.logger import logger

import subprocess
import signal
import atexit


def cleanup_process(process):
    """终止并清理后台进程"""
    if process:
        logger.info("Terminating the Redis server...")
        process.send_signal(signal.SIGTERM)  # 发送终止信号
        process.wait()  # 等待进程终止
        logger.info("Redis server has been terminated.")
        return True
    return False


def start_redis_server(redis_config_path=""):
    # 返回的process的生命周期和资源回收会被管理
    process = None
    try:
        if not pathlib.Path(redis_config_path).is_file():
            logger.warning("Invalid config file path: {}".format(redis_config_path))
            redis_config_path = ""
        process = subprocess.Popen(['redis-server', redis_config_path])
        logger.info("Redis server successfully started.")

        atexit.register(cleanup_process, process)
    except Exception as e:
        logger.error(f"Failed to start Redis server: {repr(e)}")
        # 如果进程已启动但后续操作失败，需要清理资源
        if process:
            process.terminate()
            process.wait()  # 等待进程终止
    return process


redis_pool = None  # NOTE: this variable is defined for reuse, which means you SHOULD assign a initial value in main program


def create_redis():
    return redis.ConnectionPool(
        host=SERVER_IP_ADDRESS,
        port=REDIS_HOST_PORT,
        db=REDIS_DEFAULT_DB_NUM,
        decode_responses=True
    )
