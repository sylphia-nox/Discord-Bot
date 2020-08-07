# this cog defines Admin commands for the bot and relies on helper_cogs.py for functionality

# import statements
import os
import discord

from dotenv import load_dotenv
from discord.ext import commands, tasks

class admin_cogs(commands.Cog, name='Admin Commands'):
    
    # get admin role code for command checks.
    admin_role_codes = ["null"]

    # this method runs on cog load
    def __init__(self, bot):
        self.bot = bot


        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, admin_cogs failed to load helper_cogs.py')

        self.initialize_admin_role_codes()
     

    # this is a utility command to refresh a raid post based on data in MySQL DB
    @commands.command(name='refresh', help='type ~refresh and the raid info will be refreshed')
    @commands.has_any_role(admin_role_codes)
    async def refresh(self, ctx, raid_id: int):
        # call utility
        await helpers.print_raid(raid_id, ctx.guild.id)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows a user with certain privileges to delete Raids
    @commands.command(name='delete', help='type ~delete #, this command is only available to admin users.')
    @commands.has_any_role(admin_role_codes)
    async def delete(self, ctx, raid_id: int):
        # call utility
        await helpers.delete_raid(raid_id, ctx.guild.id)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows an admin user to add someone to a raid post
    @commands.command(name='add', help='type add @usertag # #, where # # is the raid ID followed by the spot to add them to that raid.')
    @commands.has_any_role(admin_role_codes)
    async def add(self, ctx, user: discord.Member, raid_id: int, spot_id: int):
        # call add user utility
        await helpers.add_user_to_raid(user, raid_id, ctx.guild.id, ctx.message.author, spot_id)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows an admin user to remove someone from a raid post
    @commands.command(name='remove', help='type remove @usertag #, where # is the raid ID to remove the tagged user from the raid')
    @commands.has_any_role(admin_role_codes)
    async def remove(self, ctx, user: discord.Member, raid_id: int):
        # call utility
        await helpers.remove_user(user, raid_id, ctx.guild.id, ctx.message.author)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows an admin user to reschedule a raid
    @commands.command(name='reschedule', hidden = True)
    @commands.has_any_role(admin_role_codes)
    async def reschedule(self, ctx, raid_id: int, new_time: str):
        # call utility to change time
        await helpers.change_raid_time(ctx.message.author, raid_id, ctx.guild.id, new_time)
        
        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows a server admin to configure the raid_channel
    @commands.command(name='setup_raid_posts', hidden = True)
    @commands.has_permissions(administrator = True)
    async def setup_raid_posts(self, ctx, admin_role: discord.Role, destiny_folk: discord.Role,  channel: discord.TextChannel = None):
        if channel is None:
            channel_id = "null"
        else:
            channel_id = channel.id

        # call utility to setup channel
        await helpers.setup_server(channel_id, admin_role.id, destiny_folk.id, ctx.guild.id)
        
        # reload admin role codes
        await self.update_admin_role_codes()

        # delete command message to keep channels clean
        await ctx.message.delete()

    # syncronous method to initialize admin role codes on cog load.
    def initialize_admin_role_codes(self):
        sqlreturn = helpers.query_db_sync('SELECT `admin_role_code` FROM `guilds`;')
        self.admin_role_codes = [] 
        for val in sqlreturn: 
            if val[0] != None : 
                self.admin_role_codes.append(int(val[0])) 
        print (self.admin_role_codes)
  
    # async helper function to update global admin_role_codes for 
    async def update_admin_role_codes(self):
        sqlreturn = await helpers.query_db('SELECT `admin_role_code` FROM `guilds`;')
        self.admin_role_codes = [] 
        for val in sqlreturn: 
            if val[0] != None: 
                self.admin_role_codes.append(int(val[0]))





def setup(bot):
    bot.add_cog(admin_cogs(bot))