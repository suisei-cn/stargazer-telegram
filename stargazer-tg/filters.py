from typing import Union

from aiogram.dispatcher.filters import AdminFilter
from aiogram.types import CallbackQuery, ChatType, InlineQuery, Message


class PrivilegedUser(AdminFilter):
    async def check(self, obj: Union[Message, CallbackQuery, InlineQuery]) -> bool:
        user_id = obj.from_user.id

        if self._check_current:
            if isinstance(obj, Message):
                message = obj
            elif isinstance(obj, CallbackQuery) and obj.message:
                message = obj.message
            else:
                return False
            if ChatType.is_private(message):
                return True
            chat_ids = [message.chat.id]
        else:
            chat_ids = self._chat_ids

        admins = [member.user.id for chat_id in chat_ids for member in await obj.bot.get_chat_administrators(chat_id)]

        return user_id in admins
