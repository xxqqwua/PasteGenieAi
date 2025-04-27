import disnake
from disnake.ext import commands
from disnake.ext.commands import slash_command

from database.db_manager import DBManager
from .ReportSystem import *
from .PasteRating import *

import logging
import logging_config

logger = logging.getLogger(__name__)


class PastaHub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # paste by id slash command
    @slash_command()
    async def paste(self, inter):
        pass

    @paste.sub_command_group()
    async def by(self, inter):
        pass

    @by.sub_command(name='id', description="showme command text")
    async def showme(self, inter, is_ai: bool, paste_id: int):
        global paste
        try:
            await inter.response.defer()

            db = DBManager("PasteGenie.db")
            db.connect()

            paste = db.get_paste_info(paste_id, is_ai=is_ai)

            db.add_view_to_paste(paste_id, is_ai=is_ai)

            paste_content = paste[2]

            paste_length = len(paste_content)
            paste_author_database_id = paste[1]
            paste_author_name = db.get_user_name(paste_author_database_id)[0]
            db.close()

            logger.info(f"showme command was used by {inter.author.name} and paste id was #{paste_id}, is ai: {is_ai}")

            if is_ai:
                respond_text = f"Copy paste #{paste_id} for {inter.author.mention}. **Author idea of paste: {paste_author_name}**"
                thread_name = f"Copy paste #{paste_id} for {inter.author.name}, content: {paste_content}"
            else:
                respond_text = f"Custom copy paste #{paste_id} for {inter.author.mention}. **Paste author: {paste_author_name}**"
                thread_name = f"Custom copy paste #{paste_id} for {inter.author.name}, content: {paste_content}"

            base_message = await inter.edit_original_response(respond_text)
            thread = await base_message.create_thread(name=thread_name[:99])

            if paste_length > 2000:
                for i in range(0, paste_length, 2000):
                    await thread.send(content=paste_content[i:i + 2000])
            else:
                await thread.send(content=paste_content)

            embed = await create_embed(paste, is_ai)

            if is_ai:
                paste_idea = paste[6]
                embed.add_field(name="Paste idea", value=paste_idea)

            view = PasteLikesButton(inter, paste_id, is_ai)
            await thread.send(embed=embed, view=view)
            await thread.edit(archived=True)

        except Exception as e:
            await error_messages(inter, self.bot, e, "showme")

    # add paste slash command
    @slash_command()
    async def add(self, inter):
        pass

    @add.sub_command(name='paste', description="addpaste command text #2")
    async def addpaste(self, inter, text: str):
        try:
            await inter.response.defer()

            db = DBManager("PasteGenie.db")
            db.connect()

            last_paste_id = db.get_last_paste_id(is_ai=False)[0]
            last_paste_id += 1
            user_discord_id = inter.author.id
            user_discord_name = inter.author.name

            if db.is_exist(user_discord_id) is False:
                db.create_user(user_discord_id, user_discord_name)
            user_database_id = db.get_user_database_id(user_discord_id)[0]

            if db.uniqueness_check(text, is_ai=False):
                return await inter.edit_original_response("This paste content already exists, try another!",
                                                          delete_after=15)

            logger.info(
                f"addpaste command was used by {inter.author.name} and paste content was {text[:99]}, number #{last_paste_id}")

            base_message = await inter.edit_original_response(f"#{last_paste_id} addpaste by {inter.author.mention}")
            thread_name = f"Copy paste #{last_paste_id} for {inter.author.name}, content: {text})"
            thread = await base_message.create_thread(name=thread_name[:99])
            text_length = len(text)

            if text_length > 2000:
                for i in range(0, text_length, 2000):
                    await thread.send(text[i:i + 2000])
            else:
                await thread.send(content=text)
            await thread.edit(archived=True)

            db.create_paste(user_database_id, text, is_ai=False, idea=None)
            db.close()

        except Exception as e:
            await error_messages(inter, self.bot, e, "addpaste")

    # author pastes slash command
    @slash_command(name="author")
    async def author(self, inter):
        pass

    @author.sub_command(name='pastes', description="addpaste command text #1")
    async def showme_by_author(self, inter, is_ai: bool, author_name_or_id: str):
        """
        Спрашивать сначала нейм, если он введет неверно и БД не выдала ничего, то спрашивать по discord ID
        """
        await inter.response.defer()

        db = DBManager("PasteGenie.db")
        db.connect()

        if author_name_or_id.startswith("<@") and author_name_or_id.endswith(">"):
            author_name_or_id = author_name_or_id[2:-1]

        author = db.search_user_by_name(author_name_or_id)

        if author is not None:
            pastes = db.get_users_pastes(author[0], is_ai)
            db.close()

            if not pastes:
                await inter.edit_original_response(
                    f"Author '{author_name_or_id}' don't have any {'AI' if is_ai else 'custom'} pastes.",
                    delete_after=30
                )
                return

            view = PasteRatingButtons(self.bot, inter, pastes, is_ai)
            embed = await view.update_embed()

            await inter.edit_original_response(embed=embed, view=view)
        elif author is None:
            author_discord = db.get_user_database_id(author_name_or_id)
            if author_discord:
                author_database_id = author_discord[0]
                pastes = db.get_users_pastes(author_database_id, is_ai)
                db.close()

                if not pastes:
                    await inter.edit_original_response(
                        f"Author '{author_name_or_id}' don't have any {'AI' if is_ai else 'custom'} pastes.",
                        delete_after=30
                    )
                    return

                view = PasteRatingButtons(self.bot, inter, pastes, is_ai)
                embed = await view.update_embed(isUserRating=True)

                await inter.edit_original_response(embed=embed, view=view)
            else:
                await inter.edit_original_response("Author not found.", delete_after=15)


def setup(bot):
    bot.add_cog(PastaHub(bot))
