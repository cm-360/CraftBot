# Python 3.10

# Main CraftBot class
import craftbot
# Discord API
import discord
from discord.ext import commands
from discord import slash_command, Option
# Built-in Python libraries
import os


class ControlCog(commands.Cog):
    env_guild_ids = [int(os.environ['CRAFTBOT_GUILD_ID'])]

    def __init__(self, bot: craftbot.CraftBot):
        self.bot = bot

    @slash_command(description='Reload this bot\'s cogs.', guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def reload_cogs(self, ctx: discord.ApplicationContext):
        if self.bot.reload_cogs():
            await ctx.interaction.response.send_message(content='Reloaded all cogs!')
        else:
            await ctx.interaction.response.send_message(content='An error occured while reloading cogs, check the log for details.')

    @reload_cogs.error
    async def reload_cogs_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.interaction.response.send_message(content='You do not have permission to run this command!')
        else:
            await ctx.interaction.response.send_message(content='An unspecified error has occured. Please check the log for details.')


def setup(bot):
    bot.add_cog(ControlCog(bot))