import json
import logging
from asyncio import Queue, create_task, sleep
from socket import gaierror

import websockets
from websockets.exceptions import ConnectionClosedError

from .dispatchers import MessageDispatcher


class EventTask:
    def __init__(self, message_dispatcher: MessageDispatcher, ws_url):
        self.dispatcher = message_dispatcher
        self.ws_url = ws_url

    async def worker(self, queue: Queue):
        logging.debug("worker up")
        while True:
            raw_event = await queue.get()

            event = json.loads(raw_event)
            try:
                await self.dispatcher.dispatch(event)
            except Exception as e:
                logging.exception("Exception occur in dispatcher worker.")

            queue.task_done()

    async def run(self, workers):
        task_queue = Queue()
        tasks = []
        for i in range(workers):
            task = create_task(self.worker(task_queue))
            tasks.append(task)

        logging.info("event loop up")
        while True:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    async for raw_event in ws:
                        task_queue.put_nowait(raw_event)
            except (ConnectionClosedError, gaierror, ConnectionRefusedError):
                await sleep(5)
