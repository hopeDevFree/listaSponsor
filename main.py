import re

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import tgcrypto
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

app = Client(name="SponsorLVB", api_id=os.environ["api_id"], api_hash=os.environ["api_hash"],
             bot_token=os.environ["bot_token"])

conn = psycopg2.connect(database=os.environ["db_name"],
                        host=os.environ["db_host"],
                        user=os.environ["db_user"],
                        password=os.environ["db_password"],
                        port=os.environ["db_port"])


@app.on_message(filters.command('start') & filters.private)
async def start_command(app, message):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (message.from_user.id,))
    if cur.fetchone() is None:
        cur.execute("INSERT INTO users(id, date) VALUES (%s, %s)", (message.chat.id, message.date))

    base_buttons_list = [[InlineKeyboardButton('Registra canali ✏️', callback_data="channelSU/0")]]

    if message.from_user.id == 793550967 or message.from_user.id == 5453376840:
        welcome_text = """👷🏻 <i>Ciao admin!     

👇🏻 Digita i pulsanti sotto per effettuare l'operazione che preferisci!</i>"""

        base_buttons_list.append([InlineKeyboardButton("Canali registrati 👁️", callback_data="allChannels"),
                                  InlineKeyboardButton("Preview lista 📄", callback_data="previewList")])

        await message.reply(
            text=welcome_text,
            reply_markup=InlineKeyboardMarkup(base_buttons_list),
            disable_web_page_preview=True)

    conn.commit()


@app.on_callback_query()
async def callback_query(app, callbackQuery):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (callbackQuery.from_user.id,))
    user = cur.fetchone()

    cur.execute("SELECT * FROM list")
    list_obj = cur.fetchone()

    if callbackQuery.data == "menu":

        base_buttons_list = [[InlineKeyboardButton('Registra canali ✏️', callback_data="channelSU/0")]]

        if callbackQuery.from_user.id == 793550967 or callbackQuery.from_user.id == 5453376840:
            welcome_text = """👷🏻 <i>Ciao admin!     

👇🏻 Digita i pulsanti sotto per effettuare l'operazione che preferisci!</i>"""

            base_buttons_list.append([InlineKeyboardButton("Canali registrati 👁️", callback_data="allChannels"),
                                      InlineKeyboardButton("Preview lista 📄", callback_data="previewList")])

            await callbackQuery.edit_message_text(
                text=welcome_text,
                reply_markup=InlineKeyboardMarkup(base_buttons_list),
                disable_web_page_preview=False)

    if "channelSU" in callbackQuery.data:

        signup_pass = callbackQuery.data.split("/")[1]

        if signup_pass == "0":
            await callbackQuery.edit_message_text(
                text="""<i>📄 Invia la lista che verrà inoltrata.</i>""",

                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('👇🏻 Scrivi', callback_data='none')]]),
                disable_web_page_preview=False)

            cur.execute("UPDATE users SET step = %s, lastbotmessage = %s WHERE id = %s",
                        ("pass0", callbackQuery.message.id, user[0],))

    if callbackQuery.data == "previewList":
        await app.send_message(chat_id=callbackQuery.from_user.id,
                               text=f"""<i>👁️ Ecco la lista attuale:""")

        await app.copy_message(
            chat_id=callbackQuery.from_user.id,
            from_chat_id=callbackQuery.from_user.id,
            message_id=list_obj[0],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Home', callback_data='menu')]])
        )

    if callbackQuery.data == "allChannels":
        pattern = r'@\S+'

        match = re.findall(pattern, list_obj[1])

        channels_text = "➕ Questi sono i canali presenti nella lista:\n\n"
        for channel in match:
            channels_text = channels_text + f"- {channel}\n"

        await app.send_message(
            chat_id=callbackQuery.from_user.id,
            text=channels_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Home', callback_data='menu')]])
        )

    conn.commit()


# Check passaggi singup
@app.on_message(filters.private)
async def signupChannel(app, message):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=%s", (message.from_user.id,))
    user = cur.fetchone()

    if user[1] == "pass0":
        list_text = message.text
        id_message_list = message.id

        cur.execute("SELECT * FROM list")
        list_obj = cur.fetchone()

        if list_obj is None:
            cur.execute("INSERT INTO list(id, text) values (%s, %s)", (id_message_list, list_text))

        else:
            cur.execute("UPDATE list SET id = %s, text = %s WHERE id = %s", (id_message_list, list_text, list_obj[0]))

        await message.reply(
            text="""<i>✅ La lista è stata salvata correttamente! 
                                    
Verrà inoltrata il <b>primo</b> giorno di ogni mese alle 18:00.</i>""",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('🔙 Home', callback_data='menu')]]),
            disable_web_page_preview=False)

    conn.commit()


async def send_list_message():
    cur = conn.cursor()
    cur.execute("SELECT * FROM list")
    list_obj = cur.fetchone()

    pattern = r'@\S+'

    match = re.findall(pattern, list_obj[1])

    for channel in match:
        copied_message = await app.copy_message(
            chat_id=channel,
            from_chat_id=793550967,
            message_id=list_obj[0]
        )
        cur.execute("INSERT INTO channels_message(username, id_message) values(%s, %s)", (channel, copied_message.id))

    conn.commit()


async def delete_list_message():
    cur = conn.cursor()
    cur.execute("SELECT * FROM channels_message")
    list_objs = cur.fetchall()

    for channel in list_objs:
        await app.delete_messages(
            chat_id=channel[0],
            message_ids=channel[1])
        cur.execute("DELETE FROM channels_message WHERE username=%s", (channel[0],))

    conn.commit()


scheduler = AsyncIOScheduler(timezone="Europe/Rome")
scheduler.add_job(send_list_message, "cron", day=1, hour=18, minute=0)
scheduler.add_job(delete_list_message, "cron", day=2, hour=18, minute=0)
scheduler.start()

app.run()
