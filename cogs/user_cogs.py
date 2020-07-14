# this cog defines User commands for the bot and relies on helper_cogs.py for functionality

#import statements
import os
import discord
import mysql.connector
import traceback

from discord.ext import commands
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.parser import ParserError

class user_cogs(commands.Cog, name='User Commands'):
    
    def __init__(self, bot):
        self.bot = bot

        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, user_cogs failed to load helper_cogs.py')

        #global variables to allow the bot to know if raid setup is ongoing and its state
        global raid_setup_active
        global raid_setup_step
        global raid_setup_what

        raid_setup_active = False
        raid_setup_step = "what"
        raid_setup_what = 1


    #this event activates on all messages but is for DM messages for setting up a raid, everything else goes through commands
    @commands.Cog.listener()
    async def on_message(self, message):
        global raid_setup_active
        global raid_setup_user
        global raid_setup_step
        global raid_setup_id
        global raid_setup_what

        #check if raid setup is active, if not ignore
        if(raid_setup_active):
            #check to see if the message is a DM from the raid_setup_user
            if message.channel.type is discord.ChannelType.private and message.author == raid_setup_user:
                #Check what state the raid setup is in.
                if(raid_setup_step == "what"):
                    #try loop to catch non int-parsable input, all other exceptions will trigger on_error event and send exception to admin user
                    try:
                        # get number of current raids
                        sqlreturn = await helpers.query_db("SELECT COUNT(*) FROM raid_info")

                        # checking to confirm the response is valid
                        if (int(message.content) <= int(sqlreturn[0][0])):
                            raid_setup_id = int(message.content)

                            # prompt user for time in DM channel
                            await raid_setup_user.dm_channel.send(f'When is the raid?')

                            # set global variable to "when" to change the event response
                            raid_setup_step = "when"

                        # if the answer is not valid, reprompt user and do not change state
                        else:
                            await raid_setup_user.dm_channel.send(f'Invalid choice, please choose a number from the list')

                    # except block to catch ValueError if user does not provide int-parsable input
                    except ValueError:
                        await raid_setup_user.dm_channel.send(f'Your input is not a number, please provide valid input')

                # elif check if raid setup is in "when" state
                elif(raid_setup_step == "when"):
                    try:
                        # if the input is invalid it will throw either ParserError, ValueError, or Overflow Error
                        raid_time = parse(message.content, fuzzy=True)

                        await helpers.create_raid(raid_setup_what, raid_time)

                        # DM user that raid setup is complete
                        await raid_setup_user.dm_channel.send(f'raid setup complete')

                        # reset global variables for next raid setup
                        raid_setup_active = False
                        raid_setup_step = "what"

                        # Reset boss display status
                        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="commands | ~help"))

                    #catching the error handling to notify user if their input was invalid
                    except ParserError:
                        await raid_setup_user.dm_channel.send(f'not a date time input, please try again')
                    except ValueError:
                        await raid_setup_user.dm_channel.send(f'invalid input, please try again')
                    except OverflowError:
                        await raid_setup_user.dm_channel.send(f'date time values exceed possible values, please try again')


    #this command creates a new raid post, user needs to respond to DMs to complete setup.
    @commands.command(name='raid', help='Type ~raid and the bot will create a new raid post for you')
    async def raid(self, ctx):
        #declare global variables used in command
        global raid_setup_active
        global raid_setup_user 
        global raid_setup_step

        #setting global variable values for new raid setup
        raid_setup_active = True
        raid_setup_user = ctx.message.author
        raid_setup_step = "what"

        #ask the user which raid they want to do via DM
        await helpers.which_raid_question(raid_setup_user)

        # Setting `Playing ` status to show bot is setting up a raid
        await self.bot.change_presence(activity=discord.Game(name="setting up a raid"))

        #delete command message to keep channels clean
        await ctx.message.delete()
 

    #this command allows a user to join a raid.
    @commands.command(name='join', help='type ~join # # First number is the raid id to join followed by the spot you would like to take (1-6 for primary 7-8 for backup)')
    async def join(self, ctx, raid_id: int, spot: int):
        # call utility
        await helpers.add_user_to_raid(ctx.message.author, raid_id, ctx.message.author, spot)

        #delete command message to keep channels clean
        await ctx.message.delete()

    #command to allow a user to leave the raid, it will remove the user from the first spot it finds them in.
    @commands.command(name='leave', help='type ~leave # and you will be removed from that raid')
    async def leave(self, ctx, raid_id: int):
        # call utility
        await helpers.remove_user(ctx.message.author, raid_id, ctx.message.author)

        #delete command message to keep channels clean
        await ctx.message.delete()


def setup(bot):
    bot.add_cog(user_cogs(bot))