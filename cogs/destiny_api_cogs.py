# this cog defines the commands that interact with the Destiny 2 APIs, it relies on destiny_api_helper_cogs.py for functionality.

from discord.ext import commands
from datetime import datetime

class destiny_api_cogs(commands.Cog, name='Destiny Commands'): 
    
    # this method is called on loading of the cog.
    def __init__(self, bot):
        self.bot = bot

        # load Destiny helper cogs
        global destiny_helpers
        destiny_helpers = self.bot.get_cog('Destiny Utilities')
        if(destiny_helpers is None):
            print(f'Fatal error, Destiny_api_cogs failed to load destiny_api_helper_cogs')


    # this command shows a user their current power, highest power level of each equipement piece, and needed power to hit the next level.
    @commands.command(name = 'power', help = "`~power <steam_name> <class>` Class should be warlock/hunter/titan (not case sensitive).")
    async def power(self, ctx, steam_name: str, character: str, platform: int = 3):
        # get memberID and membershipType
        player_info = await destiny_helpers.get_member_info(steam_name, platform)
        
        # get player character info
        player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character)

        # declare list to hold items and get items
        items = await destiny_helpers.get_player_items(player_char_info)
        
        # get highest light for each slot
        high_items = await destiny_helpers.get_max_power_list(items)

        # get formatted message string
        embed = await destiny_helpers.format_power_message(high_items, player_char_info, steam_name)

        # send message to channel
        await ctx.send(embed = embed)

        # delete command message to keep channels clean
        await ctx.message.delete()

    @commands.command(name = 'next_power', help = "`~next_power <steam_name> <class>` Class should be warlock/hunter/titan (not case sensitive).")
    async def next_power(self, ctx, steam_name: str, character: str, platform: int = 3):
        
        # get memberID and membershipType
        player_info = await destiny_helpers.get_member_info(steam_name, platform)
        
        # get player character info
        player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character)
        
        # declare list to hold items and get items
        items = await destiny_helpers.get_player_items(player_char_info)
        
        # get highest light for each slot
        high_items = await destiny_helpers.get_max_power_list(items)
        
        # get message to send to channel
        embed = await destiny_helpers.format_power_message(high_items, player_char_info, steam_name)
        
        embed = await destiny_helpers.calculate_next_step(high_items, player_char_info, embed)
        

        # send message to channel
        await ctx.send(embed = embed)
        
        # delete command message to keep channels clean
        await ctx.message.delete()


    @commands.command(name = 'reload_manifest', hidden = True)
    @commands.is_owner()
    async def reload_manifest(self, ctx):
         # load manifest
        await destiny_helpers.get_manifest()

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this command sends users a url to authenticate with Bungie.net.
    @commands.command(name = 'authenticate', help = "`~authenticate`, Bot will DM you a link to authenticate with Bungie.net")
    async def authenticate(self, ctx):
        discordID = ctx.message.author.id
        
        url = f'https://destiny.scarfi.me:5000/api/v1/authenticate?id={discordID}'

        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Please use the below link to authenticate with Bungie.net:\n{url}')

        # delete command message to keep channels clean
        await ctx.message.delete()
    

def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))