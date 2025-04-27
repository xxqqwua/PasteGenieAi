import os

import disnake
from disnake.ext import commands
from disnake.ext.commands import slash_command

from dotenv import load_dotenv
import datetime

from .ReportSystem import error_messages

import logging
import logging_config

logger = logging.getLogger(__name__)
load_dotenv()
pfp_url = os.getenv("pfp_url")


class InfoCMDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Get bot ping")
    async def ping(self, inter):
        try:
            latency = int(self.bot.latency * 1000)

            await inter.send(f"Bot ping: {latency}ms", delete_after=30, ephemeral=True)
        except Exception as error:
            await error_messages(inter, self.bot, error, "ping")

    @slash_command(description="Get information about the bot")  # Calls embed
    async def help(self, inter):
        try:
            embed = await info_embed(self.bot)
            if embed is not None:
                await inter.send(embed=embed, delete_after=60)
            else:
                await inter.send(f"Couldn't get the delay, try again later")

        except Exception as error:
            await error_messages(inter, self.bot, error, "ping")


async def info_embed(bot):
    from database.db_manager import DBManager

    db = DBManager("PasteGenie.db")
    db.connect()

    current_copypastes_numbers = db.get_last_paste_id()[0]
    current_custom_copypastes_numbers = db.get_last_paste_id(is_ai=False)[0]
    current_servers_number = len(bot.guilds)
    latency = int(bot.latency * 1000)

    embed = disnake.Embed(
        title="Paste Genie Ai 🧞‍♂️",
        description="""
            **Your magical assistant for creating creative copypastas!**
            Generate unique texts for any request and share them with friends.
            
            **🎯 Main Commands**

            > **/create from idea** — Create a new copypasta using AI
            > **/add paste** — Add your own custom copypasta to the database
            > **/paste by id** — Find and display a previously created copypasta
            > **/generate from messages** — Create a copypasta based on messages
            > **/author pastes** — View all copypastas by a specific author

            **📊 Additional Features**
        
            > **/ratings** — Popularity ratings for copypastas and authors
            > **/report** — Report inappropriate content
            > **/help** — Show this guide
            > **/ping** — Check the bot's response time
        """,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick roll; could be changed to another website
        color=disnake.Colour.light_embed(),
        timestamp=datetime.datetime.now(),
    )

    embed.set_thumbnail(url=pfp_url)
    embed.set_footer(text="Make your server more fun with Paste Genie AI! 🧞", icon_url=pfp_url)

    embed.add_field(
    name="📈 Bot Statistics:",
    value=f"""
        **🤖 Generated copypastas:** `{current_copypastes_numbers:,}`
        **📝 User-added copypastas:** `{current_custom_copypastes_numbers:,}`
        **🌐 Servers:** `{current_servers_number:,}`
        **⚡ Ping:** `{latency} ms`
    """,
    inline=False)

    return embed


def setup(bot):
    bot.add_cog(InfoCMDs(bot))
