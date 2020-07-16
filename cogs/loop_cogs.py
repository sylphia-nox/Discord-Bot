#this cog is for the loop tasks, relies on helper_cogs.py for functionality.

# import statements
from discord.ext import commands, tasks
from discord.ext.tasks import loop
from datetime import datetime, timedelta

from dateutil.parser import parse
from dateutil.parser import ParserError

class loop_cogs(commands.Cog):

    # this method runs on cog load
    def __init__(self, bot):
        self.bot = bot

        # import utility functions
        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, loop_cogs failed to load helper_cogs.py')

        # pyline ignore command as it does not properly recognize that this method does exist
        self.notify.start() # pylint: disable=no-member



    # creating this event to notify users approximately 1 hour before a raid
    @tasks.loop(minutes = 30)
    async def notify(self):

        # grab current time.
        now = datetime.now()
        
        # print to console for monitoring
        print(f'loop check {now}')

        # run utility
        await helpers.raid_notifiation_check()

    #function ensure bot is started and ready before running loop
    @notify.before_loop
    async def notify_before(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(loop_cogs(bot))