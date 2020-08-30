# this cog defines the commands that interact with the Destiny 2 APIs, it relies on destiny_api_helper_cogs.py for functionality.

from discord import ChannelType
from discord.ext import commands
from datetime import datetime
import pandas as pd

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
    async def power(self, ctx, character: str = "", steam_name: str = "", platform: int = 3, OAuth = True):

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
        if character == "":
            player_char_info = await destiny_helpers.choose_player_char_and_get_info(ctx, player_info[0], player_info[1], OAuth, access_token)
        else:
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
        if ctx.channel.type is ChannelType.text and ctx.channel.type is not ChannelType.private and ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @commands.command(name = 'level', brief = "`~level <class> <steam_name:optional>`", help = "`~level <class> optional:<steam_name>` Steam_name is needed if you have not authenticated. Class should be warlock/hunter/titan (not case sensitive).  Advanced ~level <class> <account_name> <platform> (steam = 3, PSN = 2, XB = 1)")
    async def level(self, ctx, character:str = "", steam_name: str = "", platform: int = 3, OAuth = True):
        
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
        if character == "":
            player_char_info = await destiny_helpers.choose_player_char_and_get_info(ctx, player_info[0], player_info[1], OAuth, access_token)
        else:
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
        if ctx.channel.type is ChannelType.text and ctx.channel.type is not ChannelType.private and ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()


    @commands.command(name = 'reload_manifest', hidden = True)
    @commands.is_owner()
    async def reload_manifest(self, ctx):
         # load manifest
        await destiny_helpers.check_for_updated_manifests()

        # delete command message to keep channels clean if not a dm and bot has permissions
        if ctx.channel.type is ChannelType.text and ctx.channel.type is not ChannelType.private and ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    # this command sends users a url to authenticate with Bungie.net.
    @commands.command(name = 'authenticate', brief = "~authenticate",  help = "`~authenticate`, Bot will DM you a link to authenticate with Bungie.net")
    async def authenticate(self, ctx):
        discordID = ctx.message.author.id
        
        url = f'https://destiny.scarfi.me/api/v1/authenticate?id={discordID}'

        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Please use the below link to authenticate with Bungie.net.  It may freeze on the final page, please give it time to finish.\n{url}')

        # delete command message to keep channels clean if not a dm and bot has permissions
        if ctx.channel.type is ChannelType.text and ctx.channel.type is not ChannelType.private and ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()
    
    # this command provides users with optimized gear to maximize stats.
    @commands.command(name = 'optimize', brief = "~optimize <class_name>",  help = "~optimize <class_name:(hunter/warlock/titan)>, Command to create optimized loadouts based on 3 stats.  Bot will respond with additional questions, use y or n to respond to yes/no questions.")
    async def optimize(self, ctx, character:str = ""):
        print(f'Starting optimize command')
        player_info = await destiny_helpers.get_member_info_Oauth(ctx.message.author.id)
        access_token = player_info[3]
        
        # get player character info [memberID, membershipType, character_class, char_ids, char_id, emblem]
        if character == "":
            player_char_info = await destiny_helpers.choose_player_char_and_get_info(ctx, player_info[0], player_info[1], True, access_token)
        else:
            player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character, True, access_token)

        print(f'Finished getting player info')
        # declare list to hold armor and get items [itemInstanceID, itemType, itemSubType, power_cap, exotic, item_stats, itemHash]
        armor = await destiny_helpers.get_player_armor(player_char_info, True, access_token)
        
        # get user input for variables
        exotic_hash, power_cap, traits, stat_goal_reductions = await destiny_helpers.ask_user_input_for_optimize(ctx, armor)

        # filter list to use specific exotic and for sunsetting.
        armor = await destiny_helpers.filter_armor(armor, exotic_hash, power_cap)

        # get dataframe of optimized items
        results_df = await destiny_helpers.get_optimized_armor(armor, traits, stat_goal_reductions)

        # create embed to send to user
        embed = await destiny_helpers.format_armor_message(results_df, player_char_info, player_info[2], traits, stat_goal_reductions)

        await ctx.send(embed = embed)

    # this command provides users with optimized gear to maximize stats.
    @commands.command(name = 'cleanse', brief = "~cleanse <class_name>",  help = "~cleanse <class_name:(hunter/warlock/titan)>  Will return a list with name, scr(base stat total weighted based on your provided stat order), power cap, and DIM search string.")
    async def cleanse(self, ctx, character:str = "", number:int = 15):
        player_info = await destiny_helpers.get_member_info_Oauth(ctx.message.author.id)
        access_token = player_info[3]
        
        # get player character info [memberID, membershipType, character_class, char_ids, char_id, emblem]
        if character == "":
            player_char_info = await destiny_helpers.choose_player_char_and_get_info(ctx, player_info[0], player_info[1], True, access_token)
        else:
            player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character, True, access_token)

        # ask if player want to include all items or only items in vault
        all_items = await destiny_helpers.include_items_on_character(ctx)

        # declare list to hold armor and get items [itemInstanceID, itemType, itemSubType, power_cap, exotic, item_stats, itemHash]
        armor = await destiny_helpers.get_player_armor(player_char_info, True, access_token, all_items = all_items)

        # add bonus stats to exotic armor
        # commenting out to improve performance while testing.
        armor = await destiny_helpers.add_exotic_bonus_stats(armor)

        # need to add function to get modifier numbers
        modifiers = await destiny_helpers.get_cleanse_modifiers(ctx)

        results_df = await destiny_helpers.get_cleanse(armor, modifiers, number)

        embed = await destiny_helpers.build_cleanse_embed(results_df, player_char_info, player_info[2])

        await ctx.send(embed = embed)

def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))