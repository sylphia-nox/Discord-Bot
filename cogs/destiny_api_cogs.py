# this cog defines the commands that interact with the Destiny 2 APIs, it relies on destiny_api_helper_cogs.py for functionality.

from discord import ChannelType
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
    @commands.command(name = 'power', brief = "`~power <class> <steam_name:optional>`", help = "`~power<class> optional:<steam_name>` Steam_name is needed if you have not authenticated.  Class should be warlock/hunter/titan (not case sensitive). Advanced ~power <class> <account_name> <platform> (steam = 3, PSN = 2, XB = 1)")
    async def power(self, ctx, character: str, steam_name: str = "", platform: int = 3, OAuth = True):

        if steam_name == "":
            player_info = await destiny_helpers.get_member_info_Oauth(ctx.message.author.id)
            access_token = player_info[3]
        else:
            # get [memberID, membershipType, displayName]
            player_info = await destiny_helpers.get_member_info(steam_name, platform)

            if OAuth:
                # get access token for discordID/memberID combo
                access_token = await destiny_helpers.get_user_token(ctx.message.author.id, player_info[0])
                # if we got an error message back, set OAuth to False and continue
                if (access_token == "refresh token expired" or access_token == "token not found"):
                    OAuth = False
        
        # get player character info [memberID, membershipType, character_class, char_ids, char_id, emblem]
        player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character, OAuth, access_token)

        # declare list to hold items and get items
        items = await destiny_helpers.get_player_items(player_char_info, OAuth, access_token)
        
        # get highest light for each slot
        high_items = await destiny_helpers.get_max_power_list(items)

        # get formatted message string
        embed = await destiny_helpers.format_power_message(high_items, player_char_info, player_info[2])

        # send message to channel
        await ctx.send(embed = embed)

        # delete command message to keep channels clean if not a dm and bot has permissions
        if ctx.channel.type is ChannelType.text and ctx.message.channel.guild.me.guild_permissions.text.manage_messages:
            await ctx.message.delete()

    @commands.command(name = 'level', brief = "`~level <class> <steam_name:optional>`", help = "`~level <class> optional:<steam_name>` Steam_name is needed if you have not authenticated. Class should be warlock/hunter/titan (not case sensitive).  Advanced ~level <class> <account_name> <platform> (steam = 3, PSN = 2, XB = 1)")
    async def level(self, ctx, character: str, steam_name: str = "", platform: int = 3, OAuth = True):
        
        if steam_name == "":
            player_info = await destiny_helpers.get_member_info_Oauth(ctx.message.author.id)
            access_token = player_info[3]
        else:
            # get [memberID, membershipType, displayName]
            player_info = await destiny_helpers.get_member_info(steam_name, platform)

            if OAuth:
                # get access token for discordID/memberID combo
                access_token = await destiny_helpers.get_user_token(ctx.message.author.id, player_info[0])
                # if we got an error message back, set OAuth to False and continue
                if (access_token == "refresh token expired" or access_token == "token not found"):
                    OAuth = False

        # get player character info
        player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character, OAuth, access_token)
        
        # declare list to hold items and get items
        items = await destiny_helpers.get_player_items(player_char_info, OAuth, access_token)
        
        # get highest light for each slot
        high_items = await destiny_helpers.get_max_power_list(items)
        
        # get message to send to channel
        embed = await destiny_helpers.format_power_message(high_items, player_char_info, player_info[2])
        
        embed = await destiny_helpers.calculate_next_step(high_items, player_char_info, embed, OAuth, access_token)
        

        # send message to channel
        await ctx.send(embed = embed)
        
        # delete command message to keep channels clean if not a dm and bot has permissions
        if ctx.channel.type is ChannelType.text and ctx.message.channel.permissions_for(self.bot.user).manage_messages:
            await ctx.message.delete()


    @commands.command(name = 'reload_manifest', hidden = True)
    @commands.is_owner()
    async def reload_manifest(self, ctx):
         # load manifest
        await destiny_helpers.get_manifest()

        # delete command message to keep channels clean if not a dm and bot has permissions
        if ctx.channel.type is ChannelType.text and ctx.message.channel.permissions_for(self.bot.user).manage_messages:
            await ctx.message.delete()

    # this command sends users a url to authenticate with Bungie.net.
    @commands.command(name = 'authenticate', brief = "~authenticate",  help = "`~authenticate`, Bot will DM you a link to authenticate with Bungie.net")
    async def authenticate(self, ctx):
        discordID = ctx.message.author.id
        
        url = f'https://destiny.scarfi.me/api/v1/authenticate?id={discordID}'

        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Please use the below link to authenticate with Bungie.net.  It may freeze on the final page, please give it time to finish.\n{url}')

        # delete command message to keep channels clean if not a dm and bot has permissions
        if ctx.channel.type is ChannelType.text and ctx.message.channel.permissions_for(self.bot.user).manage_messages:
            await ctx.message.delete()
    

def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))