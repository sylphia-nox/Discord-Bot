#this cog is for the loop tasks, relies on helper_cogs.py for functionality.

# import statements
from discord.ext import commands, tasks
from discord.ext.tasks import loop
from datetime import datetime, timedelta

from dateutil.parser import parse
from dateutil.parser import ParserError
import errors

class loop_cogs(commands.Cog):

    # this method runs on cog load
    def __init__(self, bot):
        self.bot = bot

        global state
        state = 0

        # import utility functions
        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, loop_cogs failed to load helper_cogs.py')

        # load Destiny helper cogs
        global destiny_helpers
        destiny_helpers = self.bot.get_cog('Destiny Utilities')
        if(destiny_helpers is None):
            print(f'Fatal error, Destiny_api_cogs failed to load destiny_api_helper_cogs')

        # pylint ignore command as it does not properly recognize that this method does exist
        self.notify.add_exception_type(errors.ApiError)             # pylint: disable=no-member
        self.notify.add_exception_type(errors.ManifestLoadError)    # pylint: disable=no-member
        self.notify.add_exception_type(IndexError)                  # pylint: disable=no-member
        self.notify.start()                                         # pylint: disable=no-member



    # creating this event to notify users approximately 1 hour before a raid
    @tasks.loop(minutes = 20)
    async def notify(self):
        global state

        # grab current time.
        now = datetime.now()
        
        # print to console for monitoring
        print(f'loop check {now}')
        try:
            # run utility
            await helpers.raid_notification_check()
        except Exception as e:
            await helpers.log_error(e)

        # run purge OAuth
        try:
            await helpers.purge_oauth_DB()
        except Exception as e:
            await helpers.log_error(e)

        # load/update manifests
        try:
            await destiny_helpers.check_for_updated_manifests()
        except Exception as e:
            await helpers.log_error(e)

        if state == 0:
            print(f'Bot initialized')
            state = 1


    #function ensure bot is started and ready before running loop
    @notify.before_loop
    async def notify_before(self):
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(loop_cogs(bot))