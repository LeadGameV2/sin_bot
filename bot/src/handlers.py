from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ContextTypes, CallbackContext

import psycopg2

from src import prompts
from src.states import UserStateEnum, UserStates
from settings import settings

user_state = UserStates()


def db_request(query: str, fetch: bool = False):
    try:
        connection = psycopg2.connect(
            database=settings.postgres.db_name,
            host=settings.postgres.host,
            user=settings.postgres.user,
            password=settings.postgres.password,
            port=settings.postgres.port)
        cursor = connection.cursor()
        cursor.execute(query)
        if fetch:
            result = cursor.fetchall()
        else:
            connection.commit()
            result = True
        
    except (Exception, psycopg2.Error) as error:
        logger.warning(f"Error while fetching data from PostgreSQL {error}")
        result = False

    finally:
        if connection:
            cursor.close()
            connection.close()

    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state.update_state(update)
    chat_id = update.effective_chat.id
    logger.info(f"START with {chat_id}")

    q = f"""INSERT INTO sins.users (id, chat_id, nickname, created, modified) 
    VALUES (gen_random_uuid(), {chat_id}, '{update.effective_user.username}', NOW(), NOW());"""
    db_request(q)

    await context.bot.send_message(
        chat_id=chat_id, text=prompts.GREETING_TEXT
    )
    q = f"select id from sins.users where chat_id = {chat_id}"
    user_uuid = db_request(q, fetch=True)
    if user_uuid:
        user_state.update_uuid(update, user_uuid[0][0])
    else:
        logger.warning(f"No user {chat_id} {update.effective_user.username}")

    await ask_choice(update, context)


async def ask_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state.update_state(update, UserStateEnum.START)
    reply_markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Написать свой грех 🙏🏻", callback_data="create")
            ],
            [
                InlineKeyboardButton("Мои грехи 😈", callback_data="my"),
            ],
            [
                InlineKeyboardButton("Оценить чужие грехи 👀", callback_data="vote"),
            ],
            [
                InlineKeyboardButton("Лучшие грехи 💯", callback_data="top"),
            ]
        ]
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=prompts.ASK_FOR_CHOICE,
        reply_markup=reply_markup,
    )


async def create_sin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Напиши сюда свой самый страшный продуктовый грех"
    )
    user_state.update_state(update, UserStateEnum.WRITE)

async def my_sins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_uuid =  user_state.get_uuid(update)

    q = f"select text from sins.sins where author_id = '{user_uuid}'"
    sins = db_request(q, fetch=True)

    if not sins:
        sins_text = "Нет грехов"
    
    else:
        sins_text = "\n\n".join([f"{num + 1}. {sin[0]}" for num, sin in enumerate(sins)])

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=sins_text
    )
    await ask_choice(update, context)


def get_total_sins_count():
    q = "SELECT COUNT(*) FROM sins.sins"
    sin_num = db_request(q, fetch=True)

    if sin_num:
        return sin_num[0][0]
    else:
        return 0


def get_top_sins(page, page_size=settings.top_sins_per_page):
    offset = (page - 1) * page_size
    q = f"""SELECT id, text, likes, dislikes
        FROM sins.sins
        ORDER BY likes - dislikes DESC
        LIMIT {page_size} OFFSET {offset}"""
    
    top_sins = db_request(q, fetch=True)
    return top_sins
    

def get_paginated_top_sins(page: int = 1, page_size=settings.top_sins_per_page):
    sins_list = get_top_sins(page, page_size)

    if sins_list:
        top_sins_text = "*Топ грехов:*\n\n" + \
            "\n\n".join([f"{(page - 1) * page_size + num + 1}. {sin[1]}\n👍 {sin[2]} 👎 {sin[3]}" for num, sin in enumerate(sins_list)])
    else:
        top_sins_text = "Нет доступных грехов."
    
    return top_sins_text

def get_paginated_navigation(page: int = 1):
    total_sins = get_total_sins_count()

    keyboard = []
    if page > 1:
        keyboard.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page-1}"))
    if page * settings.top_sins_per_page < total_sins:  # проверяем, есть ли еще страницы
        keyboard.append(InlineKeyboardButton("➡️", callback_data=f"page_{page+1}"))

    return InlineKeyboardMarkup([keyboard])


async def top_sins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=get_paginated_top_sins(1), 
        reply_markup=get_paginated_navigation(1),
        parse_mode=constants.ParseMode.MARKDOWN)


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_uuid = user_state.get_uuid(update)
    q = f"""SELECT *
            FROM sins.sins s
            LEFT JOIN sins.votes v ON s.id = v.sin_id AND v.author_id = '{user_uuid}'
            WHERE v.id IS null and s.author_id != '{user_uuid}'
            order by s.likes + s.dislikes 
            limit 1"""
    
    sin = db_request(q, fetch=True)
    if not sin:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Новых грехов нет! Приходи позже 🙏🏻"
        )
        await ask_choice(update, context)

    else:
        user_state.update_sin(update, sin[0])

        reply_markup = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("👍", callback_data="like"),
                 InlineKeyboardButton("👎", callback_data="dislike")],
                [InlineKeyboardButton("В меню", callback_data="menu")]
            ]
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=sin[0][1],
            reply_markup=reply_markup
        )

async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'create':
        await create_sin(update, context)

    elif query.data == 'vote':
        await vote(update, context)

    elif query.data == 'my':
        await my_sins(update, context)

    elif query.data == 'top':
        await top_sins(update, context)

    elif query.data.startswith("page_"):
        page = int(query.data.split("_")[1])
        await query.edit_message_text(get_paginated_top_sins(page),
                                      reply_markup=get_paginated_navigation(page),
                                      parse_mode=constants.ParseMode.MARKDOWN)
        
    elif query.data == "menu":
        await ask_choice(update, context)

    elif query.data in ("dislike", "like"):
        sin = user_state.get_sin(update)
        user_uuid = user_state.get_uuid(update)
        sin_likes, sin_dislikes = sin[3:5]

        if sin_likes + sin_dislikes == 0:
            msg_text = "Ты первый, кто оценил этот грех!"
        else:
            if query.data == "dislike":
                part = int(sin_dislikes * 100 / (sin_likes + sin_dislikes))
            else:
                part = int(sin_likes * 100 / (sin_likes + sin_dislikes))

            msg_text = f"Твое мнение совпало с {part}% пользователей!"
        
        if query.data == "dislike":
            sin_dislikes += 1
        else:
            sin_likes += 1

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=msg_text
        )

        q_update = f"""UPDATE sins.sins
                    SET likes = {sin_likes}, 
                        dislikes = {sin_dislikes}
                    WHERE id = '{sin[0]}';"""
        db_request(q_update)
        #create vote

        q_create = f"""INSERT INTO sins.votes (id, author_id, sin_id, created, modified)
                    VALUES (gen_random_uuid(), '{user_uuid}', '{sin[0]}', NOW(), NOW());"""

        db_request(q_create)

        await vote(update, context)


async def text_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = user_state.get_state(update)
    user_uuid =  user_state.get_uuid(update)

    if status == UserStateEnum.WRITE:
        q = f"""INSERT INTO sins.sins (id, text, anon, likes, dislikes, author_id, created, modified)
            VALUES (gen_random_uuid(), '{update.message.text}', TRUE, 0, 0, '{user_uuid}', NOW(), NOW());"""
        db_request(q)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Поздравляем, ты отпустил свой грех!"
        )
        await ask_choice(update, context)
