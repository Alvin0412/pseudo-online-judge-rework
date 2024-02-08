import concurrent.futures
import typing

from celery import Celery
import celery
from subprocess import Popen, PIPE, TimeoutExpired
import os
import shlex
import threading
import pathlib
import psutil

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


class CodeProcess(typing.TypedDict):
    code: str
    connection_id: str
    process_id: int


class CommunicateResult(typing.TypedDict):
    process_id: int
    good: bool
    result: str


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


process_dict = ThreadSafeDict()


def default_process_dict():
    return process_dict


def make_exec_process(
        connection_id: str,
        code: str,
        engine_path: str = "Pseudo/PseudoEngine2.exe",
        get_io_dict=default_process_dict
) -> CodeProcess:
    file_path = pathlib.Path.cwd() / f"Buffer/{connection_id}.pseudo"
    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as file:
        file.write(code)
    full_engine_path = pathlib.Path.cwd() / engine_path
    command = f"{full_engine_path} {file_path}"

    p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, shell=True)
    io_dict = get_io_dict()
    io_dict.set_item(connection_id, p)
    # 对p进行检查然后返回
    return {
        'code': code,
        'connection_id': connection_id,
        'process_id': p.pid
    }


def get_process(connection_id: str, get_io_dict=default_process_dict) -> Popen:
    io_dict = get_io_dict()
    return io_dict.get_item(connection_id)


def handle_process_input(
        ps: Popen,
        content: str,
) -> CommunicateResult:
    if ps is None:
        return {
            'process_id': -1,
            'good': False,
            'result': "Process not found"
        }
    try:
        ps_process = psutil.Process(ps.pid)
        ps_process_status = ps_process.status()
        if ps_process_status in {
            psutil.STATUS_ZOMBIE,
            psutil.STATUS_DEAD,
            psutil.STATUS_STOPPED,
            psutil.STATUS_LOCKED
        }:
            return {
                'process_id': ps.pid,
                'good': False,
                'result': f"Process is {PSUTIL_STATUS_MAPPER[ps_process_status]}"
            }
        if not ps_process.is_running():
            return {
                'process_id': ps.pid,
                'good': False,
                'result': "Process is not running"
            }
        ps.stdin.write(content)
        ps.stdin.flush()
        return {
            'process_id': ps.pid,
            'good': True,
            'result': "Success"
        }
    except Exception as e:
        return {
            'process_id': ps.pid,
            'good': False,
            'result': f"Error: {str(e)}"
        }


def handle_process_output(
        ps: Popen,
) -> CommunicateResult:
    if ps is None:
        return {
            'process_id': -1,
            'good': False,
            'result': "Process not found"
        }
    try:

        test_ps = psutil.Process(ps.pid)
        _ = {
            'process_id': ps.pid,
            'good': True,
            'result': f"{ps.stdout.readline()}"
        }
        return _
    except Exception as e:
        return {
            'process_id': ps.pid,
            'good': False,
            'result': f"Error: {str(e)}"
        }


_code = \
    """
    DECLARE a:STRING
    OUTPUT "Hello, World!"
    INPUT a
    OUTPUT "Hello, World!\n" & a
    OUTPUT "Hello, World!\n" & a
    OUTPUT "Hello, World!\n" & a
    OUTPUT "Hello, World!\n" & a
    INPUT a
    OUTPUT "Hello, World!\n" & a
    """
test_id = "test"
make_exec_process(test_id, _code)
get_test_ps = lambda: get_process(test_id)
# handle_process_input(get_test_ps(), "Alvin!")
res = handle_process_output(get_test_ps())
print(res)
# handle_process_input(get_test_ps(), "A111111")
# res = handle_process_output(get_test_ps())
# print(res)
