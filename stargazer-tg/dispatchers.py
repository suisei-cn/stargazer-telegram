import asyncio
import os
import logging
import traceback
from typing import Optional, Any
from urllib.parse import urljoin

from aiogram import Bot
from aiogram.utils.exceptions import BadRequest, BotBlocked, BotKicked, CantInitiateConversation, ChatNotFound, RetryAfter
from httpx import AsyncClient

from .utils import escape_md_v2

if telemetry := os.environ.get("telemetry", ""):
    from sentry_sdk import capture_exception

event_map = {
    "t_tweet": "Twitter推文",
    "t_rt": "Twitter转推",
    "bili_plain_dyn": "Bilibili动态",
    "bili_rt_dyn": "Bilibili转发",
    "bili_img_dyn": "Bilibili图片动态",
    "bili_video": "Bilibili视频",
    "ytb_video": "Youtube视频",
    "ytb_reminder": "Youtube直播提醒",
    "ytb_live": "Youtube直播",
    "ytb_sched": "Youtube新直播计划"
}

escape_list = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']


class MessageDispatcher:
    def __init__(self, bot: Bot, backend_url: str, m2m_token: str):
        self.bot = bot
        self.http_client = AsyncClient(headers={"Authorization": f"Bearer {m2m_token}"})
        self.backend_url = backend_url

    async def dispatch(self, event: dict):
        topic = event["vtuber"]
        event_type = event["type"]
        message = self._build(event)

        if images := message["images"]:
            if len(images) > 1:
                input_images = [{"type": "photo", "media": image} for image in images]
                await self._dispatch(topic, event_type, self.bot.send_message, message["body"], parse_mode="MarkdownV2")
                await self._dispatch(topic, event_type, self.bot.send_media_group, input_images)
            else:
                await self._dispatch(topic, event_type, self.bot.send_photo, images[0],
                                     caption=message["body"], parse_mode="MarkdownV2")
        else:
            await self._dispatch(topic, event_type, self.bot.send_message, message["body"], parse_mode="MarkdownV2")

    @staticmethod
    def _build(event: dict) -> dict:
        name = event["vtuber"]
        tag = event_map.get(event["type"], event["type"])
        images = event["data"].get("images", [])
        msg_body = []
        if body := event["data"].get("title"):
            msg_body.append(body)
        if body := event["data"].get("text"):
            msg_body.append(body)
        if sched_time := event["data"].get("scheduled_start_time"):
            msg_body.append(f"预定时间：{sched_time}")
        if actual_time := event["data"].get("actual_start_time"):
            msg_body.append(f"上播时间：{actual_time}")

        msg_body = "\n".join(msg_body)

        link = f"[链接]({link})" if (link := event["data"].get("link")) else ""
        return {"body": "".join([escape_md_v2(f"#{name} #{tag}\n{msg_body}\n"), link]),
                "images": images}

    async def _dispatch(self, topic: str, event_type: str, func, msg: Any = "", **kwargs):
        def _parse(user_string: str) -> Optional[str]:
            try:
                user_type, user_id = user_string.split("+")
            except ValueError:
                return
            if user_type != "tg":
                return
            return user_id

        async def send_msg(user_id_str: str, _msg: Any):
            retry = True
            while retry:
                retry = False
                try:
                    await func(user_id_str, _msg, **kwargs)
                except RetryAfter as e:
                    retry = True
                    logging.warning(f"Flood control exceeded. Retry in {e.timeout} + 5 seconds.")
                    if telemetry:
                        capture_exception(e)
                    await asyncio.sleep(e.timeout + 5)
                except (BotBlocked, CantInitiateConversation, ChatNotFound, BotKicked) as e:
                    logging.warning(f"Banned/deleted/kicked/not added by chat {user_id_str}")
                    if telemetry:
                        capture_exception(e)
                except BadRequest as e:
                    logging.error(f"Unable to send message: {_msg} {kwargs}")
                    traceback.print_exc()
                    if telemetry:
                        capture_exception(e)

        logging.info(f"Dispatcher: Incoming {event_type} event.")
        all_users = (await self.http_client.get(urljoin(self.backend_url, f"m2m/subs/{topic}"),
                                                params={"type": event_type})).json()
        users = [user for _user in all_users if (user := _parse(_user))]
        logging.info(f"Dispatcher: Sending to users {users}")
        await asyncio.gather(*(send_msg(user, msg) for user in users))
