import os
from pyrogram import Client
from pyrogram.types import Message
import pyrogram.filters as fl
from db import DataBase

app = Client("my_account", os.environ["API_ID"], os.environ["API_HASH"])
database = DataBase()

@app.on_message(filters = fl.group & fl.command("listen"))
async def start(cli: Client, msg: Message):
    database.active_chat(msg.chat.id)
    await msg.reply("Spotlight is listening to feed the matrix...")

@app.on_message(filters = fl.group & fl.command("protas"))
async def get_rank(cli: Client, msg: Message):
    if database.join_chat(msg.chat.id) is not None:
        pass
    else:
        await msg.reply("Run the command /listen first")

@app.on_message(filters = fl.group & fl.reply & ~fl.command(["listen", "protas"]), group = 1)
async def reply_listener(cli: Client, msg: Message):
    if database.join_chat(msg.chat.id) is None:
        return

    if msg.reply_to_message is None:
        return
    
    user = msg.from_user
    replied = msg.reply_to_message.from_user

    if user is None or replied is None:
        return
    
    if user.is_bot or replied.is_bot:
        return
    
    if user.id == replied.id:
        return

    database.add_reply(msg.chat.id, user.id, replied.id)
    database.add_user(msg.chat.id, user.id, user.first_name, user.username)
    database.add_user(msg.chat.id, replied.id, replied.first_name, replied.username)
    #database.debug()

app.run()
