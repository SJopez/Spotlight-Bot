import os
from pyrogram import Client
from pyrogram.types import Message
import pyrogram.filters as fl
from db import DataBase
from svd import get_list, get_scores
from pyrogram.enums import ParseMode

app = Client("my_account", os.environ["API_ID"], os.environ["API_HASH"])
database = DataBase()
MEDALS = ["🥇", "🥈", "🥉"]

WELCOME = (
    "🎬 <b>Spotlight</b>\n\n"
    "I identify the main characters of a group chat.\n\n"
    "<b>How it works</b>\n"
    "• I count who replies to whom\n"
    "• I analyze those counts with linear algebra (SVD)\n"
    "• I rank people by how relevant the people who answer them are, not just by volume\n\n"
    "<b>Commands</b>\n"
    "• /listen — start counting replies in this group\n"
    "• /protas — show the ranking\n"
    "• /import — reply to an exported <code>result.json</code> file with it \n\n"
    "🔒 <b>Privacy</b>\n"
    "I never save the content of any message.\n\n"
)

@app.on_message(filters = fl.private & fl.command(["start", "help"]))
async def welcome_private(cli: Client, msg: Message):
    await msg.reply(WELCOME, parse_mode=ParseMode.HTML)

@app.on_message(filters = fl.group & fl.new_chat_members)
async def welcome_group(cli: Client, msg: Message):
    if any(user.is_self for user in msg.new_chat_members):
        await msg.reply(WELCOME, parse_mode=ParseMode.HTML)

@app.on_message(filters = fl.group & fl.command("import"))
async def import_history(cli: Client, msg: Message):
    if database.join_chat(msg.chat.id) is None:
        await msg.reply("Run the command /listen first")
        return

    source = msg.reply_to_message
    doc = source.document if source else None
    if doc is None or not (doc.file_name or "").endswith(".json"):
        await msg.reply("Reply to the exported result.json file with /importar")
        return

    await msg.reply("Importing, this may take a while...")
    path = await source.download()
    
    """
    try:
        counts, names = await asyncio.to_thread(parse_export, path)
    except (json.JSONDecodeError, KeyError):
        await msg.reply("The file is not a valid Telegram export")
        return
    finally:
        os.remove(path)

    database.add_users_if_missing(msg.chat.id, names)
    database.add_replies(msg.chat.id, counts)
    await msg.reply(f"Imported {sum(counts.values())} replies from {len(names)} users")
    """

@app.on_message(filters = fl.group & fl.command("listen"))
async def start(cli: Client, msg: Message):
    database.active_chat(msg.chat.id)
    await msg.reply("Spotlight is listening to feed the matrix...")

@app.on_message(filters = fl.group & fl.command("protas"))
async def get_rank(cli: Client, msg: Message):
    if database.join_chat(msg.chat.id) is None:
        await msg.reply("Run the command /listen first")
        return

    if database.count_users(msg.chat.id) == 0:
        await msg.reply("Not enough replies yet to build a ranking")
        return

    top = 10
    scores = get_scores(get_list(database, msg.chat.id))
    names = database.get_names(msg.chat.id)

    lines = ["🎬 Protagonists of this chat\n"]
    for pos, (user_id, score) in enumerate(scores[:top]):
        mark = MEDALS[pos] if pos < 3 else f"{pos + 1}."
        lines.append(f"{mark} {names.get(user_id, 'Unknown')} — {score:.0f}%")

    await msg.reply("\n".join(lines), parse_mode=ParseMode.DISABLED)

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
