import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

import click
import discord
from discord.ext import commands

from text_checks import is_text_variant

IMAGE_PATH = "meme.png"
LAST_SENT: dict[int, float] = {}
RATE_LIMIT_SECONDS = 3


class BotConfig(TypedDict):
    verbose: bool


CONFIG: BotConfig = {"verbose": False}


@dataclass
class Event:
    triggers: tuple[str, ...]
    reply_pool: tuple[str, ...]

    def random_reply(self) -> str:
        return random.choice(self.reply_pool)


AUTISM_EVENT = Event(
    triggers=("autism", "autyzm", "autistic", "autystyk"),
    reply_pool=("Czy ktoś powiedział: autyzm??😳😳",),
)

MEOW_EVENT = Event(
    triggers=("meow", "miau", "nya", "purr", "mrrr"),
    reply_pool=("meow meow 🐱✨", "miau~ 😺💫", "kitty detected 🐈‍⬛👀"),
)

UWU_EVENT = Event(
    triggers=("uwu", "nuzzles"),
    reply_pool=("Pls no furry roleplay 🙏😔",),
)

FEMBOY_EVENT = Event(
    triggers=("femboj", "femboy", "femboi"),
    reply_pool=("Uuuu ... femboyy ✨",),
)

FURRY_EVENT = Event(
    triggers=("furry", "fursuit", "fursona"),
    reply_pool=("Furry detected - commencing ICBM strike.... 🚀💀",),
)

ANNOYING_CHANNEL_ID = 1472578525486780457
ANNOYING_EVENTS = (MEOW_EVENT, UWU_EVENT, FEMBOY_EVENT, FURRY_EVENT)


async def do_reply(message: discord.Message, event: Event) -> bool:
    if not is_text_variant(message.content, event.triggers, verbose=CONFIG["verbose"]):
        return False

    try:
        await message.reply(event.random_reply())
        print(f"Sent response to channel {message.channel.id}")
        LAST_SENT[message.channel.id] = time.time()
        return True
    except Exception as e:
        print("Failed to send:", e)
        return False


async def dispatch_annoying_event(message: discord.Message) -> bool:
    shuffled_events = random.sample(ANNOYING_EVENTS, len(ANNOYING_EVENTS))

    for event in shuffled_events:
        if await do_reply(message, event):
            return True

    return False


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} — ready.")


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    ch_id = message.channel.id
    now = time.time()
    last = LAST_SENT.get(ch_id, 0)

    if now - last < RATE_LIMIT_SECONDS:
        return

    if random.random() < 0.7:  # 70% chance to reply
        await do_reply(message, AUTISM_EVENT)

    # Check mentions
    if bot.user in message.mentions or message.mention_everyone:

        # Ignore replies to the bot's messages
        if message.reference and message.reference.resolved:
            if getattr(message.reference.resolved, "author", None) == bot.user:
                return

        LAST_SENT[ch_id] = now
        try:
            await message.reply(file=discord.File(IMAGE_PATH))
            print(f"Sent image to channel {ch_id}")
        except Exception as e:
            print("Failed to send image:", e)

    # Restricing all event functionalities
    # to the annoying channel to avoid spamming
    # other channels with memes and replies
    if ch_id == ANNOYING_CHANNEL_ID:
        await dispatch_annoying_event(message)

    await bot.process_commands(message)


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging for text matching.")
def main(verbose: bool) -> None:
    CONFIG["verbose"] = verbose

    if verbose:
        print("Verbose mode enabled.")

    token = Path("token").read_text().strip()
    bot.run(token)
