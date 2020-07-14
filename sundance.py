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

#set channel codes, raid channel is where Raids are published, sun channel is for diagnostic messages
bot_admin_code = int(os.getenv('BOT_ADMIN_CODE'))

#create bot object
bot = commands.Bot(command_prefix='~')

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

#this event catches errors from commands
@bot.event
async def on_command_error(ctx, error):
    print(f'error occured and was caught by on_command_error')
    #import global variables
    global bot_admin_code

    #grab admin user object
    admin = bot.get_user(bot_admin_code)

    #grab the name of the command that the user tried to execute
    #this is grabbing what the user typed, taking the first word, and then removing the "~"
    command_name = ctx.message.content.split()[0].strip("~")

    #because we only have role checks we know if the checks fail it was a role error
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'You do not have the correct role to use {command_name}.')

    #checking if the input was bad
    elif isinstance(error, commands.BadArgument):
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Incorrect arguments for command: {command_name}, type `~help {command_name}` for more information.')

    #checking if the command is missing arguments
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Missing arguments for command: {command_name}, type `~help {command_name}` for more information.')

    #check if user was trying to cross-out text and so triggered the bot.  If so, this is not an error.
    elif (ctx.message.content.split()[0][1] == "~"):
        #not an error do nothing 
        print(f'not an error.  Someone was using cross-out notation.')

    #check to see if they user was trying to cross out a message and accidentally triggered the bot, if not, delete their message
    else:
        #inform user an unkown error occured
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Unkown error, please retry your command or contact <@{bot_admin_code}> for assistance.')
        
        #grab time for error message
        now = datetime.now().time()

        #send error message to server admin
        await admin.create_dm()
        await admin.dm_channel.send(f'Command error occured at {now}\nUser: {ctx.message.author.name}\nMessage: {ctx.message.content}\nTraceback: {traceback.format_exc()}\nError: {error}')

    #check to see if they user was trying to cross out a message and accidentally triggered the bot, if not, delete their message
    if(ctx.message.content.split()[0][1] != "~"):
        #delete message that caused error to keep channels clean
        await ctx.message.delete()

#this event catches errors from event coroutines 
@bot.event
async def on_error(event, *args, **kwargs):
    #import global variables
    global bot_admin_code

    #grab admin user object
    admin = bot.get_user(bot_admin_code)
    
    #Gets the message object
    message = args[0] 
    
    #grab time for error message
    now = datetime.now().time()

    #inform user an error occured
    await message.author.create_dm()
    await message.author.dm_channel.send(f'An error occured, please correct your input and try again.  If the issue continues to occur please contact <@{bot_admin_code}>.')

    #send error message to server admin
    await admin.create_dm()
    await admin.dm_channel.send(f'On_message error occured at {now}\nUser: {message.author.name}\nMessage: {message.content}\nError: {traceback.format_exc()}')

#load cogs
bot.load_extension('cogs.helper_cogs')
bot.load_extension('cogs.admin_cogs')
bot.load_extension('cogs.user_cogs')
bot.load_extension('cogs.loop_cogs')

#execute Bot
bot.run(BotToken)