""""""
"""
思路：任何输出将会被放在redis的队列中

"""
import asyncio
import datetime
import hashlib
import logging
import select
import typing

import loguru
import redis
from subprocess import Popen, PIPE
import threading
import pathlib
import psutil
import enum

PSUTIL_STATUS_MAPPER = {
    psutil.STATUS_RUNNING: "running",
    psutil.STATUS_SLEEPING: "sleeping",
    psutil.STATUS_DISK_SLEEP: "disk sleeping",
    psutil.STATUS_STOPPED: "stopped",
    psutil.STATUS_TRACING_STOP: "tracing stop",
    psutil.STATUS_ZOMBIE: "zombie",
    psutil.STATUS_DEAD: "dead",
    psutil.STATUS_WAKING: "waking",
    psutil.STATUS_IDLE: "idle",
    psutil.STATUS_LOCKED: "locked"
}


class RunStatus(str, enum.Enum):
    RUNNING = "running"
    SLEEPING = "sleeping"
    STOPPED = "stopped"
    INPUT = "input"
    OUTPUT = "output"
    EXCEPTION = "exception"


class InteractionType(str, enum.Enum):
    INPUT = "input"


class Interaction(typing.TypedDict):
    type: InteractionType
    data: str


class CodeProcess(typing.TypedDict):
    code: str
    connection_id: str
    process_id: int


class CommunicateResult(typing.TypedDict):
    process_id: int
    good: bool
    result: str


class Signal(typing.TypedDict):
    type: RunStatus
    result: typing.Optional[dict]
    reason: typing.Optional[str]


class ThreadSafeDict:
    def __init__(self):
        self.dict: dict[str, Popen] = {}
        self.lock = threading.Lock()

    def set_item(self, key, value):
        with self.lock:
            self.dict[key] = value

    def get_item(self, key):
        with self.lock:
            return self.dict.get(key)

    def remove_item(self, key):
        with self.lock:
            self.dict.pop(key, None)

    def items(self):
        with self.lock:
            return self.dict.items()


class SourceCode(typing.TypedDict):
    code: str
    language: str


