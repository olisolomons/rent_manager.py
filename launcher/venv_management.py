import asyncio
import logging
import queue
import subprocess
import threading
from pathlib import Path

import appdirs
import itertools
import sys

is_windows = sys.platform.startswith('win')

rent_manager_dirs = appdirs.AppDirs('RentManager')
user_cache = Path(rent_manager_dirs.user_cache_dir)
script_dir = Path(__file__).parent

conda_dir = user_cache / 'python' / 'miniconda'
launcher_venv = user_cache / 'python' / 'launcher_venv'

LOG_STDERR = logging.INFO + 2
logging.addLevelName(LOG_STDERR, 'STDERR')
LOG_STDOUT = logging.INFO + 1
logging.addLevelName(LOG_STDOUT, 'STDOUT')

if is_windows:
    conda_exec = conda_dir / '_conda.exe'
    venv_dir_python_relative = 'python.exe'
else:
    conda_exec = conda_dir / 'bin' / 'conda'
    venv_dir_python_relative = Path('bin') / 'python'


def new_venv(destination, requirements, channels=()):
    destination.mkdir(parents=True)
    LoggedProcess.run([conda_exec, 'create', '-p', destination, 'python=3.9', '--yes', '--no-default-packages'])
    LoggedProcess.run([
        conda_exec, 'install', '-p', destination, '--file', requirements, '--yes',
        *itertools.chain.from_iterable(('-c', channel) for channel in channels)
    ])


def popen_in_venv(venv, command: list, **kwargs) -> 'LoggedProcess':
    if is_windows:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    return LoggedProcess.popen([conda_exec, 'run', '-p', venv, *command], **kwargs)


class AsyncLoggedProcess:
    def __init__(self, process: asyncio.subprocess.Process, stdout_task: asyncio.Task, stderr_task: asyncio.Task,
                 detach_event: asyncio.Event):
        self.process = process
        self.stdout_task = stdout_task
        self.stderr_task = stderr_task
        self.detach_event = detach_event

    @classmethod
    async def popen(cls, args, **kwargs) -> 'AsyncLoggedProcess':
        process: asyncio.subprocess.Process = await asyncio.create_subprocess_exec(
            *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )
        detach = asyncio.Event()

        logger = logging.getLogger().getChild(f'proc{process.pid}')
        logger.info(f'started process with args {[str(arg) for arg in args]}')

        async def do_log(stream, level):
            try:
                while True:
                    line: str = (await stream.readline()).decode()
                    if not line:
                        break
                    logger.log(level, line.rstrip())
                logger.log(level, '[CLOSED]')
            except asyncio.CancelledError:
                logger.log(level, '[DETACHED]')
                raise

        async def terminable(coro):
            task = asyncio.create_task(coro)
            detached = asyncio.create_task(detach.wait())

            await asyncio.wait([task, detached], return_when=asyncio.FIRST_COMPLETED)
            task.cancel()

        stdout_task = asyncio.create_task(terminable(do_log(process.stdout, LOG_STDOUT)))
        stderr_task = asyncio.create_task(terminable(do_log(process.stderr, LOG_STDERR)))

        return cls(process, stdout_task, stderr_task, detach)

    async def wait(self) -> int:
        await asyncio.gather(self.stdout_task, self.stderr_task)

        return await self.process.wait()

    async def detach(self):
        self.detach_event.set()
        await asyncio.gather(self.stdout_task, self.stderr_task)

    @classmethod
    async def run(cls, args, **kwargs):
        process = await cls.popen(args, **kwargs)
        return_code = await process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, args)

        return return_code


class LoggedProcess:
    """
    Wrapper for AsyncLoggedProcess allowing synchronous usage
    """

    def __init__(self, thread: threading.Thread, to_async: queue.Queue, from_async: queue.Queue,
                 async_process: AsyncLoggedProcess):
        self.async_process = async_process
        self.from_async = from_async
        self.to_async = to_async
        self.thread = thread

    @classmethod
    def popen(cls, args, **kwargs) -> 'LoggedProcess':
        to_async = queue.Queue()
        from_async = queue.Queue()

        async def do_popen():
            logging.debug('do_popen: Awaiting process open')
            async_process = await AsyncLoggedProcess.popen(args, **kwargs)
            from_async.put(async_process)

            logging.debug('do_popen: getting wait/detach command')
            todo_next = await asyncio.to_thread(to_async.get)
            logging.debug('do_popen: performing command')
            result = await todo_next()
            from_async.put(result)
            logging.debug('do_popen: done')

        thread = threading.Thread(target=lambda: asyncio.run(do_popen()))
        logging.debug('Starting process management thread')
        thread.start()
        logging.debug('Started, getting process handle')

        async_process = from_async.get()
        logging.debug('Got handle')

        return LoggedProcess(thread, to_async, from_async, async_process)

    def wait(self) -> int:
        self.to_async.put(lambda: self.async_process.wait())
        self.thread.join()
        return self.from_async.get()

    def detach(self):
        self.to_async.put(lambda: self.async_process.detach())
        self.thread.join()
        return self.from_async.get()

    @classmethod
    def run(cls, args, **kwargs):
        process = cls.popen(args, **kwargs)
        return_code = process.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, args)

        return return_code
