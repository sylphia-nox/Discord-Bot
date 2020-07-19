import discord
import traceback
import os
import errors

from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv

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
            print(f'Custom error: {str(error)}')

        #because we only have role checks we know if the checks fail it was a role error
        elif isinstance(error, commands.errors.CheckFailure):
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
            await admin.dm_channel.send(f'Command error occured at {now}\nUser: {ctx.message.author.name}\nMessage: {ctx.message.content}\nTraceback: {traceback.format_exc()}\nError: ' + '{}: {}'.format(type(error).__name__, error))

            #delete message that caused error to keep channels clean
            await ctx.message.delete()

            raise error

        #check to see if they user was trying to cross out a message and accidentally triggered the bot, if not, delete their message
        if(ctx.message.content.split()[0][1] != "~"):
            #delete message that caused error to keep channels clean
            await ctx.message.delete()

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