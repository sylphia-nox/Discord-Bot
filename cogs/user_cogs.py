from discord.ext import commands

class user_cogs(commands.Cog, name='User Commands'):
    def __init__(self, bot):
        self.bot = bot

    







def setup(bot):
    bot.add_cog(user_cogs(bot))