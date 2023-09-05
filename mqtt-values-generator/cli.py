import argparse
import asyncio
import os.path
import sys

from loguru import logger

import loader
from signal import SIGINT, SIGTERM

parser = argparse.ArgumentParser(
    prog='Generate mqtt packages from files',
    description='What the program does',
    epilog='Text at the bottom of help')

parser.add_argument('configs', metavar='config path', type=str, nargs='+',
                    help='an integer for the accumulator')


def run():
    args = parser.parse_args()
    logger.info(args)

    workers = []
    for file_path in args.configs:
        if os.path.exists(file_path):
            worker = loader.MessageWorker(file_path)
            workers.append(worker)

    loop = asyncio.get_event_loop()
    task_list = []
    for worker in workers:
        task = worker.get_task(loop)
        task_list.append(task)

    logger.info(f"Load {len(task_list)} tasks.")

    for signal in [SIGINT, SIGTERM]:
        loop.add_signal_handler(signal, loop.stop)

    asyncio.gather(*task_list)
    loop.run_forever()


sys.exit(run())
