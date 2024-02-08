import concurrent.futures
import typing

from celery import Celery
import celery
from subprocess import Popen, PIPE, TimeoutExpired
import os
import shlex
import threading
import pathlib

# class CodeExecuteWorker(celery.Task):
#     def __init__(self, engine_path="/Pseudo/PseudoEngine2"):
#         super().__init__()
#         self.process = None
#         self.outputs = []
#         self.engine_path = engine_path
#         self.errors = []
#
#     def run(self, connection_id, code):
#         file_path = os.path.join(os.getcwd(), f"Buffer/{connection_id}.pseudo")
#         with open(file_path, 'w') as file:
#             file.write(code)
#         engine_path = "/Pseudo/PseudoEngine2"
#         full_engine_path = os.path.join(os.getcwd(), engine_path)
#         command = shlex.split(f"{full_engine_path} {file_path}")
#
#         # Start process
#         self.process = Popen(command, stdout=PIPE, stderr=PIPE, text=True)
#
#         def handle_output(process, output_list):
#             for line in iter(process.stdout.readline, b''):
#                 output_list.append(line.decode().strip())
#
#         with concurrent.futures.ThreadPoolExecutor() as executor:
#             executor.submit(handle_output, self.process, self.outputs)
#             try:
#                 self.process.wait(timeout=120)
#             except TimeoutExpired:
#                 self.process.kill()
#                 self.errors.append("TIMEOUT AFTER 120 SECONDS")
#             self.errors.extend(self.process.stderr.read().splitlines())
#         return {
#             'outputs': self.outputs,
#             'errors': self.errors
#         }
#
# @celery.shared_task
# def run_process(connection_id, code):
#     outputs = []
#     errors = []
#     terminate = False
#
#     file_path = os.path.join(os.getcwd(), f"Buffer/{connection_id}.pseudo")
#     with open(file_path, 'w') as file:
#         file.write(code)
#     engine_path = "/Pseudo/PseudoEngine2"
#     full_engine_path = os.path.join(os.getcwd(), engine_path)
#     command = shlex.split(f"{full_engine_path} {file_path}")
#
#     # Start process
#     p = Popen(command, stdout=PIPE, stderr=PIPE, text=True)
#
#     def handle_output(process, output_list):
#         for line in iter(process.stdout.readline, b''):
#             output_list.append(line.decode().strip())
#
#     thread = threading.Thread(target=handle_output, args=(p, outputs))
#     thread.start()
#
#     try:
#         p.wait(timeout=120)
#         thread.join()
#     except TimeoutExpired:
#         p.kill()
#         errors.append("TIMEOUT AFTER 120 SECONDS")
#         terminate = True
#     errors.extend(p.stderr.read().splitlines())
#     return {'outputs': outputs, 'errors': errors, 'terminate': terminate}