class CodeExecutor:
    """
        执行源代码的类。此类通过在子进程中运行代码来执行，并管理该过程的输入输出和状态。

        属性:
            execution_id (str): 基于源代码和当前时间生成的唯一执行ID。
            root (Path): 当前工作目录的路径。
            engine_path (Path): 用于执行代码的引擎路径。
            source_code (str): 要执行的源代码。
            process (Optional[Popen]): 子进程对象，用于执行源代码。
            _p (Optional[psutil.Process]): psutil库的进程对象，用于更细粒度的进程控制。
            input_queue (None): 用于存储输入的队列。（未在此代码片段中使用）
            _input_thread (None): 处理输入的线程。（未在此代码片段中使用）
    """

    def __init__(self, source_code: str):
        self.execution_id = hashlib.md5(f"{source_code} {datetime.datetime.now()}".encode()).hexdigest()
        self.root = pathlib.Path.cwd()
        self.engine_path = self.root / "Pseudo/PseudoEngine2"

        self.source_code = source_code
        self.process: Popen | None = None
        self._p = None
        self.input_queue = None
        self._input_thread = None

    # Launch the engine with source code provided
    def setup_runtime(self):
        """准备运行环境，包括源代码文件的创建和子进程的初始化。"""
        file_path = self.root / f"Buffer/{self.execution_id}.pseudo"
        pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)  # make sure the path and file exists

        with open(file_path, 'w') as file:  # write code into template source code file
            file.write(self.source_code)

        command = f"{self.engine_path} {file_path}"  # TODO: add support for custom options
        self.process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, shell=True)
        self._p = psutil.Process(self.process.pid)

    def is_process_terminated(self):
        return self.process.poll() is not None

    def _process_select_stdout(self, readable) -> typing.List[Signal]:
        signals: typing.List[Signal] = []
        for stream in readable:
            if stream == self.process.stdout.fileno():
                read = self.process.stdout.readline()
                if read == '':  # EOF exception
                    signals.append({
                        "type": RunStatus.EXCEPTION,
                        "reason": "EOF",
                        "result": None
                    }
                    )
                signals.append({
                    "type": RunStatus.OUTPUT,
                    "result": {
                        "output": f"{read}"
                    },
                    "reason": None
                })
            elif stream == self.process.stderr.fileno():
                read = self.process.stderr.readline()
                if read == '': continue  # IGNORE the eof-like exception since they are somewhat misfunctioned
                signals.append({
                    "type": RunStatus.EXCEPTION,
                    "reason": f"{read}",
                    "result": None
                })
        return signals

    def _parse_input(self, interaction: Interaction) -> bool:
        if interaction['type'] == InteractionType.INPUT:
            self.process.stdin.write(interaction['data'])
            self.process.stdin.flush()
            return True
        return False

    def run(self) -> typing.Generator[Signal]:
        self.setup_runtime()
        yield {
            "type": RunStatus.RUNNING,
            "result": "Process started"
        }
        stdout, stderr = [], []
        flag = False
        while (not flag) and self.is_process_terminated():
            readable, writable, exception = select.select(
                [self.process.stdout.fileno(), self.process.stderr.fileno()],
                [],
                [],
                0.1  # Timeout
            )
            if not readable:  # 如果没有可读的流
                break  # 退出循环

            signals = []
            readable_signals = self._process_select_stdout(readable)
            signals.extend(readable_signals)
            signals.append({  # Ensure every loop can provide at least 1 yield
                "type": RunStatus.RUNNING,
                "result": "Process is running..."
            })
            for _signal in signals:
                if _signal == RunStatus.EXCEPTION and _signal['reason'] == 'EOF': flag = True
                recv = yield _signal
                self._parse_input(recv)
        yield {
            "type": RunStatus.STOPPED,
            "result": f"Process ended for {self.source_code}",
        }
        return {
            "output": stdout,
            "error": stdout
        }


class ExecutionManager:
    def __init__(self,
                 source_code,
                 connection_id,
                 redis_instance: redis.Redis,
                 logger: loguru.Logger | logging.Logger = None,
                 _debug: bool = False
                 ):
        self.connection_id = connection_id  # redis的队列名为connection_id
        self.executor = CodeExecutor(source_code)
        self.redis_instance = redis_instance
        # 实现通过websocket获得input的功能，假设它将会由fastapi中的ws路由调用且使用celery执行
        self._input_queue = asyncio.Queue()
        self.max_taken_amount = 200
        self._debug = _debug

    async def fetch_user_input(self):
        try:
            items = await self.redis_instance.lpop(
                f"input_{self.connection_id}",
                self.max_taken_amount
            )
            for item in items:
                await self._input_queue.put(item.decode('utf-8'))
        except redis.exceptions.ConnectionError as e:
            print(repr(e))

    async def run(self):
        code_iter: typing.Generator = self.executor.run()
        interaction = None
        while (signal := code_iter.send(interaction)) != StopIteration:
            await self.fetch_user_input()
            item = await self._input_queue.get()
            if signal["type"] == RunStatus.OUTPUT:
                await self.redis_instance.lpush(
                    f"output_{self.connection_id}",
                    f"{signal['result'].get('output')}".encode('utf-8')
                )  # 需要cache优化
            interaction = {
                "type": InteractionType.INPUT,
                "data": item
            }


if __name__ == "__main__":
    code = \
        """
        DECLARE A:INTEGER
        INPUT A
        OUTPUT A
        """
    code_executor = CodeExecutor(code)
    for _signal in code_executor.run():
        print("Signal received:", _signal)
        # if signal['type'] == RunStatus.OUTPUT and "INPUT" in signal['result']['data']:
        #     # 当需要输入时，发送输入
        #
        #     signal = {"input": user_input}
