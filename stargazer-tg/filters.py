from typing import Union

from aiogram.dispatcher.filters import AdminFilter, ChatTypeFilter
from aiogram.types import CallbackQuery, ChatType, InlineQuery, Message


class PrivilegedUser(AdminFilter):
    async def check(self, obj: Union[Message, CallbackQuery, InlineQuery]) -> bool:
        user_id = obj.from_user.id

        if self._check_current:
            if isinstance(obj, Message):
                chat = obj.chat
            elif isinstance(obj, CallbackQuery) and obj.message:
                chat = obj.message.chat
            else:
                return False
            if chat.type == ChatType.PRIVATE:
                return True
            chat_ids = [chat.id]
        else:
            chat_ids = self._chat_ids

        admins = [member.user.id for chat_id in chat_ids for member in await obj.bot.get_chat_administrators(chat_id)]

        return user_id in admins
