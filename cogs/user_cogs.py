# this cog defines User commands for the bot and relies on helper_cogs.py for functionality

# import statements
import discord

from discord.ext import commands
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.parser import ParserError
import asyncio

# create cog and define name
class user_cogs(commands.Cog, name='User Commands'):
    
    # method that defines cog function startup.
    def __init__(self, bot):
        self.bot = bot

        # import utility functions
        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, user_cogs failed to load helper_cogs.py')


    # this command creates a new raid post, user needs to respond to DMs to complete setup.
    @commands.command(name='raid', help='Type ~raid and the bot will create a new raid post for you')
    async def raid(self, ctx):
        # setting global variable values for new raid setup
        raid_setup_user = ctx.message.author
        server_id = ctx.guild.id
        channel_id = ctx.message.channel.id
        raid_number = 0
        raid_time = ""
        note = ""

        # ask the user which raid they want to do via DM
        await helpers.which_raid_question(raid_setup_user)

        # Setting `Playing ` status to show bot is setting up a raid
        await self.bot.change_presence(activity=discord.Game(name="setting up a raid"))

        # try loop to catch async timeout if user does not respond in a timely fashion.
        try:
            while raid_number == 0:
                # wait for user to responsd with which raid they want to join
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.type is discord.ChannelType.private)
                # try loop to catch non int-parsable input, all other exceptions will trigger on_error event and send exception to admin user
                try:
                    # get number of current raids
                    sqlreturn = await helpers.query_db("SELECT COUNT(*) FROM raid_info")

                    # checking to confirm the response is valid
                    if (int(msg.content) <= int(sqlreturn[0][0])):
                        raid_number = int(msg.content)

                        # prompt user for time in DM channel
                        await raid_setup_user.dm_channel.send(f'When is the raid?')

                    # if the answer is not valid, reprompt user and do not change state
                    else:
                        await raid_setup_user.dm_channel.send(f'Invalid choice, please choose a number from the list')
                # except block to catch ValueError if user does not provide int-parsable input
                except ValueError:
                    await raid_setup_user.dm_channel.send(f'Your input is not a number, please provide valid input')

            while raid_time == "":
                # wait for user to responsd with which raid they want to join
                msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.type is discord.ChannelType.private)

                try:
                    # if the input is invalid it will throw either ParserError, ValueError, or Overflow Error
                    raid_time = parse(msg.content, fuzzy=True)

                    # prompt user for optional message
                    await raid_setup_user.dm_channel.send(f'Any additional message concerning the raid? (Limite 140 characters, Respond with n if you do not have a message.)')
 
                # catching the error handling to notify user if their input was invalid
                except ParserError:
                    await raid_setup_user.dm_channel.send(f'not a date time input, please try again')
                except ValueError:
                    await raid_setup_user.dm_channel.send(f'invalid input, please try again')
                except OverflowError:
                    await raid_setup_user.dm_channel.send(f'date time values exceed possible values, please try again')

            
            # wait for user to responsd with which raid they want to join
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel.type is discord.ChannelType.private)

            if msg.content != "n" and msg.content != "no":
                note = msg.content[0:140]
 
        except asyncio.TimeoutError:
            await raid_setup_user.dm_channel.send(f'Raid creation has timed out, please start again.')           
        
        # create raid and raid post
        await helpers.create_raid(raid_number, raid_time, note, raid_setup_user.id, server_id, channel_id)

        # DM user that raid setup is complete
        await raid_setup_user.dm_channel.send(f'raid setup complete')

        # Reset boss display status
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="commands | ~help"))

        # delete command message to keep channels clean
        await ctx.message.delete()
 

    # this command allows a user to join a raid.
    @commands.command(name='join', help='type ~join # # First number is the raid id to join followed by the spot you would like to take (1-6 for primary 7-8 for backup)')
    async def join(self, ctx, raid_id: int, spot: int):
        # call utility
        await helpers.add_user_to_raid(ctx.message.author, raid_id, ctx.guild.id, ctx.message.author, spot)

        #delete command message to keep channels clean
        await ctx.message.delete()

    # command to allow a user to leave the raid, it will remove the user from the first spot it finds them in.
    @commands.command(name='leave', help='type ~leave # and you will be removed from that raid')
    async def leave(self, ctx, raid_id: int):
        
        # call utility
        await helpers.remove_user(ctx.message.author, raid_id, ctx.guild.id, ctx.message.author)

        #delete command message to keep channels clean
        await ctx.message.delete()

def setup(bot):
    bot.add_cog(user_cogs(bot))