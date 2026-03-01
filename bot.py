import discord
from discord.ext import commands
import aiosqlite
import requests
import os

intents = discord.Intents.default()
intents.message_content = True       # Required for reading messages
intents.members = True               # Required if you want to track joins/leaves or user info

bot = commands.Bot(command_prefix="/", intents=intents)

DB_PATH = "decks.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                deck_name TEXT,
                deck_text TEXT
            );
        """)
        await db.commit()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await init_db()

@bot.command()
async def deck(ctx, action: str, *, args=None):
    # /deck submit "My Deck" cards...
    if action.lower() == "submit":
        if not args:
            await ctx.send("Usage: `/deck submit <deck name> | <deck text>`")
            return

        try:
            name, text = args.split("|", 1)
        except ValueError:
            await ctx.send("Please include a deck name and a deck list separated by `|`")
            return

        user_id = ctx.author.id
        user_name = ctx.author.display_name

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO decks (user_id, user_name, deck_name, deck_text) VALUES (?, ?, ?, ?)",
                (user_id, user_name, name.strip(), text.strip())
            )
            await db.commit()
        await ctx.send(f"Deck **{name.strip()}** submitted by **{user_name}**!")

    elif action.lower() == "list":
        async with aiosqlite.connect(DB_PATH) as db:
            rows = await db.execute_fetchall("SELECT user_name, deck_name FROM decks")
        if not rows:
            await ctx.send("No decks submitted yet.")
            return

        text = "\n".join([f"{r[0]}: {r[1]}" for r in rows])
        await ctx.send(f"**Submitted Decks:**\n{text}")

    elif action.lower() == "view":
        if not args:
            await ctx.send("Usage: `/deck view <player name>`")
            return
        async with aiosqlite.connect(DB_PATH) as db:
            rows = await db.execute_fetchall(
                "SELECT deck_name, deck_text FROM decks WHERE user_name LIKE ?",
                (f"%{args}%",)
            )
        if not rows:
            await ctx.send("No deck found for that player.")
            return

        name, text = rows[0]
        await ctx.send(f"**{args} – {name}**\n{text}")

    else:
        await ctx.send("Unknown `<action>`. Use `submit`, `list`, or `view`.")

bot.run(os.environ["DISCORD_TOKEN"])