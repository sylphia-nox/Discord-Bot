#sundance.py
#Created by Sylphia Nox
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

#set Bot Token variables
BotToken = os.getenv('BOT_TOKEN')
version = os.getenv('BOT_VERSION')

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
        await ctx.send('Cog reloaded')

# command to reload cogs
@bot.command(name='load_cog', hidden=True)
@commands.is_owner()
async def load_cog(ctx, module : str):
    """Reloads a module."""
    try:
        bot.load_extension(module)
    except Exception as e:
        await ctx.send('\N{PISTOL}')
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Cog loaded')

# command to reload cogs
@bot.command(name='unload_cog', hidden=True)
@commands.is_owner()
async def unload_cog(ctx, module : str):
    """Reloads a module."""
    try:
        bot.unload_extension(module)
    except Exception as e:
        await ctx.send('\N{PISTOL}')
        await ctx.send('{}: {}'.format(type(e).__name__, e))
    else:
        await ctx.send('Cog unloaded')


#this event dictates the actions the bot takes when it connects.
@bot.event
async def on_ready():
    bot.owner_id = int(os.getenv('BOT_ADMIN_CODE'))

    # Display connected servers
    print(f'{bot.user.name} has connected to Discord!')
    print(f'{bot.user} is connected to the following guild:\n')
    for guild in bot.guilds:
        print (f'{guild.name}(id: {guild.id})\n')
    
    try:
        import googleclouddebugger
        googleclouddebugger.enable(
            module='Sundance.py',
            version=  version,
            breakpoint_enable_canary=False
        )
    except ImportError:
        pass
    

    # Setting `Listening` status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="commands | ~help"))


@bot.event
async def on_guild_join(guild):
    owner = guild.owner
    await owner.create_dm()
    await owner.dm_channel.send(f'Thank you for adding Sundance to the Server!\nPlease use `~setup` to configure the bot.')
    print(f'Bot added to server: {guild.name} ({guild.id})')


#load cogs
bot.load_extension('cogs.helper_cogs')
bot.load_extension('cogs.destiny_api_caller_cogs') 
bot.load_extension('cogs.destiny_api_helper_cogs')
bot.load_extension('cogs.admin_cogs')
bot.load_extension('cogs.error_handling_cogs')
bot.load_extension('cogs.user_cogs')
bot.load_extension('cogs.loop_cogs')
bot.load_extension('cogs.destiny_api_cogs')

#execute Bot
bot.run(BotToken)
