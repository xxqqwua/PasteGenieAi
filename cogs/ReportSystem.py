import disnake
from disnake.ext import commands
from disnake.ext.commands import slash_command

import datetime

import logging
import logging_config

logger = logging.getLogger(__name__)


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Report an error or bug")
    async def report(self, inter, reason: str, time: str):
        report_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await inter.response.send_message(f"Report sent successfully to the owner: \nReason: {reason} \nTime: {time}",
                                          ephemeral=True)
        owner = self.bot.get_user(self.bot.owner_id)
        await owner.send(
            f"Manual report from {inter.author.name} \nReport time: {report_time} \n---Users info--- \nReason: {reason} \nTime: {time}")
        logger.info(
            f"Manual report from {inter.author.name} \nReport time: {report_time} \n---Users info--- \nReason: {reason} \nTime: {time}")


class ReportButton(disnake.ui.View):
    def __init__(self, inter, bot, error, function):
        super().__init__(timeout=30.0)
        self.error = error
        self.inter = inter
        self.bot = bot
        self.function = function

    @disnake.ui.button(label="Report", style=disnake.ButtonStyle.primary, emoji="🚨")
    async def report_button_callback(self, button: disnake.ui.Button, inter):
        # Check if the user who pressed the button is the same as the user who created the paste
        if inter.author.id != self.inter.author.id:
            return await inter.response.send_message("You can't use this button", ephemeral=True)

        report_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await inter.response.send_message("Report sent successfully to the owner!", ephemeral=True)
        owner = self.bot.get_user(self.bot.owner_id)
        await owner.send(
            f"Report throw button from {inter.author.name} \nReport time: {report_time} \nFuction: {self.function} \n---Users info--- \nReason: {self.error}")
        logger.info(
            f"Report throw button from {inter.author.name} \nReport time: {report_time} \n---Users info--- \nReason: {self.error}")


async def error_messages(inter, bot, error, func_name):  # Error messages template
    view = ReportButton(inter, bot, error, func_name)
    logger.error(f'User {inter.author.name} entered the "{func_name}" command and got an error: "{error}"')

    await inter.send(content=f'''
    An unexpected error occurred during task execution: "{error}"
    Repeat your request later or enter another idea.
    You can report if you think it is a important error!
    ''', view=view, ephemeral=True, delete_after=120)


def setup(bot):
    bot.add_cog(Reports(bot))
