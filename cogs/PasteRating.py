import disnake
from disnake.ext import commands
from disnake.ext.commands import slash_command

from database.db_manager import DBManager
from .ReportSystem import error_messages

import logging
import logging_config

logger = logging.getLogger(__name__)


class PasteRating(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='ratings', description="rate description")
    async def showrating(self, inter, is_ai: bool, rating: str = commands.Param(choices=["views", "likes", "created pastes"])):
        try:
            await inter.response.defer()
            global pastes

            db = DBManager("PasteGenie.db")
            db.connect()

            if rating == "views" or rating == "likes":
                if rating == "likes":
                    pastes = db.get_top_10_pastes_by_rating(is_ai=is_ai)
                elif rating == "views":
                    pastes = db.get_top_10_pastes_by_views(is_ai=is_ai)

                view = PasteRatingButtons(self.bot, inter, pastes, is_ai)
                embed = await view.update_embed()

                await inter.edit_original_response(embed=embed, view=view)
            else:
                import datetime
                top_10_users = db.get_top_10_users_by_amount_pastes(is_ai)

                embed = disnake.Embed(
                    title=f"Top 10 users by the number of created {'AI' if is_ai else 'custom'} pastes",
                    color=disnake.Colour.light_embed(),
                    timestamp=datetime.datetime.now(),
                )

                medals = ["1️⃣ ", "2️⃣ ", "3️⃣ ", "4️⃣ ", "5️⃣ ", "6️⃣ ", "7️⃣ ", "8️⃣ ", "9️⃣ ", "🔟 "]
                for author, amount in top_10_users:
                    embed.add_field(
                        name=f"{medals[top_10_users.index((author, amount))]} {db.get_user_name(author)[0]}:",
                        value=amount, inline=False)

                await inter.edit_original_response(embed=embed)
            db.close()
        except Exception as e:
            await error_messages(inter, self.bot, e, "showrating")


class PasteRatingButtons(disnake.ui.View):
    def __init__(self, bot, inter, pastes, is_ai):
        super().__init__(timeout=30.0)
        self.bot = bot
        self.inter = inter
        self.pastes = pastes
        self.is_ai = is_ai
        self.current_page = 0

    async def update_embed(self, isUserRating=False):
        paste = self.pastes[self.current_page]
        i = self.current_page + 1
        embed = await create_embed(paste, self.is_ai, i, isUserRating)
        embed.add_field(name="Content", value=paste[2][:500] + "...")

        if self.is_ai:
            paste_idea = paste[6]
            embed.add_field(name="Paste idea", value=paste_idea)

        return embed

    @disnake.ui.button(label="Previous", style=disnake.ButtonStyle.primary, emoji="⬅️")
    async def previous_button_callback(self, button: disnake.ui.Button, inter):
        if inter.author.id != self.inter.author.id:
            return await inter.response.send_message("You can't use this button", ephemeral=True)

        if self.current_page > 0:
            self.current_page -= 1
        await inter.response.edit_message(embed=await self.update_embed(), view=self)

    @disnake.ui.button(label="Check", style=disnake.ButtonStyle.green, emoji="👀")
    async def check_button_callback(self, button: disnake.ui.Button, inter):
        try:
            await inter.response.defer()

            if inter.author.id != self.inter.author.id:
                return await inter.response.send_message("You can't use this button", ephemeral=True)

            db = DBManager("PasteGenie.db")
            db.connect()

            paste = self.pastes[self.current_page]

            db.add_view_to_paste(paste[0])
            db.close()

            thread_name = f"Copy paste #{paste[0]} for {inter.author.name}, content: {paste[2]}"
            base_message = await inter.edit_original_message(f"#{paste[0]} checkpaste by {inter.author.mention}",
                                                             embed=None, view=None)
            thread = await base_message.create_thread(name=thread_name[:99])

            text_length = len(paste[2])
            if text_length > 2000:
                for i in range(0, text_length, 2000):
                    await thread.send(paste[2][i:i + 2000])
            else:
                await thread.send(content=paste[2])

            embed = await create_embed(paste, self.is_ai)

            if self.is_ai:
                paste_idea = paste[6]
                embed.add_field(name="Paste idea", value=paste_idea)

            view = PasteLikesButton(inter, paste[0], self.is_ai)
            await thread.send(embed=embed, view=view)

            await thread.edit(archived=True)

        except disnake.errors.NotFound:
            await inter.followup.send("This interaction has expired. Please start a new request.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in check_button_callback: {e}")
            await inter.followup.send("An error occurred while creating the thread.", ephemeral=True)

    @disnake.ui.button(label="Next", style=disnake.ButtonStyle.primary, emoji="➡️")
    async def next_button_callback(self, button: disnake.ui.Button, inter):
        if inter.author.id != self.inter.author.id:
            return await inter.response.send_message("You can't use this button", ephemeral=True)

        if self.current_page < len(self.pastes) - 1:
            self.current_page += 1
        await inter.response.edit_message(embed=await self.update_embed(), view=self)


class PasteLikesButton(disnake.ui.View):
    def __init__(self, inter, paste_id, is_ai):
        super().__init__(timeout=30.0)
        self.inter = inter
        self.paste_id = paste_id
        self.is_ai = is_ai

    @disnake.ui.button(label="Like", style=disnake.ButtonStyle.green, emoji="👍")
    async def like_button_callback(self, button: disnake.ui.Button, inter):
        db = DBManager("PasteGenie.db")
        db.connect()
        if await self.is_liked(db):
            return await inter.response.send_message("You already liked this paste!", ephemeral=True)
        db.connect()
        db.add_like_to_paste(self.paste_id, inter.author.id, is_ai=self.is_ai)
        db.close()
        await inter.response.send_message("Like added successfully!", ephemeral=True)

    async def is_liked(self, db):
        likes = db.get_who_likes_the_paste(self.paste_id, is_ai=self.is_ai)
        if not likes:
            pass
        if likes:
            likes = likes[0]
        if self.inter.author.id in likes:
            return True


async def create_embed(paste_to_check, is_ai, i=0, isUserRating=False):
    paste = paste_to_check
    db = DBManager("PasteGenie.db")
    db.connect()

    author = db.get_user_name(paste[1])[0]

    if isUserRating:
        if is_ai:
            ai_pastes_amount = len(db.get_users_pastes(paste[1]))
            embed_title = f"Paste #{paste[0]}  {i} of {ai_pastes_amount}"
        else:
            custom_pastes_amount = len(db.get_users_pastes(paste[1], is_ai=False))
            embed_title = f"Custom paste #{paste[0]}  {i} of {custom_pastes_amount}"
    else:
        if is_ai:
            embed_title = f"Paste #{paste[0]}"
        else:
            embed_title = f"Custom paste #{paste[0]}"
    db.close()

    embed = disnake.Embed(
        title=embed_title,
        description=f'''
        **Author of paste:** {author}
        **Rating:** {paste[4]}
        **Created at:** {paste[3]}
        **Views:** {paste[5]}
        ''',
        color=disnake.Colour.light_embed()
    )

    return embed


def setup(bot):
    bot.add_cog(PasteRating(bot))
