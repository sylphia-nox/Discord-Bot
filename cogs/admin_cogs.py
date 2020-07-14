from discord.ext import commands
#import statements
import os
import discord
import mysql.connector
import traceback

from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.tasks import loop
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.parser import ParserError

import numpy as np

class admin_cogs(commands.Cog, name='Admin Commands'):
    
    #set channel codes, raid channel is where Raids are published, sun channel is for diagnostic messages
    sun_chan_code = int(os.getenv('SUN_CHAN_CODE'))
    #raid_chan_code = int(os.getenv('RAID_CHAN_CODE')) 
    raid_chan_code = int(os.getenv('TEST_RAID_CHAN'))  #secondary channel for testing
    admin_role_code = int(os.getenv('ADMIN_ROLE_CODE'))
    bot_admin_code = int(os.getenv('BOT_ADMIN_CODE'))

    def __init__(self, bot):
        self.bot = bot

        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, failed to load helper_cogs.py')

        global mycursor
        global mydb
        # global sun_chan_code
        # global raid_chan_code
        # global admin_role_code
        # global bot_admin_code

        #create DB connection
        mydb = mysql.connector.connect(
            host = os.getenv('DB_HOST'),
            user = os.getenv('DB_USER'),
            passwd = os.getenv('DB_PASSWD'),
            database = os.getenv('DATABASE'),
            auth_plugin='mysql_native_password'
        )

        #create object to access DB connection
        mycursor = mydb.cursor()

        

    #this is a utility command to refresh a raid post based on data in MySQL DB
    @commands.command(name='refresh', help='type ~refresh and the raid info will be refreshed')
    @commands.has_role(admin_role_code)
    async def refresh(self, ctx, raid_id: int):
        global helpers

        await helpers.print_raid(raid_id)

        #delete command message to keep channels clean
        await ctx.message.delete()

    #this command allows a user with certain privileges to delete Raids
    @commands.command(name='delete', help='type ~delete #, this command is only available to admin users.')
    @commands.has_role(admin_role_code)
    async def delete(self, ctx, raid_id: int):
        global helpers

        await helpers.delete_raid(raid_id)

        #delete command message to keep channels clean
        await ctx.message.delete()

    #this command allows an admin user to add someone to a raid post
    @commands.command(name='add', help='type add @usertag # #, where # # is the raid ID followed by the spot to add them to that raid.')
    @commands.has_role(admin_role_code)
    async def add(self, ctx, user: discord.Member, raid_id: int, spot_id: int):
       

        #call add user command
        await helpers.add_user_to_raid(user, raid_id, ctx.message.author, spot_id)

        #delete command message to keep channels clean
        await ctx.message.delete()

    #this command allows an admin user to remove someone from a raid post
    @commands.command(name='remove', help='type remove @usertag #, where # is the raid ID to remove the tagged user from the raid')
    @commands.has_role(admin_role_code)
    async def remove(self, ctx, user: discord.Member, raid_id: int):
        await helpers.remove_user(user, raid_id, ctx.message.author)

        #delete command message to keep channels clean
        await ctx.message.delete()

    #this command allows an admin user to reschedule a raid
    @commands.command(name='reschedule', hidden = True)
    @commands.has_role(admin_role_code)
    async def reschedule(self, ctx, raid_id: int, new_time: str):
        print (f'Raid ID: {raid_id} new_time string: {new_time}')

        #create DM channel for user, creating now so except clauses can also use.
        await ctx.message.author.create_dm()

        try:
            #if the input is invalid it will throw either ParserError, ValueError, or Overflow Error
            raid_time = parse(new_time, fuzzy=True)

            #update DB with "when" value
            sql = "UPDATE raid_plan SET time = %s WHERE idRaids = %s"
            val = (f'{raid_time.strftime("%I:%M %p %m/%d")}', raid_id)
            mycursor.execute(sql, val)

            #DM user that raid setup is complete
            await ctx.message.author.dm_channel.send(f'raid {raid_id} rescheduled to {raid_time.strftime("%I:%M %p %m/%d")}')

            #edit raid post to show new data
            await helpers.print_raid(raid_id)

        #catching the error handling to notify user if their input was invalid
        except ParserError:
            await ctx.message.author.dm_channel.send(f'not a date time input, please try again')
        except ValueError:
            await ctx.message.author.dm_channel.send(f'invalid input, please try again')
        except OverflowError:
            await ctx.message.author.dm_channel.send(f'date time values exceed possible values, please try again')

        #delete command message to keep channels clean
        await ctx.message.delete()
    


def setup(bot):
    bot.add_cog(admin_cogs(bot))