import disnake
from disnake.ext import commands
from disnake.ext.commands import slash_command

from AI.AnswerGenerator import ai_answer_generator
from database.db_manager import DBManager
from .ReportSystem import error_messages

import logging
import logging_config

logger = logging.getLogger(__name__)


class PasteGenerator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # generate from idea slash command
    @slash_command()
    async def create(self, inter):
        pass

    @create.sub_command_group(name='from')
    async def by(self, inter):
        pass

    @by.sub_command(name='idea', description="For creating internet paste, does not support “bad words”, RACISM, NAZISM, ETC.")
    async def generate(self, inter, idea: str):  # "idea" - user-entered text for the paste, an idea for it
        try:
            await inter.response.defer()

            db = DBManager("PasteGenie.db")
            db.connect()

            last_copypaste_id = db.get_last_paste_id()[0]
            last_copypaste_id += 1
            user_discord_id = inter.author.id
            user_discord_name = inter.author.name

            if db.is_exist(user_discord_id) is False:
                db.create_user(user_discord_id, user_discord_name)
            user_database_id = db.get_user_database_id(user_discord_id)[0]

            logger.info(
                f'Generator command was used by {inter.author.name} and idea was "{idea[:99]}", #{last_copypaste_id}')

            answer = await ai_answer_generator(idea)
            if answer == 'Error while getting answer. Please contact developers.':
                return await inter.edit_original_response("Can't generate paste right now, try again later",
                                                          delete_after=15)

            if db.uniqueness_check(answer, is_ai=False):
                return await inter.edit_original_response("This paste content already exists, try another!",
                                                          delete_after=15)

            answer_length = len(answer)
            logger.debug(f'Answer was "{answer[:25]}" and length was {answer_length}')

            base_message = await inter.edit_original_response(f"Generated paste for {inter.author.mention}")
            thread_name = f"#{last_copypaste_id} Generated paste by {inter.author.name}, idea: {idea}"
            thread = await base_message.create_thread(name=thread_name[:99], auto_archive_duration=60)

            if answer_length > 2000:
                for i in range(0, answer_length, 2000):  # Iterate over the answer in chunks of 2000 characters
                    await thread.send(answer[i:i + 2000])
            else:
                await thread.send(content=answer)

            current_paste_db_id = db.create_paste(user_database_id, answer, idea=idea)
            db.close()

            view = ReGenerator(self.bot, inter, current_paste_db_id, idea)
            embed = disnake.Embed(description="Click the button below to regenerate the paste:", color=0x4752c4)
            await thread.send(embed=embed, view=view)

        except Exception as error:
            await error_messages(inter, self.bot, error, "generate")

    # generate from messages slash command
    @slash_command()
    async def generator(self, inter):
        pass

    @generator.sub_command_group(name='from')
    async def byy(self, inter):
        pass

    @byy.sub_command(name='messages', description="For creating internet paste, does not support “bad words”, RACISM, NAZISM, ETC.")
    async def generator_from_channel(self, inter, amount: int):
        if amount > 50:
            return await inter.response.send_message("You can't put more than 50 messages at once", ephemeral=True)

        if not isinstance(inter.channel, disnake.DMChannel):
            msg_list = []
            async for message in inter.channel.history(limit=amount):
                if message.author == self.bot.user:
                    continue

                msg_list.append(message.content)

            if len(msg_list) == 0:
                return await inter.response.send_message("Can't find any messages", ephemeral=True)

            await self.generate(inter, idea=msg_list)

        else:
            await inter.response.send_message("You can't use this command in DM", ephemeral=True)


class ReGenerator(disnake.ui.View):  # Regenerate button
    def __init__(self, bot, inter, current_paste_db_id, idea: str):
        super().__init__(timeout=1800.0)
        self.inter = inter
        self.idea = idea
        self.bot = bot
        self.current_paste_db_id = current_paste_db_id

    @disnake.ui.button(label="ReGenerate", style=disnake.ButtonStyle.primary, emoji="🔄")
    async def regenerate(self, button: disnake.ui.Button, inter):
        try:
            await inter.response.defer()

            db = DBManager("PasteGenie.db")
            db.connect()

            # Check if the user who pressed the button is the same as the user who created the paste
            if inter.author.id != self.inter.author.id:
                return await inter.response.send_message("You can't use this button", ephemeral=True)

            logger.info(f'ReGenerator command was used by {inter.author.name} and content was "{self.idea[:99]}"')
            await inter.edit_original_message("### Paste is regenerating now, please wait...", embed=None, view=None)

            answer = await ai_answer_generator(self.idea)
            answer_length = len(answer)
            logger.debug(f'Answer was "{answer[:25]}" and length was {answer_length}')

            if answer_length > 2000:
                for i in range(0, answer_length, 2000):
                    await inter.channel.send(answer[i:i + 2000])
            else:
                await inter.channel.send(content=answer)

            db.update_paste(self.current_paste_db_id, answer)
            db.close()

            view = ReGenerator(self.bot, inter, self.current_paste_db_id, self.idea)
            embed = disnake.Embed(description="Click the button below to regenerate the paste:", color=0x4752c4)
            await inter.channel.send(embed=embed, view=view)

        except Exception as error:
            await error_messages(inter, self.bot, error, "regenerator")


def setup(bot):
    bot.add_cog(PasteGenerator(bot))
