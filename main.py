import asyncio
from contextlib import closing

import psycopg2
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChannelPrivate
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated

import tgcrypto
from dotenv import load_dotenv
import os

from keep_alive import keep_alive

load_dotenv()

app = Client(name="SponsorLVB", api_id=os.environ["api_id"], api_hash=os.environ["api_hash"],
             bot_token=os.environ["bot_token"])

standard_buttons = [
    [InlineKeyboardButton('👀 SCOPRI ALTRI CANALI 👀', url="T.ME/LVBNET")],
    [InlineKeyboardButton('✅ AGGIUNGI IL TUO CANALE✅', url="t.me/LVBnetStaffbot")]
]


@app.on_message(filters.command('start') & filters.private)
async def start_command(app, message):
    with closing(psycopg2.connect(
            database=os.environ["db_name"],
            host=os.environ["db_host"],
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            port=os.environ["db_port"]
    )) as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT * FROM users WHERE id=%s", (message.from_user.id,))
            if cur.fetchone() is None:
                cur.execute("INSERT INTO users(id, date) VALUES (%s, %s)", (message.chat.id, message.date))

            base_buttons_list = [[InlineKeyboardButton('Registra canali ✏️', callback_data="channelSU/0")]]

            if message.from_user.id == 793550967 or message.from_user.id == 5453376840:
                welcome_text = """👷🏻 <i>Ciao admin!     
        
👇🏻 Digita i pulsanti sotto per effettuare l'operazione che preferisci!</i>"""

                base_buttons_list.append([InlineKeyboardButton("Preview lista 📄", callback_data="previewList"),
                                          InlineKeyboardButton("Vedi canali 📣", callback_data="seeChannels")])

                await message.reply(
                    text=welcome_text,
                    reply_markup=InlineKeyboardMarkup(base_buttons_list),
                    disable_web_page_preview=True)

            conn.commit()


@app.on_callback_query()
async def callback_query(app, callbackQuery):
    with closing(psycopg2.connect(
            database=os.environ["db_name"],
            host=os.environ["db_host"],
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            port=os.environ["db_port"]
    )) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (callbackQuery.from_user.id,))
            user = cur.fetchone()

            cur.execute("SELECT * FROM list")
            list_obj = cur.fetchone()

            if callbackQuery.data == "menu":

                base_buttons_list = [[InlineKeyboardButton('Registra canali ✏️', callback_data="channelSU/0")]]

                if callbackQuery.from_user.id == 793550967 or callbackQuery.from_user.id == 5453376840:
                    welcome_text = """👷🏻 <i>Ciao admin!     
        
👇🏻 Digita i pulsanti sotto per effettuare l'operazione che preferisci!</i>"""

                    base_buttons_list.append([InlineKeyboardButton("Preview lista 📄", callback_data="previewList"),
                                              InlineKeyboardButton("Vedi canali 📣", callback_data="seeChannels")])

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
                await app.send_message(
                    chat_id=callbackQuery.from_user.id,
                    text="<i>👁️ Ecco la lista attuale:\n\n" + list_obj[1],
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Home', callback_data='menu')]]),
                    disable_web_page_preview=True
                )

            if callbackQuery.data == "seeChannels":
                cur.execute("SELECT * FROM channels")
                channels = cur.fetchall()

                canali_text = "<i>📣 Questi sono i canali in cui verrà inviata la lista e che hanno aggiunto il bot:</i>\n\n"

                if channels:
                    for channel in channels:
                        try:
                            channel_get = await app.get_chat(channel[0])
                            canali_text = canali_text + "- " + channel_get.title + "\n"

                        except ChannelPrivate:
                            cur.execute("DELETE FROM channels WHERE id = %s", (channel[0],))
                            print("Il canale/supergruppo è privato e non accessibile.")

                else:
                    canali_text = "<i>❌ Il bot non è stato aggiunto in nessun canale.</i>"
                await app.send_message(
                    chat_id=callbackQuery.from_user.id,
                    text=canali_text,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Home', callback_data='menu')]])
                )

            conn.commit()


