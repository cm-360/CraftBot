# Python 3.10

# PyCord API
import discord
from discord.ext import commands
from discord.commands import slash_command, Option
# Asynchronous Minecraft RCON library
from async_mcrcon import MinecraftClient, InvalidPassword
# SQLite database library
import sqlite3
# Library to load variables from the '.env' file
import dotenv
# Built-in Python libraries
import asyncio, datetime as date, json, math, os, re, socket, sys, threading



def log_message(location: str, message: str):
    print("[{0}] [{1}] {2}".format(date.datetime.now().strftime(r"%d-%m-%Y %H:%M:%S"), location, message))

def log_exception(location: str, details: str, exception: Exception):
    log_message(location, details)
    log_message(location, "{0}: {1}".format(type(exception).__name__, exception))
    traceback = exception.__traceback__
    while traceback:
        log_message(location, "  {0}: {1}".format(traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))
        traceback = traceback.tb_next
    if exception.__cause__ is not None:
        log_exception(location, "Caused by", exception.__cause__)


# Deep search a dictionary for the value associated with a dot-delimited key
def search_get_dict(dictionary: dict, dotted_key: str):
    key_split = re.split(r"\.", dotted_key, 1)
    if len(key_split) > 1:
        subdictionary = dictionary.get(key_split[0], None)
        if subdictionary is not None:
            return search_get_dict(subdictionary, key_split[1])
        else:
            return None
    else:
        return dictionary.get(key_split[0], None)

# Deep search a dictionary to set a value associated with a dot-delimited key
def search_set_dict(dictionary: dict, dotted_key: str, value) -> bool:
    key_split = re.split(r"\.", dotted_key, 1)
    if len(key_split) > 1:
        subdictionary = dictionary.get(key_split[0], None)
        if subdictionary is not None:
            return search_set_dict(subdictionary, key_split[1], value)
        else:
            return False
    else:
        dictionary[key_split[0]] = value
        return True

# Splits the first word from the given string
def split_prefix(string: str) -> str:
    return re.split(r"\s+", string, 1)



