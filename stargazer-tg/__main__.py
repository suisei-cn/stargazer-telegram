import asyncio
import logging
import os
from urllib.parse import urljoin

from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.exceptions import BotBlocked, CantInitiateConversation
from httpx import AsyncClient

from .dispatchers import MessageDispatcher
from .filters import PrivilegedUser
from .tasks import EventTask

if dsn := os.environ.get("TELEMETRY", ""):
    import sentry_sdk

    sentry_sdk.init(dsn, release=os.environ.get("TELEMETRY_RELEASE", None))

BOT_TOKEN = os.environ["BOT_TOKEN"]
PROXY = _proxy if (_proxy := os.environ.get("PROXY")) else None

bot = Bot(token=BOT_TOKEN, proxy=PROXY)
dp = Dispatcher(bot)

help_msg = "\n".join([
    "PyStargazer Telegram Bot",
    "/register - Register account",
    "/settings - Set preference",
    "/delete_account - Delete account",
    "Only group owner/admins can send commands to me if I'm in a group",
    "In this case settings link will be sent to the sender privately."
])

WORKERS = int(os.environ.get("WORKERS", "10"))
M2M_TOKEN = os.environ["M2M_TOKEN"]
BACKEND_URL = os.environ["BACKEND_URL"]
FRONTEND_URL = os.environ["FRONTEND_URL"]
MESSAGE_WS = os.environ["MESSAGE_WS"]

message_dispatcher = MessageDispatcher(bot, BACKEND_URL, M2M_TOKEN)
event_task = EventTask(message_dispatcher, MESSAGE_WS)
http_client = AsyncClient(headers={"Authorization": f"Bearer {M2M_TOKEN}"})


@dp.message_handler(PrivilegedUser(), commands=["register"])
async def register(message: Message):
    r = await http_client.post(urljoin(BACKEND_URL, "users"), content=f"tg+{message.chat.id}")
    if r.status_code == 409:
        await message.answer(f"Account already exists. Please use command /settings to set your preference.")
    elif r.status_code == 204:
        await message.answer("Account created. Please use command /settings to set your preference.")
    else:
        await message.answer(f"{r.status_code} {r.text}")


@dp.message_handler(commands=["start", "help"])
async def register(message: Message):
    await message.answer(help_msg)


@dp.message_handler(PrivilegedUser(), commands=["delete_account"])
async def delete_account(message: Message):
    for_sure = len(args := message.text.split(" ")) == 2 and args[-1] == "!force"
    if not for_sure:
        await message.answer(
            f"You are going to delete your account.\n"
            f"Your account and data will be removed from the database immediately!\n"
            f"Please confirm your request by sending /delete_account !force")
        return

    r = await http_client.delete(urljoin(BACKEND_URL, f"users/tg+{message.chat.id}"))
    if r.status_code == 204:
        await message.answer("Account deleted.")
    else:
        await message.answer(f"{r.status_code} {r.text}")


@dp.message_handler(PrivilegedUser(), commands=["settings"])
async def settings(message: Message):
    r = await http_client.get(urljoin(BACKEND_URL, f"m2m/get_token/tg+{message.chat.id}"))
    link = None
    if r.status_code == 200:
        token = r.text
        url = urljoin(FRONTEND_URL, f"auth?token={token}")
        msg = f"Please click the link below to set your preference.\n" \
              f"The link will expire in 10 minutes."
        link = InlineKeyboardMarkup(row_width=1,
                                    inline_keyboard=[[InlineKeyboardButton(text="Go to settings", url=url)]])
    elif r.status_code == 404:
        msg = "User doesn't exist. Please first register by command /register."
    else:
        msg = "{r.status_code} {r.text}"

    try:
        await bot.send_message(message.from_user.id, msg, reply_markup=link,
                               parse_mode="Markdown", disable_web_page_preview=True)
    except (BotBlocked, CantInitiateConversation):
        await message.answer("Oops! I can't send you the link because I don't know you.\n"
                             "Please say something to me privately and try again!")


async def main():
    await dp.reset_webhook(True)
    await dp.skip_updates()
    logging.warning(f'Updates were skipped successfully.')

    event_handle = asyncio.create_task(event_task.run(WORKERS))
    bot_handle = asyncio.create_task(dp.start_polling())

    await event_handle
    await bot_handle


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
