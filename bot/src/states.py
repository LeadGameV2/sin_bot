from collections import defaultdict
from enum import Enum

from telegram import Update

from bot.src.db_handler import db_request


class UserStateEnum(str, Enum):
    START = 0
    WRITE = 1


class UserStates:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._user_state = defaultdict(
                lambda: defaultdict()
            )
        return cls._instance

    def get_state(self, message: Update) -> int:
        return self._user_state[message.effective_chat.id]["state"]

    def update_state(self, message: Update, state: int = UserStateEnum.START):
        self._user_state[message.effective_chat.id]["state"] = state

    def get_sin(self, message: Update) -> list:
        return self._user_state[message.effective_chat.id]["sin"]

    def update_sin(self, message: Update, sin: list):
        self._user_state[message.effective_chat.id]["sin"] = sin

    def get_uuid(self, message: Update) -> int:
            if "uuid" in self._user_state[message.effective_chat.id]:
                return self._user_state[message.effective_chat.id]["uuid"]
            else:
                q = f"select id from sins.users where chat_id = {message.effective_chat.id}"
                user_uuid = db_request(q, fetch=True)
                if user_uuid:
                    return user_uuid[0][0];


    def update_uuid(self, message: Update, uuid: str):
        self._user_state[message.effective_chat.id]["uuid"] = uuid

    def get_attr(self, message: Update, attr_name: str) -> int:
        return self._user_state[message.effective_chat.id][attr_name]

    def update_attr(self, message: Update, attr_name: str, value: str):
        self._user_state[message.effective_chat.id][attr_name] = value