# Our custom bot implementation :)
class CraftBot(discord.Bot):

    def __init__(self):
        super().__init__()
        # Cached embed data
        self.embed_data = {}
        self.message_cache = {}
        # Cogs
        self.cog_names = ["cogs.control", "cogs.thread", "cogs.registration"]
        # Load environment variables
        dotenv.load_dotenv()
        # Load bot configuration file
        if self.init_config("config.json"):
            # Connect to SQLite database
            if self.init_sqlite("data.db"):
                # Load cogs
                self.init_cogs()
                # Start UDP server thread
                threading.Thread(target=self.run_udp, args=(self.get_config_value("udp.listen_address"), int(self.get_config_value("udp.listen_port")))).start()
            else:
                raise Exception("Failed to initialize bot!")
        else:
            raise Exception("Failed to initialize bot!")

    # Load the config from the specified file
    def init_config(self, config_file_path: str) -> bool:
        try:
            config_file = open(config_file_path, 'r', encoding="utf-8")
            self.config = json.loads(config_file.read())
            config_file.close()
            return True
        except Exception as e:
            log_exception("Init", "Failed to load bot config!", e)
        return False

    # Save the config to the specified file
    def save_config(self, config_file_path: str) -> bool:
        try:
            config_file = open(config_file_path, 'w', encoding="utf-8")
            config_file.write(json.dumps(self.config, indent=4, sort_keys=True))
            config_file.close()
            return True
        except Exception as e:
            log_exception("Saving", "Failed to save bot config!", e)
        return False

    # Read a value from the config
    def get_config_value(self, key: str):
        return search_get_dict(self.config, key)

    # Set a value in the config
    def set_config_value(self, key: str, value) -> bool:
        return search_set_dict(self.config, key, value)

    # Connect to the specified SQLite database file
    def init_sqlite(self, db_file_path: str) -> bool:
        try:
            self.database = sqlite3.connect(db_file_path)
            self.database.row_factory = sqlite3.Row
            log_message("Init", "Connected to SQLite database, running version " + sqlite3.version)
            try:
                # Create table
                # self.database.execute("DROP TABLE mc_accounts;")
                self.database.execute("""
                        CREATE TABLE IF NOT EXISTS mc_accounts (
                            username TEXT NOT NULL,
                            type TEXT NOT NULL,
                            uuid TEXT UNIQUE,
                            owner INTEGER
                        );
                    """)
                self.database.commit()
                return True
            except sqlite3.Error as e:
                log_exception("Init", "Error while creating database tables!", e)
        except sqlite3.Error as e:
            log_exception("Init", "Error while connecting to SQLite database!", e)
        return False

    # Save the SQLite database to the specified file
    def save_sqlite(self, db_file_path: str) -> bool:
        return False

    def init_cogs(self) -> bool:
        success = True
        for cog_name in self.cog_names:
            try:
                self.load_extension(cog_name)
                log_message("Init", "Loaded cog '{0}'".format(cog_name))
            except Exception as e:
                success = False
                log_exception("Init", "Failed to load cog '{0}'!".format(cog_name), e)
        return success

    def reload_cogs(self) -> bool:
        success = True
        for cog_name in self.cog_names:
            try:
                self.reload_extension(cog_name)
                log_message("Init", "Reloaded cog '{0}'".format(cog_name))
            except Exception as e:
                success = False
                log_exception("Cogs", "Failed to reload cog '{0}'!".format(cog_name), e)
        return success

    # Start listening on the specified UDP port
    def run_udp(self, address: str, port: int):
        try:
            self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            self.udp_socket.bind((address, port))
            log_message("Init", "UDP socket bound to {0}:{1}".format(address, port))
            while True:
                try:
                    data = self.udp_socket.recv(4096)
                    asyncio.run_coroutine_threadsafe(self.on_udp_message(data.decode("utf-8")), self.loop)
                except socket.error:
                    # No data was received
                    pass
        except Exception as e:
            log_exception("Init", "Error while handling UDP socket!", e)

    def run_bot(self):
        self.run(os.environ["CRAFTBOT_TOKEN"])

    async def on_ready(self):
        # Fetch some helpful variables
        config_guild_id = int(os.environ["CRAFTBOT_GUILD_ID"])
        self.guild = self.get_guild(config_guild_id)
        if self.guild is not None:
            # Print bot info
            log_message("Event", "CraftBot Info:")
            log_message("Event", "  API Version: \t{0}".format(discord.__version__))
            log_message("Event", "  User Info: \t{0.name}#{0.discriminator} (ID: {0.id})".format(self.user))
            log_message("Event", "  Guild Info: \t{0.name} (ID: {0.id})".format(self.guild))
            log_message("Event", "  Prefix: \t{0}".format(self.get_config_value("prefix")))
            # Set bot activity
            await self.change_presence(activity=discord.Game("Minecraft"))
        else:
            log_message("Event", "Failed to fetch guild {0}!".format(config_guild_id))

    async def on_message(self, message):
        try:
            # Prevent bot from replying to itself
            if message.author != self.user:
                # Check if message was sent directly to the bot
                if type(message.channel) in [discord.DMChannel, discord.GroupChannel]:
                    pass
                else:
                    if type(message.channel) == discord.Thread:
                        pass
                    else:
                        # These modules don't need to process messages from other bots, as it could cause issues!
                        if not message.author.bot:
                            # Chat forwarding channel
                            if message.channel.id == self.get_config_value("modules.chat.channel_id"):
                                # Forward message to in-game chat
                                self.send_udp_message("chat", "{0.name}#{0.discriminator} {1}".format(message.author, message.clean_content))
                            # Help channel
                            elif message.channel.id == self.get_config_value("modules.help.channel_id"):
                                # Create thread for message and greet user
                                thread = await message.create_thread(name=self.get_config_value("modules.help.formats.thread_title").format(message))
                                await thread.send(self.get_config_value("modules.help.formats.message_greeting").format(message))
                            # Suggestions channel
                            elif message.channel.id == self.get_config_value("modules.suggestions.channel_id"):
                                # Create thread for message, add voting reactions, and greet user
                                thread = await message.create_thread(name=self.get_config_value("modules.suggestions.formats.thread_title").format(message))
                                await message.add_reaction(self.get_config_value("modules.suggestions.formats.reaction_upvote"))
                                await message.add_reaction(self.get_config_value("modules.suggestions.formats.reaction_downvote"))
                                await thread.send(self.get_config_value("modules.suggestions.formats.message_greeting").format(message))
                            # Whitelist channel
                            # elif message.channel.id == self.get_config_value("modules.whitelist.channel_id"):
                            #     # Add reactions and greet user
                            #     await message.add_reaction(self.get_config_value("modules.whitelist.formats.reaction_java"))
                            #     await message.add_reaction(self.get_config_value("modules.whitelist.formats.reaction_bedrock"))
                            #     await message.channel.send(self.get_config_value("modules.whitelist.formats.message_greeting").format(message))
        except Exception as e:
            log_exception("Event", "Error while processing received message!", e)

    # async def on_reaction_add(self, reaction, user):
    #     message = reaction.message
    #     try:
    #         # Prevent bot from replying to itself
    #         if user != self.user:
    #             # Whitelist channel
    #             if message.channel.id == self.get_config_value("modules.whitelist.channel_id"):
    #                 await message.channel.send(reaction.emoji)
    #     except Exception as e:
    #         log_exception("Event", "Error while processing received message!", e)   

    async def on_command_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.interaction.response.send_message(content="You are not able to run this command!")
        else:
            craftbot.log_exception("Command", "An error occured while proccessing a command.", error)
            await ctx.interaction.response.send_message(content="An unspecified error has occured. Please check the log for details.")

    async def on_udp_message(self, message):
        try:
            # Split message into parts
            message_split = message.split("\0", 2)
            message_type = message_split[1]
            message_content = message_split[2]
            # print("Received UDP packet")
            # print("  Type:\t%s" % message_type)
            # print("  Content:\t%s" % message_content)
            # Fetch appropriate guild
            if self.guild is not None:
                message_types_chat = {"chat": ("**{0[0]}**: {0[1]}", 1), "chat_system": ("*{0[0]}*", 0)}
                message_types_stat = {"playerlist": self.parse_playerlist, "playtimes": self.parse_playtimes}
                # Perform action based on message type
                if message_type in message_types_chat:
                    chat_channel_id = self.get_config_value("modules.chat.channel_id")
                    chat_channel = self.guild.get_channel(chat_channel_id)
                    if chat_channel and type(chat_channel) is discord.TextChannel:
                        message_format, split_limit = message_types_chat.get(message_type)
                        await chat_channel.send(message_format.format(message_content.split(" ", split_limit)))
                    else:
                        log_message("UDP", "Could not find the linked chat text channel with ID %d!" % chat_channel_id)
                elif message_type in message_types_stat:
                    # Cache response
                    self.message_cache[message_type] = message_content
                    self.embed_data[message_type] = message_types_stat.get(message_type)(message_content)
                    # Locate channel of player list message
                    stats_channel_id = self.get_config_value("modules.stats.channel_id")
                    stats_channel = self.guild.get_channel(stats_channel_id)
                    if stats_channel is not None and type(stats_channel) == discord.TextChannel:
                        # Locate player list message to edit
                        stats_message_id = self.get_config_value("modules.stats.message_id")
                        if stats_message_id is not None:
                            stats_message = await stats_channel.fetch_message(stats_message_id)
                            if stats_message is not None:
                                await stats_message.edit(embed=self.generate_playerstats_embed(message_types_stat))
                                return
                        # Channel or message could not be found
                        stats_message = await stats_channel.send(embed=self.generate_playerstats_embed(message_types_stat))
                        self.set_config_value("modules.stats.message_id", stats_message.id)
                    else:
                        log_message("UDP", "Could not find the player list text channel with ID %d!" % stats_channel_id)
                else:
                    log_message("UDP", "Unrecognized message type '%s'" % message_type)
            else:
                log_message("UDP", "This guild does not exist!")
        except Exception as e:
            log_exception("UDP", "Error while processing UDP message!", e)

    def send_udp_message(self, message_type: str, message_content: str) -> bool:
        address, port = (self.get_config_value("udp.sendto_address"), self.get_config_value("udp.sendto_port"))
        try:
            self.udp_socket.sendto("\0".join([message_type, message_content]).encode(errors="replace"), (address, port))
            return True
        except Exception as exc:
            print("Failed to send UDP packet!")
            print("  Destination:\t{0}:{1}".format(address, port))
            print("  Type:\t%s" % message_type)
            print("  Content:\t%s" % message_content)
            print(exc)
            print(exc.__traceback__)
        return False

    def generate_playerstats_embed(self, content_parsers) -> discord.Embed:
        embed = discord.Embed(title="**Player Stats**", colour=discord.Colour.from_rgb(255, 170, 0), timestamp=date.datetime.now(tz=date.timezone.utc))
        for field_type in content_parsers.keys():
            field_name, field_content = self.embed_data.get(field_type, content_parsers.get(field_type)(self.message_cache.get(field_type, "")))
            embed.add_field(name=field_name, value=field_content, inline=False)
        return embed

    def parse_playerlist(self, message: str) -> tuple[str, str]:
        playerlist = ["No players online"]
        if message is not None and len(message) > 0:
            playerlist = message.split(",")
        return ("**Currently Online**", "\n".join(["```"] + playerlist + ["```"]))

    def parse_playtimes(self, message: str, count=10) -> tuple[str, str]:
        timeslist = ["No data"]
        if message is not None and len(message) > 0:
            timeslist = []
            for i,item in enumerate(message.split(",")[:count]):
                username, playtime = item.split(" ", 1)
                timeslist.append(("{0:<%d} {1:<18} {2}h {3}m" % (len(str(count)) + 1)).format(str(i + 1) + ".", username + ":", math.floor(int(playtime) / (1000 * 60 * 60)), round(int(playtime) / (1000 * 60)) % 60))
        return ("**Playtime Rankings**", "\n".join(["```"] + timeslist + ["```"]))

    # Checks if the user of the specified context is an admin here or not
    async def is_admin(ctx: discord.ApplicationContext) -> bool:
        author = ctx.author
        admin_list = ctx.bot.get_config_value("admin")
        # Check if user specifically is an admin
        if author.id in admin_list["users"]:
            return True
        # Check if user has an admin role
        if isinstance(author, discord.Member) and any(role in admin_list["roles"] for role in author.roles):
            return True
        # Checks failed :(
        return False



if __name__ == "__main__":
    # Start bot
    CraftBot().run_bot()