<h1 align="center">Spotlight</h1>

<p align="center">
  <img src="photo.jpg" alt="Spotlight" width="220">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Pyrogram-MTProto-2CA5E0?logo=telegram&logoColor=white" alt="Pyrogram">
  <img src="https://img.shields.io/badge/NumPy-SVD-013243?logo=numpy&logoColor=white" alt="NumPy">
  <img src="https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white" alt="Telegram">
</p>

<p align="center">
  A Telegram bot that estimates who the main characters of a group chat are,<br>
  based on who replies to whom, using the singular value decomposition (SVD).
</p>

---

Numerical Mathematics project, Faculty of Mathematics and Computer Science, University of Havana (MATCOM).

## What it does

Once added to a group, the bot counts how many times each person replies to each other person. From those counts it builds a matrix and uses SVD to compute an "authority" score for every user. The result is a ranking that does not depend only on who talks the most, but on **who gets replied to by the people who matter themselves**.

## How it works, step by step

### 1. Data collection

A Telegram bot only sees messages sent after it joined the group, and to receive replies you must turn off *privacy mode* in BotFather (or make the bot an admin). Every time someone replies to a message, the bot records the pair `(who replied, to whom)` and adds one to that pair's counter.

Replies to oneself, messages from bots, messages without an author and commands are ignored.

**The content of messages is never stored**, only counters and the names needed to display the ranking.

### 2. Storage

Everything lives in a single SQLite file (`data.db`) with three tables:

| Table | Contents |
|---|---|
| `replies(chat_id, i, j, n)` | `n` = number of times `i` replied to `j` in that chat. Primary key `(chat_id, i, j)`. |
| `users(chat_id, user_id, first_name, username)` | Names used to display the ranking. |
| `active_chats(chat_id)` | Chats where the bot is counting. |

Counting uses an *upsert* (`INSERT ... ON CONFLICT DO UPDATE`), so each reply either increments the existing counter or creates the pair.

### 3. The matrix

When the ranking is requested, a square matrix $A$ is built on demand, where

$$A_{ij} = \text{number of times user } i \text{ replied to user } j$$

with a zero diagonal. Telegram IDs are mapped to positions $0 \dots n-1$, and that mapping is kept so the results can be translated back to real users. For now the matrix is capped at 100 users.

### 4. Normalization

Before the SVD, the square root is applied to every entry. With raw counts, a couple of very talkative users dominate the whole first component. With `log(1 + x)` the opposite happens: people who barely talk weigh too much. The square root is a middle ground that was tuned by testing on real chats.

### 5. SVD and scoring

The decomposition $A = U \Sigma V^T$ is computed. The approach is analogous to Kleinberg's HITS:

- The first row of $V^T$ (right singular vector) gives the **authority**: who the people that matter reply to.
- The first column of $U$ (left singular vector) gives the **hub**: who replies to the people that matter.

The sign of a singular vector is arbitrary, so it is normalized to make its sum positive. For the ranking, each user's authority is divided by the total and shown as a percentage, so the values add up to 100 %.

### 6. Importing history

Since the bot cannot read a group's past, there is `/importar`: export the chat from Telegram Desktop (JSON format, without media) and reply to the file with the command. The bot reads `result.json`, matches each reply with its author and adds the counts to the existing ones.

## Commands

| Command | Description |
|---|---|
| `/listen` | Start counting replies in the group. |
| `/protas` | Show the ranking of main characters. |
| `/importar` | Reply to a `result.json` with it to load past history. |
| `/restart` | Restart the bot (group admins only). |
| `/start`, `/help` | In private: explanation and a button to add the bot to a group. |

## Installation

```bash
git clone <repository-url>
cd <folder>
pip install -r requirements.txt
```

`requirements.txt`:

```
pyrogram
tgcrypto
numpy
python-dotenv
```

Create a `.env` file in the project root:

```
API_ID=123456
API_HASH=your_api_hash
BOT_TOKEN=your_botfather_token
```

`API_ID` and `API_HASH` come from [my.telegram.org](https://my.telegram.org) and the token from [@BotFather](https://t.me/BotFather). Then, in BotFather, disable the bot's *privacy mode* (`/setprivacy` → `Disable`) and add the bot to the group again. To run it:

```bash
python bot.py
```

`.env`, `*.session` and `*.db` are in `.gitignore`: never commit them.

## Project structure

```
bot.py        Telegram handlers and message formatting
db.py         DataBase class: SQLite tables and queries
svd.py        matrix construction, SVD and scores
importer.py   reader for the exported result.json
assets/       bot image
```

## Status

Pending: some performance improvements and deploying the bot to a host.

## Privacy

The bot only stores who replied to whom and how many times, together with each user's display name and username. The text of messages is neither stored nor processed.
