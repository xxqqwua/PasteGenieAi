import disnake

from disnake.ext import commands
from disnake.ext.commands import slash_command

from database.db_manager import DBManager


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description='stats description')
    async def stats(self, inter, author_name_or_id: str):
        import datetime
        global user_stats
        await inter.response.defer()

        db = DBManager("PasteGenie.db")
        db.connect()

        # Remove mention tags from author_name_or_id if present
        author_name_or_id = author_name_or_id.strip("<@").strip(">")

        if author_name_or_id == 'me':
            author_name_or_id = inter.author.id

        # Try to find author by name or ID
        author = db.search_user_by_name(author_name_or_id) or db.get_user_database_id(author_name_or_id)

        if author:
            user_stats = db.get_users_stats(author[0] if isinstance(author[0], int) else author[0][0])
            db.close()

            if user_stats:
                pastes_amount, views_amount, likes_amount = user_stats
                embed = disnake.Embed(
                    title=f"Stats of {author_name_or_id}",
                    color=disnake.Colour.light_embed(),
                    timestamp=datetime.datetime.now(),
                    description=f"""
                    **Total number of copy pastes:** {pastes_amount or 0}
                    **Total number of views:** {views_amount or 0}
                    **Total number of likes:** {likes_amount or 0}
                    """
                )
                await inter.edit_original_response(embed=embed)
            else:
                await inter.edit_original_response(
                    f"Author '{author_name_or_id}' don't have any pastes.",
                    delete_after=30
                )
        else:
            await inter.edit_original_response("Author not found.", delete_after=15)


def setup(bot):
    bot.add_cog(Stats(bot))