# Check passaggi singup
@app.on_message(filters.private)
async def signupChannel(app, message):
    with closing(psycopg2.connect(
            database=os.environ["db_name"],
            host=os.environ["db_host"],
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            port=os.environ["db_port"]
    )) as conn:
        with conn.cursor() as cur:
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
                    cur.execute("UPDATE list SET id = %s, text = %s WHERE id = %s",
                                (id_message_list, list_text, list_obj[0]))

                await message.reply(
                    text="""<i>✅ La lista è stata salvata correttamente! 
                                            
Verrà inoltrata il <b>primo</b> giorno di ogni mese alle 18:00.</i>""",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton('🔙 Home', callback_data='menu')]]),
                    disable_web_page_preview=False)

            conn.commit()


async def send_list_message():
    with closing(psycopg2.connect(
            database=os.environ["db_name"],
            host=os.environ["db_host"],
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            port=os.environ["db_port"]
    )) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM channels")
            channels = cur.fetchall()
            cur.execute("SELECT * FROM list")
            list_obj = cur.fetchone()
            for channel in channels:
                sent_message = await app.send_message(
                    chat_id=channel[0],
                    text=list_obj[1],
                    reply_markup=InlineKeyboardMarkup(standard_buttons),
                    disable_web_page_preview=True
                )
                cur.execute("INSERT INTO channels_message(username, id_message) values(%s, %s)",
                            (channel, sent_message.id))

                await asyncio.sleep(3)

            conn.commit()


async def delete_list_message():
    with closing(psycopg2.connect(
            database=os.environ["db_name"],
            host=os.environ["db_host"],
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            port=os.environ["db_port"]
    )) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM channels_message")
            list_objs = cur.fetchall()

            for channel in list_objs:
                try:
                    await app.delete_messages(
                        chat_id=channel[0],
                        message_ids=channel[1])
                    cur.execute("DELETE FROM channels_message WHERE username=%s", (channel[0],))

                except Exception as e:
                    print("Errore su canale: " + channel[0] + ", " + str(e))

            conn.commit()


@app.on_chat_member_updated()
async def handle_chat_member_update(client: Client, chat_member_updated: ChatMemberUpdated):
    chat_id = chat_member_updated.chat.id
    new_member = chat_member_updated.new_chat_member
    old_member = chat_member_updated.old_chat_member

    with closing(psycopg2.connect(
            database=os.environ["db_name"],
            host=os.environ["db_host"],
            user=os.environ["db_user"],
            password=os.environ["db_password"],
            port=os.environ["db_port"]
    )) as conn:
        with conn.cursor() as cur:
            if new_member is not None:
                if new_member.user.id == 7353195821:

                    cur.execute("SELECT * FROM channels WHERE id = %s", (chat_id,))
                    channel_obj = cur.fetchone()

                    if channel_obj is None:
                        if new_member.status == ChatMemberStatus.ADMINISTRATOR:
                            cur.execute("INSERT INTO channels(id) values(%s)", (chat_id,))
                    else:
                        if new_member.status == ChatMemberStatus.BANNED:
                            cur.execute("DELETE FROM channels WHERE id=%s", (chat_id,))

            else:
                if old_member is not None and old_member.user.id == 7353195821:
                    cur.execute("DELETE FROM channels WHERE id=%s", (chat_id,))

            conn.commit()


scheduler = AsyncIOScheduler(timezone="Europe/Rome")
scheduler.add_job(send_list_message, "cron", day=1, hour=18, minute=0)
scheduler.add_job(delete_list_message, "cron", day=2, hour=18, minute=0)


async def main():
    await app.start()
    scheduler.start()
    keep_alive()
    await idle()

    scheduler.shutdown()
    await app.stop()


asyncio.run(main())
