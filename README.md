# CraftBot
A custom Discord bot for the CraftWars Network which can report play times, link in-game and Discord chat, automatically manage threads for suggestions/requests, and register players.

#
### Setup
* Dependencies
    * Python 3.10+
    * [PyCord 2.1.3+](https://docs.pycord.dev/en/master/)
    * [Python-dotenv](https://pypi.org/project/python-dotenv/)
* Optional
    * [CraftWarsPlugin](https://github.com/cm-360/CraftWarsPlugin): Enables chat linking, registration, and play time reporting.
1. Clone this repository with `git clone https://github.com/cm-360/CraftBot.git`.
2. Create a file named `.env` in the root folder of the cloned repository and fill it out as follows:

    ```
    CRAFTBOT_GUILD_ID=your-discord-guild-id-goes-here
    CRAFTBOT_TOKEN=your-discord-bot-token-goes-here
    ```
3. Update `config.json` with the appropriate information for your server.
4. Start the bot with `python ./craftbot.py`.

#
### Configuration
The `.env` file holds the bot's Discord API token **(keep this private!)** and the ID of the guild it is in. Currently only one guild at a time is supported, although feel free to open a PR to add multi-guild functionality. All other configuration is done with `config.json`, which comes hard-coded with values from the CraftWars Discord server that will need to be changed.

#
### Licensing
This software is licensed under the terms of the GPLv3. You can find a copy of the license in the LICENSE file.
