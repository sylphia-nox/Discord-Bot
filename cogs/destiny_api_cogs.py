# this cog defines the commands that interact with the Destiny 2 APIs, it relies on destiny_api_helper_cogs.py for functionality.

from discord.ext import commands

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
    @commands.command(name = 'power', help = "`~power <steam_name> <class: str> Class should be warlock/hunter/titan (not case sensitive).")
    async def power(self, ctx, steam_name: str, character: str):
        # get memberID and membershipType
        player_info = await destiny_helpers.get_member_info(steam_name)
        
        # get player character info
        player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character)
        char_type = player_char_info[2]

        # declare list to hold items and get items
        items = await destiny_helpers.get_player_items(player_char_info)
        
        # get highest light for each slot
        high_items = await destiny_helpers.get_max_power_list(items)

        # get formatted message string
        message_content = await destiny_helpers.format_power_message(high_items, char_type, steam_name)

        # send message to channel
        await ctx.send(message_content)

        # delete command message to keep channels clean
        await ctx.message.delete()

    @commands.command(name = 'next_power', help = "`~next_power <steam_name> <class: str> Class should be warlock/hunter/titan (not case sensitive).")
    async def next_power(self, ctx, steam_name: str, character: str):
        # get memberID and membershipType
        player_info = await destiny_helpers.get_member_info(steam_name)

        # get player character info
        player_char_info = await destiny_helpers.get_player_char_info(player_info[0], player_info[1], character)
        char_type = player_char_info[2]

        # declare list to hold items and get items
        items = await destiny_helpers.get_player_items(player_char_info)
        
        # get highest light for each slot
        high_items = await destiny_helpers.get_max_power_list(items)

        # get message to send to channel
        next_power_message = await destiny_helpers.calculate_next_step(high_items, player_char_info)
        power_message = await destiny_helpers.format_power_message(high_items, char_type, steam_name)

        # send message to channel
        await ctx.send(power_message + "\n" + next_power_message)

        # delete command message to keep channels clean
        await ctx.message.delete()


    @commands.command(name = 'reload_manifest', hidden = True)
    @commands.is_owner()
    async def reload_manifest(self, ctx):
         # load manifest
        await destiny_helpers.get_manifest()

        # delete command message to keep channels clean
        await ctx.message.delete()
    

def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))