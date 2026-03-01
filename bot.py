import discord
from discord.ext import commands
import aiosqlite
import os

# Intents
intents = discord.Intents.default()
intents.message_content = True  # Needed for reading messages
bot = commands.Bot(command_prefix="/", intents=intents)

# Database path
DB_PATH = "decks.db"

# Initialize database
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                deck_name TEXT,
                deck_url TEXT
            );
        """)
        await db.commit()

# When bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await init_db()

# Deck command
@bot.command()
async def deck(ctx, action: str, *, args=None):
    if action.lower() == "submit":
        if not args:
            await ctx.send("Usage: `/deck submit <deck name> | <deck URL>`")
            return

        try:
            name, url = args.split("|", 1)
        except ValueError:
            await ctx.send("Please include a deck name and a deck URL separated by `|`")
            return

        user_id = ctx.author.id
        user_name = ctx.author.display_name

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO decks (user_id, user_name, deck_name, deck_url) VALUES (?, ?, ?, ?)",
                (user_id, user_name, name.strip(), url.strip())
            )
            await db.commit()

        embed = discord.Embed(title=name.strip(), description=f"[View Deck]({url.strip()})", color=0x1abc9c)
        await ctx.send(f"Deck submitted by **{user_name}**:", embed=embed)

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
                "SELECT deck_name, deck_url FROM decks WHERE user_name LIKE ?",
                (f"%{args}%",)
            )

        if not rows:
            await ctx.send("No deck found for that player.")
            return

        name, url = rows[0]
        embed = discord.Embed(title=name, description=f"[View Deck]({url})", color=0x1abc9c)
        await ctx.send(embed=embed)

    else:
        await ctx.send("Unknown action. Use `submit`, `list`, or `view`.")

# Run bot using environment variable
bot.run(os.environ["DISCORD_TOKEN"])