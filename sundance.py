#sundance.py
#Created by Michael Scarfi
#
#Function: cordinate Raids and Fireteams

#import statements
import os
import discord
import traceback

from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime

import numpy as np

#load environment variables
load_dotenv()

#set Bot and Server Token variables
BotToken = os.getenv('BOT_TOKEN')
ServerToken = os.getenv('SERVER_TOKEN')

#create bot object
bot = commands.Bot(command_prefix='~')

# command to reload cogs
@bot.command(name='reload_cog', hidden=True)
@commands.is_owner()
async def reload_cog(ctx, module : str):
    """Reloads a module."""
    try:
        bot.reload_extension(module)
    except Exception as e:
        await ctx.send('\N{PISTOL}')
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('\N{OK HAND SIGN}')


#this event dictates the actions the bot takes when it connects.
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    guild = bot.guilds[0]

    #code to confirm the bot has connected to the proper server
    print (
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

    # Setting `Listening ` status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="commands | ~help"))

#load cogs
bot.load_extension('cogs.helper_cogs')
bot.load_extension('cogs.admin_cogs')
bot.load_extension('cogs.error_handling_cogs')
bot.load_extension('cogs.user_cogs')
bot.load_extension('cogs.loop_cogs')
bot.load_extension('cogs.destiny_api_cogs')

#execute Bot
bot.run(BotToken)