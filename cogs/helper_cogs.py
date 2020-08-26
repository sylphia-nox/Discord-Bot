# this cog provides the utiltiy functions used by the commands to actually make changes
# to avoid issues with multiple connections to the DB, anything that uses the mysql DB will exist in this cog even if it is only used once elsewhere

# import statements
import os
import discord
import mysql.connector
import traceback
import errors

from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord.ext.tasks import loop
from datetime import datetime, timedelta
from dateutil.parser import parse
from dateutil.parser import ParserError

import numpy as np

class helper_cogs(commands.Cog, name='Utilities'): 
    
    # this method is called on loading of the cog.
    def __init__(self, bot):
        self.bot = bot

        global bot_admin_code

        # create DB connection
        mydb = mysql.connector.connect(
            host = os.getenv('DB_HOST'),
            user = os.getenv('DB_USER'),
            passwd = os.getenv('DB_PASSWD'),
            database = os.getenv('DATABASE'),
            auth_plugin='mysql_native_password',
            pool_name='helper_cogs_pool',
            pool_size=5
        )
        mydb.close()

        bot_admin_code = int(os.getenv('BOT_ADMIN_CODE'))


    # helper utility to update the raid post, requires raid_id input matching ID in DB
    async def print_raid(self, raid_id, server_id):
        # SQL for query to pull Raid info with display values
        select = f'SELECT t.id, `time`, `raid_info`.`name`, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two, message_id, `raid_info`.`dlc`, `raid_info`.`light_level`, `note`, `channel_id` '
        from_clause = f'FROM raid_plan t '
        join_clause = f'LEFT OUTER JOIN raid_info ON `raid_info`.`idRaids`=t.what '
        where_clause = f'WHERE t.id = {raid_id} AND `server_id` = {server_id}'
        sql_statement = select + from_clause + join_clause + where_clause

        # execute SQL and grab results
        sqlreturn = await self.query_db(sql_statement)
        sqlreturn = sqlreturn[0]
        note = sqlreturn[14]
        raid_chan_code = int(sqlreturn[15])

        # parse return to change values of None to "" and change ID values to tag format and store them in new array: raid_spots
        raid_spots = []
        for i in range(8):
            if(sqlreturn[i+3]==None):
                raid_spots.append("")
            else:
                raid_spots.append(f'<@{sqlreturn[i+3]}>')

        # grab message object to update using message_ID stored in DB
        raid_message = await self.bot.get_channel(raid_chan_code).fetch_message(sqlreturn[11])

        # text of post
        details = f'Raid {sqlreturn[0]}\nWe are raiding {sqlreturn[2]} at {sqlreturn[1]}\n'
        primaries = f'Primary 1: {raid_spots[0]}\nPrimary 2: {raid_spots[1]}\nPrimary 3: {raid_spots[2]}\nPrimary 4: {raid_spots[3]}\nPrimary 5: {raid_spots[4]}\nPrimary 6: {raid_spots[5]}\n'
        backups = f'Backup 1: {raid_spots[6]}\nBackup 2: {raid_spots[7]}\n'
        requirements = f'{sqlreturn[2]} requires {sqlreturn[12]} and a light level of {sqlreturn[13]}'

        # check optional message
        if note != "":
            details += f'{note}\n'

        # update post with text
        await raid_message.edit(content = f'{details}{primaries}{backups}{requirements}')

    # helper function to ask user what raid they want to run
    async def which_raid_question(self, user):
        # grab the list of Raid names from DB
        sqlreturn = await self.query_db(f'SELECT idRaids, name FROM raid_info')

        # DM user list of Raids
        await user.create_dm()
        await user.dm_channel.send(f'What raid? (type number)')
        raids = ""
        for raid in sqlreturn:
            raids = f'{raids}{raid[0]}: {raid[1]} \n'
        await user.dm_channel.send(f'{raids}')

    # helper function to add user to a raid
    async def add_user_to_raid(self, user, raid_id, server_id, request_user, spot):
        # create array of values to allow dynamic sql
        spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

        # pull current information on raid.
        sqlreturn = await self.query_db(f'SELECT message_id, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE id = {raid_id} AND `server_id` = {server_id}')
        sqlreturn = sqlreturn[0]

        # check to confirm user is not already in the raid.
        if str(user.id) in np.array(sqlreturn):
            #check if request user is same as user to be added
            if(user.id==request_user.id):
                #inform user they are already in the raid
                await request_user.create_dm()
                await request_user.dm_channel.send(f'You are already in this raid.')
            else:
                #inform request user that the user is already in the raid
                await request_user.create_dm()
                await request_user.dm_channel.send(f'User is already in this raid.')

        # check to ensure the spot the user wants is not taken and add them if it is not
        elif(sqlreturn[int(spot)] == None):
            #update dabase with new info
            sql = "UPDATE raid_plan SET " + spots[int(spot)-1] + " = %s WHERE id = %s AND `server_id` = %s"
            val = (f'{user.id}', raid_id, server_id)
            await self.write_db(sql, val)

            #check if request user is same as user to be added
            if(user.id==request_user.id):
                #inform user they are added to the raid
                await request_user.create_dm()
                await request_user.dm_channel.send(f'You have been added to the raid.')
            else:
                #inform request user that the user was added to the raid.
                await request_user.create_dm()
                await request_user.dm_channel.send(f'User added to the raid.')
            
        # if user is not already in the raid and tries to join a taken spot
        else:
            #inform user the spot is taken
            await request_user.create_dm()
            await request_user.dm_channel.send(f'That spot is taken, please choose another.')

        # update raid post
        await self.print_raid(raid_id, server_id)


    # helper function to remove user from a raid.
    async def remove_user(self, user, raid_id, server_id, request_user):
        # create array of values to allow dynamic sql
        spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

        # pull current raid info
        sqlreturn = await self.query_db(f'SELECT prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE id = {raid_id} AND `server_id` = {server_id}')
        sqlreturn = sqlreturn[0]

        # iterate through each spot to check if the user is in that spot.
        for i, spot in enumerate(sqlreturn):
            # check if the message author's ID matches the ID in the spot
            if (spot == str(user.id)):
                
                #update SQL to remove user
                sql = "UPDATE raid_plan SET " + spots[i] + " = NULL WHERE id = %s AND `server_id` = %s"
                val = (raid_id, server_id)
                await self.write_db(sql, val)

                # notify request_user that the user has been removed from the raid.
                if(user.id==request_user.id):
                    #inform user they were removed from the raid
                    await request_user.create_dm()
                    await request_user.dm_channel.send(f'You have been removed from the raid.')
                else:
                    #inform request user that the user was removed to the raid.
                    await request_user.create_dm()
                    await request_user.dm_channel.send(f'User has been removed from the raid.')

                # update raid post with new data
                await self.print_raid(raid_id, server_id)

                # break loop to avoid excess computing
                break


    #helper function to delete raids.
    async def delete_raid(self, raid_id, server_id):
        #grab raid message ID to be deleted
        sqlreturn = await self.query_db(f'SELECT message_id, notify_message_id, channel_id FROM raid_plan WHERE id = {raid_id} AND `server_id` = {server_id}')
        sqlreturn = sqlreturn[0]
        raid_chan_code = int(sqlreturn[2])

        #delete raid from DB
        sql = "DELETE FROM raid_plan WHERE id = %s and `server_id` = %s"
        val = (raid_id, server_id)
        await self.write_db(sql, val)

        try:
            #grab message object to delete using the message_ID stored in DB
            raid_message = await self.bot.get_channel(raid_chan_code).fetch_message(sqlreturn[0])

            #delete raid post
            await raid_message.delete()

            #delete notify message if it exists
            if(sqlreturn[1] != None):
                #grab message object to delete using the message_ID stored in DB
                notify_message = await self.bot.get_channel(raid_chan_code).fetch_message(sqlreturn[1])
                await notify_message.delete()
        except:
            print(f'Error deleting raid posts.  Server {server_id}')

        
        

    # helper utility to change the raid time.
    async def change_raid_time(self, user, raid_id, server_id, new_time):
        #create DM channel for user, creating now so except clauses can also use.
        await user.create_dm()

        try:
            #if the input is invalid it will throw either ParserError, ValueError, or Overflow Error
            raid_time = parse(new_time, fuzzy=True)

            #update DB with "when" value
            sql = "UPDATE raid_plan SET time = %s WHERE id = %s and server_id = %s"
            val = (f'{raid_time.strftime("%I:%M %p %m/%d")}', raid_id, server_id)
            await self.write_db(sql, val)

            #DM user that raid setup is complete
            await user.dm_channel.send(f'raid {raid_id} rescheduled to {raid_time.strftime("%I:%M %p %m/%d")}')

            #edit raid post to show new data
            await self.print_raid(raid_id, server_id)

        #catching the error handling to notify user if their input was invalid
        except ParserError:
            await user.dm_channel.send(f'not a date time input, please try again')
        except ValueError:
            await user.dm_channel.send(f'invalid input, please try again')
        except OverflowError:
            await user.dm_channel.send(f'date time values exceed possible values, please try again')


    
    # helper utility to create raid
    async def create_raid(self, raid_number: int, raid_time: str, note: str, creater_id, server_id, channel_id):
        # check if the server has a raid channel setup, otherwise use channel from command
        sql_return = await self.query_db(f'SELECT `raid_chan`, `destiny_folk` FROM `guilds` WHERE `guildID` = {server_id};')
        try:
            if (sql_return[0][0] != "null"):
                channel_id = int(sql_return[0][0])

            if (sql_return[0][1] is not None):
                destiny_folk = f'<@&{sql_return[0][1]}>' 
            else:
                destiny_folk = '@here'
        except IndexError:
            raise errors.SetupIncomplete("Setup has not been completed on this server, you cannot create raid posts until the admin configures that functionality.")

        #create raid post
        raid_chan = self.bot.get_channel(channel_id)
        response = f'{destiny_folk} let\'s raid!'
        message = await raid_chan.send(response)

        # check what the highest raid number is currently for the given server.
        sql_return = await self.query_db(f'SELECT MAX(`id`) FROM `raid_plan` WHERE `server_id` = {server_id}')
        if not (sql_return[0][0] is None):
            raid_id = int(sql_return[0][0]) + 1
        else:
            raid_id = 1

        #insert raid into DB, currently only setting Raid key and message ID
        sql = "INSERT INTO raid_plan (`id`, `time`, `what`, `server_id`, `channel_id`, `message_id`, `creater_id`, `note`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (
            raid_id,
            f'{raid_time.strftime("%I:%M %p %m/%d")}',
            raid_number,
            server_id,
            channel_id,
            message.id,
            creater_id,
            note 
        )
        await self.write_db(sql, val)

        await self.print_raid(raid_id, server_id)

    # helper utility to query the DB
    async def query_db(self, query: str):
        mydb = mysql.connector.connect(pool_name='helper_cogs_pool') 
        mycursor = mydb.cursor()

        try:
            # query DB and grab results
            mycursor.execute(query)
            sqlreturn = mycursor.fetchall()
        finally:
            mydb.close()

        # return results
        return sqlreturn

    # non-async helper utility to query the DB
    def query_db_sync(self, query: str):
        mydb = mysql.connector.connect(pool_name='helper_cogs_pool') 
        mycursor = mydb.cursor()

        try:
            # query DB and grab results
            mycursor.execute(query)
            sqlreturn = mycursor.fetchall()
        finally:
            mydb.close()

        # return results
        return sqlreturn

    # helper function to write to db
    async def write_db(self, query: str, *args):
        mydb = mysql.connector.connect(pool_name='helper_cogs_pool') 
        mycursor = mydb.cursor()

        try:
            # send sql to db.
            mycursor.execute(query, *args)
            mydb.commit()
            row = mycursor.lastrowid
        finally:
            mydb.close()

        return row

    # helper function to write to db not async
    def write_db_sync(self, query: str, *args):
        mydb = mysql.connector.connect(pool_name='helper_cogs_pool') 
        mycursor = mydb.cursor()

        try:
            # send sql to db.
            mycursor.execute(query, *args)
            mydb.commit()
            row = mycursor.lastrowid
        finally:
            mydb.close()

        return row

    # helper utility to create Raid notification posts
    async def raid_notification_check(self):
        #grab current time.
        now = datetime.now()

        #pull current information on raids and times.
        sql = f'SELECT id, time, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two, notify_message_ID, channel_id, server_id FROM raid_plan WHERE id IS NOT Null;'
        sqlreturn = await self.query_db(sql)

        for raid in sqlreturn:
            if(raid[1] is not None):
                #converting time to a dateutil object to allow comparison
                raid_time = parse(raid[1], fuzzy=True) 

                #raid_id and channel_id will be used repeatedly so setting it to a variable
                raid_id = raid[0]

                #check to see if raid started over 30 minutes ago, if so, delete
                if (raid_time + timedelta(minutes = 30) < now):
                    await self.delete_raid(raid_id, int(raid[12]))

                #check if raid is starting under 70 minutes from now and does not have a notification message already
                elif (raid_time <= (now + timedelta(minutes = 70))) and raid[10] is None:
        
                    #creating int value so the function knows how many people are in the raid
                    raid_members = 0

                    #beginning of notification message
                    notify = f'Notification: Raid {raid_id} is starting soon. If you are tagged then you are currently scheduled to raid.\n'
                    
                    #adding users to notification message and checking how many people we have
                    for i in range(8):
                        if(raid[i+2] != None and raid_members < 6):
                            raid_members += 1
                            notify =  notify + f'<@{raid[i+2]}> '

                    #adding a @here mention if we are missing people
                    if (raid_members < 6):

                        # check if the server has a raid channel setup, otherwise use channel from command
                        sql_return = await self.query_db(f'SELECT `destiny_folk` FROM `guilds` WHERE `guildID` = {raid[12]};')

                        if (sql_return[0][0] is not None):
                            destiny_folk = f'<@&{sql_return[0][0]}>' 
                        else:
                            destiny_folk = '@here'

                        notify = notify + f'\n{destiny_folk} we still need {6-raid_members} fireteam member(s) for the raid.'
                    
                    #notify everyone in the raid and ping @here if we need someone
                    raid_chan = self.bot.get_channel(int(raid[11]))
                    message = await raid_chan.send(notify)

                    #get raid post message object and set global variable
                    notify_message = message

                    #add notify message ID to DB
                    sql = "UPDATE raid_plan SET notify_message_ID = %s WHERE id = %s and `server_id` = %s"
                    val = (notify_message.id,  raid_id, raid[12])
                    await self.write_db(sql, val)


    async def purge_oauth_DB(self):
        try:
            # make sure this is the production bot and not dev bot
            #if str(os.getenv('BOT_NAME')) == 'Sundance_Discord_Bot':
            print(f'Getting guilds')
            guilds = self.bot.guilds
            print(f'Getting members')
            members = []
            for guild in guilds:
                members += guild.members
            print(f'Querying DB')
            sqlreturn = await self.query_db('SELECT `discordID` FROM `oauth_tokens` where `access_token` is null;')
            oauth_owners = (np.transpose(sqlreturn))[0]
            print(f'comparing list of ')
            for owner in oauth_owners:
                if not int(owner) in members:
                    print(f'Need to delete {owner} from DB.')
                    # await self.write_db("DELETE FROM `oauth_tokens` WHERE `discordID` = '%s'", [member,])
        except:
            print(traceback.format_exc())

    # helper function to write info into DB for guilds
    async def setup_server(self, channel, admin_role, destiny_folk, server_id):
        sql = 'REPLACE INTO guilds(guildID, raid_chan, admin_role_code, destiny_folk) VALUES(%s, %s, %s, %s);'
        val = (
            server_id,
            channel,
            admin_role,
            destiny_folk
        )
        await self.write_db(sql, val)

    # helper function to select values to setup a new Discord server for sundance
    async def ask_for_server_options(self, ctx):
        # need admin_role, destiny_folk,  channel
        # ask for light level
        await ctx.message.channel.send(f'What role should have admin control over raid posts?  Can be set to `@everyone`.')

        admin_role = None
        destiny_folk = None
        channel = None

        # loop to handle bad inputs
        while admin_role is None:

            # get response message
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel is ctx.message.channel)
            mentions = msg.role_mentions
            # checking to confirm the response is valid
            if len(mentions) >= 1:
                admin_role = mentions[0]
            else:
                await ctx.message.channel.send(f'Please provide a valid role.')

        await ctx.message.channel.send(f'What role should be tagged in raid posts?  Can be set to `@everyone`.')

        # loop to handle bad inputs
        while destiny_folk is None:

            # get response message
            msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel is ctx.message.channel)
            mentions = msg.role_mentions
            # checking to confirm the response is valid
            if len(mentions) >= 1:
                destiny_folk = mentions[0]
            else:
                await ctx.message.channel.send(f'Please provide a valid role.')

        await ctx.message.channel.send(f'What channel should raids be posted in?  You can respond without a channel name to have raids be posted in the same channel that the ~raid command is run in.')
        # get response message
        msg = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author and message.channel is ctx.message.channel)
        mentions = msg.channel_mentions
        # checking to confirm the response is valid
        if len(mentions) >= 1:
            channel = mentions[0]

        # return light_level
        return admin_role, destiny_folk, channel 


def setup(bot):
    bot.add_cog(helper_cogs(bot))