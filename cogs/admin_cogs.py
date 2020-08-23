# this cog defines Admin commands for the bot and relies on helper_cogs.py for functionality

# import statements
import os
import discord

from dotenv import load_dotenv
from discord.ext import commands, tasks
from cogs.helper_cogs import helper_cogs

class admin_cogs(commands.Cog, name='Admin Commands'):
    
    # get admin role code for command checks.
    sqlreturn = helper_cogs.query_db_sync(None, 'SELECT `admin_role_code` FROM `guilds`;')
    admin_role_codes = [] 
    for val in sqlreturn: 
        if val[0] != None : 
            admin_role_codes.append(int(val[0])) 

    # this method runs on cog load
    def __init__(self, bot):
        self.bot = bot


        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, admin_cogs failed to load helper_cogs.py')

     

    # this is a utility command to refresh a raid post based on data in MySQL DB
    @commands.command(name='refresh', hidden = True)
    @commands.has_any_role(*admin_role_codes)
    @commands.guild_only()
    async def refresh(self, ctx, raid_id: int):
        # call utility
        await helpers.print_raid(raid_id, ctx.guild.id)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows a user with certain privileges to delete Raids
    @commands.command(name='delete', brief = "`~delete <raid #>`", help='type ~delete #, this command is only available to admin users.')
    @commands.has_any_role(*admin_role_codes)
    @commands.guild_only()
    async def delete(self, ctx, raid_id: int):
        # call utility
        await helpers.delete_raid(raid_id, ctx.guild.id)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows an admin user to add someone to a raid post
    @commands.command(name='add', brief = "`~add @usertag <raid #> <spot #>`", help='type add @usertag # #, where # # is the raid ID followed by the spot to add them to that raid.')
    @commands.has_any_role(*admin_role_codes)
    @commands.guild_only()
    async def add(self, ctx, user: discord.Member, raid_id: int, spot_id: int):
        # call add user utility
        await helpers.add_user_to_raid(user, raid_id, ctx.guild.id, ctx.message.author, spot_id)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows an admin user to remove someone from a raid post
    @commands.command(name='remove', brief = "`~remove @usertag <spot number>`", help='type remove @usertag #, where # is the raid ID to remove the tagged user from the raid')
    @commands.has_any_role(*admin_role_codes)
    @commands.guild_only()
    async def remove(self, ctx, user: discord.Member, raid_id: int):
        # call utility
        await helpers.remove_user(user, raid_id, ctx.guild.id, ctx.message.author)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows an admin user to reschedule a raid
    @commands.command(name='reschedule', brief = "`~reschedule <new time>`", help = 'type `~reschedule <new time>`, new time must be a parsable time or date/time.')
    @commands.has_any_role(*admin_role_codes)
    @commands.guild_only()
    async def reschedule(self, ctx, raid_id: int, new_time: str):
        # call utility to change time
        await helpers.change_raid_time(ctx.message.author, raid_id, ctx.guild.id, new_time)
        
        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command allows a server admin to configure the raid_channel
    @commands.command(name='setup', brief = "~setup",help ='~setup` The bot will request the needed information.')
    @commands.has_permissions(administrator = True)
    @commands.guild_only()
    async def setup_raid_posts(self, ctx, admin_role: discord.Role = None, destiny_folk: discord.Role = None,  channel: discord.TextChannel = None):
        admin_role, destiny_folk, channel = await helpers.ask_for_server_options(ctx)
        
        if channel is None:
            channel_id = "null"
        else:
            channel_id = channel.id
        if admin_role is None: admin_role = ctx.guild.default_role
        if destiny_folk is None: destiny_folk = ctx.guild.default_role

        # call utility to setup channel
        await helpers.setup_server(channel_id, admin_role.id, destiny_folk.id, ctx.guild.id)

        # delete command message to keep channels clean
        await ctx.message.delete()

        # inform admin setup is complete
        await ctx.message.channel.send("Setup complete")

        # reload the cog to reset decorator values
        self.bot.reload_extension("cogs.admin_cogs")

    
    @commands.command(name='servers', brief = '`~servers`', help = "`~servers`: displays servers connected to Sundance.")
    @commands.is_owner()
    async def servers(self, ctx):
        # Display connected servers
        message = f'{self.bot.user} is connected to the following guild:\n'
        for guild in self.bot.guilds:
            message += f'{guild.name}(id: {guild.id})\n'
        await ctx.message.channel.send(message)

    @commands.command(name='public_update', brief = '`~bot_update`', help = "`~bot_update`: sends a DM to server owners.")
    @commands.is_owner()
    async def public_update(self, ctx, message: str):
        # Display connected servers
        for guild in self.bot.guilds:
            owner = guild.owner
            await owner.create_dm()
            await owner.dm_channel.send(message)
        

def setup(bot):
    bot.add_cog(admin_cogs(bot))