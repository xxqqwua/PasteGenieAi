import os

from dotenv import load_dotenv

import disnake
from disnake import DMChannel
from disnake.ext import commands

import logging
import logging_config

logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = commands.Bot(command_prefix=commands.when_mentioned_or("2chbot."), help_command=None,
                   intents=disnake.Intents.all())


# bot = commands.Bot(command_prefix=commands.when_mentioned_or("2chbot."), help_command=None,
#                    intents=disnake.Intents.all(), test_guilds=[983654886988206160])


async def cog_info(text, ctx):  # Displays the message and deletes the called message
    await ctx.send(text, delete_after=1)
    logger.info(text)
    if not isinstance(ctx.channel, DMChannel):
        await ctx.message.delete()


async def delete_messages(ctx, amount=None):
    if not isinstance(ctx.channel, DMChannel):
        await ctx.channel.purge()
    else:
        async for message in ctx.channel.history(limit=amount):
            if message.author == bot.user:
                await message.delete()
    await ctx.send("All messages were deleted", delete_after=1)


@bot.event
async def on_ready():  # When the bot is fully launched and ready to work, the output is this
    logger.info(f'''
        Bot {bot.user} is logged in
        Bot latency: {int(bot.latency * 1000)} ms
        Bot connected on {len(bot.guilds)} servers
                ''')


@bot.event
async def on_guild_join(guild):
    from cogs.InfoCMDs import info_embed
    embed = await info_embed(bot)

    system_channel = guild.system_channel
    if system_channel is None:
        for channel in guild.text_channels:
            try:
                await channel.send(embed=embed)
            except disnake.Forbidden:
                continue
            except disnake.HTTPException:
                continue
        else:
            logger.info(f"Couldn't find system channel or text channels in the guild: {guild.id}; {guild.name}")
    else:
        await system_channel.send(embed=embed)


# Commands for the owner to simplify testing and operation
@bot.command()
@commands.is_owner()
async def load(ctx, extension):  # coommand: 2chbot.load
    bot.load_extension(f"cogs.{extension}")
    await cog_info(f"Cog {extension} was loaded", ctx)


@bot.command()
@commands.is_owner()
async def unload(ctx, extension):  # coommand: 2chbot.unload
    bot.unload_extension(f"cogs.{extension}")
    await cog_info(f"Cog {extension} was unloaded", ctx)


@bot.command()
@commands.is_owner()
async def reload(ctx, extension):  # coommand: 2chbot.reload
    bot.reload_extension(f"cogs.{extension}")
    await cog_info(f"Cog {extension} was reloaded", ctx)


@bot.command()
@commands.is_owner()
async def reloadall(ctx):  # coommand: 2chbot.reloadall
    for filename in os.listdir("cogs"):
        if filename.endswith(".py"):
            bot.reload_extension(f"cogs.{filename[:-3]}")
            logging.info(f"Cog {filename[:-3]} was reloaded")
    await cog_info("All cogs were reloaded", ctx)


@bot.command()
@commands.is_owner()
async def delallmsg(ctx):  # coommand: 2chbot.delallmessages
    """
    Deletes all messages in the channel.
    Checks for DMs (direct messages), if the channel is a DM, it deletes only bots messages
    """

    await delete_messages(ctx)


@bot.command()
@commands.is_owner()
async def delmsg(ctx, amount: int):  # coommand: 2chbot.delmessages
    """
    Deletes the specified amount of messages in the channel.
    Checks for DMs (direct messages), if the channel is a DM, it deletes only bots messages
    """

    await delete_messages(ctx, amount)


for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")
        logger.info(f"Cog {filename[:-3]} was loaded")

if __name__ == '__main__':
    bot.run(TOKEN)
