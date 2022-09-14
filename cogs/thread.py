# Python 3.10

# Main CraftBot class
import craftbot
# Discord API
import discord
from discord.ext import commands
from discord import slash_command, Option
# Built-in Python libraries
import os


class ThreadCog(commands.Cog):
    env_guild_ids = [int(os.environ["CRAFTBOT_GUILD_ID"])]

    def __init__(self, bot: craftbot.CraftBot):
        self.bot = bot
    
    group_thread = discord.SlashCommandGroup(name="thread", description="Commands for managing threads.", guild_ids=env_guild_ids)

    @group_thread.command(description="Rename the current thread.", guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def rename(self, ctx: discord.ApplicationContext, name: Option(str, "The new name for this thread.", required=True)):
        if type(ctx.channel) is discord.Thread:
            await ctx.interaction.channel.edit(name=name)
            await ctx.interaction.response.send_message(content="This thread has been renamed.")
        else:
            await ctx.interaction.response.send_message(content="Sorry, this command can only be used inside of a thread!")

    @group_thread.command(description="Archive the current thread.", guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def archive(self, ctx: discord.ApplicationContext):
        if type(ctx.channel) is discord.Thread:
            await ctx.interaction.response.send_message(content="This thread will be archived.")
            await ctx.interaction.channel.archive()
        else:
            await ctx.interaction.response.send_message(content="Sorry, this command can only be used inside of a thread!")


def setup(bot):
    bot.add_cog(ThreadCog(bot))