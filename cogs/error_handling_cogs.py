import discord
import traceback
import os
import errors

from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from json import JSONDecodeError
from discord import ChannelType
from google.cloud import error_reporting


class error_handling_cogs(commands.Cog):

    # this method runs on cog load
    def __init__(self, bot):
        self.bot = bot

        global bot_admin_code
        bot_admin_code = int(os.getenv('BOT_ADMIN_CODE'))

    #this event catches errors from commands
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error, unhandled_by_cog=True):
        print(f'error occured and was caught by on_command_error')
        #import global variables
        global bot_admin_code

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        #grab admin user object
        admin = self.bot.get_user(bot_admin_code)

        #grab the name of the command that the user tried to execute
        #this is grabbing what the user typed, taking the first word, and then removing the "~"
        command_name = ctx.message.content.split()[0].strip("~")

        # check if error is from errors.py
        if isinstance(error, errors.Error):
            await ctx.message.author.create_dm()
            await ctx.message.author.dm_channel.send(f'{str(error)}')
            print(f'Error: {str(error)}')

        #checking if user tried to run server commands through DMs
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.message.author.create_dm()
            await ctx.message.author.dm_channel.send(f'Command {command_name} cannot be run in via DMs.  It must be run in a Server.')

        #because we only have role checks we know if the checks fail it was a role error
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.message.author.create_dm()
            await ctx.message.author.dm_channel.send(f'You do not have access to use {command_name}.')

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

        elif isinstance(error, JSONDecodeError):
            #grab time for error message
            now = datetime.now().time()

            await admin.create_dm()
            await admin.dm_channel.send(f'JSON decode error occured at {now}')

        #check to see if they user was trying to cross out a message and accidentally triggered the bot, if not, delete their message
        else:
            #inform user an unkown error occured
            await ctx.message.author.create_dm()
            await ctx.message.author.dm_channel.send(f'Unkown error, please retry your command or contact <@{bot_admin_code}> for assistance.')
            
            #grab time for error message
            now = datetime.now().time()

            #send error message to bot admin
            await admin.create_dm()
            guild = ctx.guild
            Error_Message = f'Command error occured at {now}\n'
            if guild is discord.Guild:
                Error_Message += 'Server: {ctx.guild.name}\nChannel: {ctx.message.channel.name}\n'
            await admin.dm_channel.send(Error_Message + f'User: {ctx.message.author.name}\nMessage: {ctx.message.content}\nTraceback: {error.__traceback__}\nError: ' + '{}: {}'.format(type(error).__name__, error))



        #check to see if they user was trying to cross out a message and accidentally triggered the bot, if not, send report to Google cloud platform and delete their message
        if(ctx.message.content.split()[0][1] != "~"):
            client = error_reporting.Client()
            try:
                raise error
            except Exception as err:
                message = traceback.format_exception(None, err, err.__traceback__, limit=None, chain=True)
                client.report(message, user = str(ctx.message.author.id))
            # delete command message to keep channels clean if not a dm and bot has permissions
            if ctx.channel.type is ChannelType.text and ctx.guild.me.guild_permissions.manage_messages:
                await ctx.message.delete()

            raise error
            

    #this event catches errors from event coroutines 
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        #import global variables
        global bot_admin_code

        #grab admin user object
        admin = self.bot.get_user(bot_admin_code)
        
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



def setup(bot):
    bot.add_cog(error_handling_cogs(bot))