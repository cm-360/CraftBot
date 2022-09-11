# Python 3.10

# Main CraftBot class
import craftbot
# Discord API
import discord
from discord.ext import commands
from discord import slash_command, Option, OptionChoice
# Built-in Python libraries
import os, re, typing


class RegistrationCog(commands.Cog):
    env_guild_ids = [int(os.environ["CRAFTBOT_GUILD_ID"])]

    def __init__(self, bot: craftbot.CraftBot):
        self.bot = bot

    @slash_command(description="Add a user to the server whitelist.", guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def register(self, ctx: discord.ApplicationContext,
            username: Option(str, "The Minecraft username to register.", required=True),
            account_type: Option(str, "The type of account to register. (Java or Bedrock)", required=True),
            account_owner: Option(discord.User, "The server member owning the specified username.", required=False)):
        account_type = account_type.lower()
        # Ensure valid account type parameter
        if account_type in ["java", "bedrock"]:
            # Check username format
            if re.match(r"\w{3,16}$", username) is not None:
                # Account owner parameter is optional
                if account_owner is None:
                    self._register(username, account_type, None)
                    await ctx.interaction.response.send_message(content="Registered {0} Edition username '{1}'.".format(account_type.capitalize(), username))
                else:
                    self._register(username, account_type, account_owner.id)
                    await ctx.interaction.response.send_message(content="Registered {0} Edition username '{1}' as belonging to {2.mention}.".format(account_type.capitalize(), username, account_owner))
            else:
                await ctx.interaction.response.send_message(content="'{0}' is not a valid Minecraft username!".format(username))
        else:
            await ctx.interaction.response.send_message(content="The parameter 'account_type' must be either 'java' or 'bedrock'!")

    @slash_command(description="Remove a user from the server whitelist.", guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def unregister(self, ctx: discord.ApplicationContext,
            username: Option(str, "The Minecraft username to unregister.", required=True),
            account_type: Option(str, "The type of account to unregister. (Java or Bedrock)", required=True)):
        account_type = account_type.lower()
        # Ensure valid account type parameter
        if account_type in ["java", "bedrock"]:
            # Check username format
            if re.match(r"\w{3,16}$", username) is not None:
                self._unregister(username, account_type)
                await ctx.interaction.response.send_message(content="Unregistered {0} Edition username '{1}'.".format(account_type.capitalize(), username))
            else:
                await ctx.interaction.response.send_message(content="'{0}' is not a valid Minecraft username!".format(username))
        else:
            await ctx.interaction.response.send_message(content="The parameter 'account_type' must be either 'java' or 'bedrock'!")

    @slash_command(description="Lookup an existing registration.", guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def lookup(self, ctx: discord.ApplicationContext,
            username: Option(str, "The Minecraft username to lookup.", required=True),
            account_type: Option(str, "The type of account to lookup. (Java or Bedrock)", required=True)):
        account_type = account_type.lower()
        # Lookup username registrations
        rows = self._lookup_username(username, account_type).fetchall()
        if len(rows) > 0:
            # Build results
            results_string = "**{0} Edition registrations for {1}**".format(account_type.capitalize(), username)
            for row in rows:
                user = await self.bot.get_or_fetch_user(int(row[3]))
                if user is not None:
                    results_string += "\n" + user.display_name + " (ID: " + str(user.id) +")"
                else:
                    results_string += "\n" + str(row[3])
            # Reply to command sender
            await ctx.interaction.response.send_message(content=results_string)
        else:
            # Reply to command sender
            await ctx.interaction.response.send_message(content="No existing {0} Edition registrations found for {1}.".format(account_type.capitalize(), username))

    @slash_command(description="List all existing registrations.", guild_ids=env_guild_ids)
    @commands.check(craftbot.CraftBot.is_admin)
    async def registrations(self, ctx: discord.ApplicationContext):
        # Lookup username registrations
        rows = self._list_registrations().fetchall()
        if len(rows) > 0:
            # Build results
            results_string = "**Account Registrations**"
            for row in rows:
                # Format result string
                results_string += "\n{0} ({1} Edition): ".format(row[0], row[1].capitalize())
                # Append owner name
                if row[3] is not None:
                    user = await self.bot.get_or_fetch_user(int(row[3]))
                    if user is not None:
                        results_string += user.display_name + " (ID: " + str(user.id) +")"
                    else:
                        results_string += str(row[3])
                else:
                    results_string += "No owner"
            # Reply to command sender
            await ctx.interaction.response.send_message(content=results_string)
        else:
            # Reply to command sender
            await ctx.interaction.response.send_message(content="No existing registrations found.")

    # Registers a Minecraft username
    def _register(self, username: str, account_type: str, account_owner: int = None):
        # Insert row to register username
        self.bot.database.execute("INSERT INTO mc_accounts (username, type, owner) VALUES (?, ?, ?);", [username, account_type, account_owner])
        self.bot.database.commit()
        # Add to server whitelist
        self.bot.send_udp_message("register", "{0} {1}".format(account_type, username))

    # Unregisters a Minecraft username
    def _unregister(self, username: str, account_type: str):
        # For case-insensitive checking
        username = username.lower()
        # Delete appropriate rows
        self.bot.database.execute("DELETE FROM mc_accounts WHERE lower(username) = ? AND type = ?;", [username, account_type])
        self.bot.database.commit()
        # Remove from server whitelist
        self.bot.send_udp_message("unregister", "{0} {1}".format(account_type, username))

    # Lookup any existing registrations of a Minecraft username
    def _lookup_username(self, username: str, account_type: str):
        # For case-insensitive checking
        username = username.lower()
        # Select all matching rows
        return self.bot.database.execute("SELECT * FROM mc_accounts WHERE lower(username) = ? AND type = ?;", [username, account_type])

    # Lookup any existing registrations belonging to a Discord guild member
    def _lookup_member(self, member_id: int):
        # Select all matching rows
        return self.bot.database.execute("SELECT * FROM mc_accounts WHERE owner = ?;", [member_id])

    def _list_registrations(self):
        return self.bot.database.execute("SELECT * FROM mc_accounts;")

    def _check_registration_username(self, username: str, account_type: str):
        return len(self._lookup_username(username, account_type)) > 0

    def _check_registration_member(self, member_id: int):
        return len(self._lookup_member(member_id)) > 0


def setup(bot):
    bot.add_cog(RegistrationCog(bot))