# this cog provides the utiltiy functions used by the commands to actually make changes
# to avoid issues with multiple connections to the DB, anything that uses the mysql DB will exist in this cog even if it is only used once elsewhere

# import statements
import os
import discord
import mysql.connector
import traceback

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

        global mycursor
        global mydb
        global sun_chan_code
        global raid_chan_code
        global bot_admin_code

        # create DB connection
        mydb = mysql.connector.connect(
            host = os.getenv('DB_HOST'),
            user = os.getenv('DB_USER'),
            passwd = os.getenv('DB_PASSWD'),
            database = os.getenv('DATABASE'),
            auth_plugin='mysql_native_password'
        )

        # create object to access DB connection
        mycursor = mydb.cursor()

        # set channel codes, raid channel is where Raids are published, sun channel is for diagnostic messages
        sun_chan_code = int(os.getenv('SUN_CHAN_CODE'))
        raid_chan_code = int(os.getenv('RAID_CHAN_CODE')) 
        #raid_chan_code = int(os.getenv('TEST_RAID_CHAN'))  #secondary channel for testing
        bot_admin_code = int(os.getenv('BOT_ADMIN_CODE'))


    # helper utility to update the raid post, requires raid_id input matching ID in DB
    async def print_raid(self, raid_id):
        # declare global variable used in command
        global raid_chan_code
        global mycursor
        global mydb

        # SQL for query to pull Raid info with display values
        select = f'SELECT t.idRaids, `time`, `raid_info`.`name`, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two, message_id, `raid_info`.`dlc`, `raid_info`.`light_level` '
        from_clause = f'FROM raid_plan t '
        join_clause = f'LEFT OUTER JOIN raid_info ON `raid_info`.`idRaids`=t.what '
        where_clause = f'WHERE t.idRaids = {raid_id}'
        sql_statement = select + from_clause + join_clause + where_clause

        # execute SQL and grab results
        mycursor.execute(sql_statement)
        sqlreturn = mycursor.fetchone()

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

        # update post with text
        await raid_message.edit(content = f'{details}{primaries}{backups}{requirements}')

    # helper function to ask user what raid they want to run
    async def which_raid_question(self, user):
        # declare global variable used in function
        global mycursor

        # grab the list of Raid names from DB
        mycursor.execute(f'SELECT idRaids, name FROM raid_info')
        sqlreturn = mycursor.fetchall()

        # DM user list of Raids
        await user.create_dm()
        await user.dm_channel.send(f'What raid? (type number)')
        raids = ""
        for i in range(len(sqlreturn)):
            raids = f'{raids}{sqlreturn[i][0]}: {sqlreturn[i][1]} \n'
        await user.dm_channel.send(f'{raids}')

    # helper function to add user to a raid
    async def add_user_to_raid(self, user, raid_id, request_user, spot):
        # declare global variables used in command
        global mycursor
        global mydb

        # create array of values to allow dynamic sql
        spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

        # pull current information on raid.
        mycursor.execute(f'SELECT message_id, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
        sqlreturn = mycursor.fetchone()

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
            sql = "UPDATE raid_plan SET " + spots[int(spot)-1] + " = %s WHERE idRaids = %s"
            val = (f'{user.id}', raid_id)
            mycursor.execute(sql, val)
            mydb.commit()

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
        await self.print_raid(raid_id)

    # helper function to remove user from a raid.
    async def remove_user(self, user, raid_id, request_user):
        # declare global variables used in command
        global mycursor
        global mydb

        # create array of values to allow dynamic sql
        spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

        # pull current raid info
        mycursor.execute(f'SELECT prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
        sqlreturn = mycursor.fetchone()

        # iterate through each spot to check if the user is in that spot.
        for i in range(len(sqlreturn)):
            # check if the message author's ID matches the ID in the spot
            if (sqlreturn[i] == str(user.id)):
                #update SQL to remove user
                sql = "UPDATE raid_plan SET " + spots[i] + " = NULL WHERE idRaids = %s"
                val = (raid_id,)
                mycursor.execute(sql, val)
                mydb.commit()

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
                await self.print_raid(raid_id)

                # break loop to avoid excess computing
                break




    #helper function to delete raids.
    async def delete_raid(self, raid_id):
        #declare global variables used in command
        global mycursor
        global mydb
        global raid_chan_code

        #grab raid message ID to be deleted
        mycursor.execute(f'SELECT message_id, notify_message_id FROM raid_plan WHERE idRaids = {raid_id}')
        sqlreturn = mycursor.fetchone()

        #grab message object to delete using the message_ID stored in DB
        raid_message = await self.bot.get_channel(raid_chan_code).fetch_message(sqlreturn[0])

        #delete raid post
        await raid_message.delete()

        #delete notify message if it exists
        if(sqlreturn[1] != None):
            #grab message object to delete using the message_ID stored in DB
            notify_message = await self.bot.get_channel(raid_chan_code).fetch_message(sqlreturn[1])
            await notify_message.delete()

        #delete raid from DB
        sql = "DELETE FROM raid_plan WHERE idRaids = %s"
        val = (raid_id,)
        mycursor.execute(sql, val)
        mydb.commit()

    # helper utility to change the raid time.
    async def change_raid_time(self, user, raid_id, new_time):
        global mycursor

        #create DM channel for user, creating now so except clauses can also use.
        await user.create_dm()

        try:
            #if the input is invalid it will throw either ParserError, ValueError, or Overflow Error
            raid_time = parse(new_time, fuzzy=True)

            #update DB with "when" value
            sql = "UPDATE raid_plan SET time = %s WHERE idRaids = %s"
            val = (f'{raid_time.strftime("%I:%M %p %m/%d")}', raid_id)
            mycursor.execute(sql, val)

            #DM user that raid setup is complete
            await user.dm_channel.send(f'raid {raid_id} rescheduled to {raid_time.strftime("%I:%M %p %m/%d")}')

            #edit raid post to show new data
            await self.print_raid(raid_id)

        #catching the error handling to notify user if their input was invalid
        except ParserError:
            await user.dm_channel.send(f'not a date time input, please try again')
        except ValueError:
            await user.dm_channel.send(f'invalid input, please try again')
        except OverflowError:
            await user.dm_channel.send(f'date time values exceed possible values, please try again')

    # helper utility to create raid
    async def create_raid(self, raid_number: int, raid_time: str):
        global mycursor
        global mydb
        global raid_chan_code

        #create raid post
        raid_chan = self.bot.get_channel(raid_chan_code)
        response = f'@here let\'s raid!'
        message = await raid_chan.send(response)

        #insert raid into DB, currently only setting Raid key and message ID
        sql = "INSERT INTO raid_plan (`message_id`, `what`, `time`) VALUES (%s, %s, %s)"
        val = (message.id, raid_number, f'{raid_time.strftime("%I:%M %p %m/%d")}')
        mycursor.execute(sql, val)
        mydb.commit()

        raid_setup_id = mycursor.lastrowid

        await self.print_raid(raid_setup_id)

    # helper utility to query the DB
    async def query_db(self, query: str):
        global mycursor

        # query DB and grab results
        mycursor.execute(f'SELECT COUNT(*) FROM raid_info')
        sqlreturn = mycursor.fetchall()

        # return results
        return sqlreturn

    # helper utility to create Raid notification posts
    async def raid_notifiation_check(self):
        global mycursor
        global raid_chan_code

        #grab current time.
        now = datetime.now()

        #pull current information on raids and times.
        mycursor.execute(f'SELECT idRaids, time, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two, notify_message_ID FROM raid_plan WHERE idRaids IS NOT Null')
        sqlreturn = mycursor.fetchall()

        for i in range(len(sqlreturn)):
            if(sqlreturn[i][1]is not None):
                #converting time to a dateutil object to allow comparison
                raid_time = parse(sqlreturn[i][1], fuzzy=True) 

                #raid_id will be used repeatedly so setting it to a variable
                raid_id = sqlreturn[i][0]

                #check if raid is starting under 70 minutes from now and does not have a notification message already
                if (raid_time <= (now + timedelta(minutes = 70))) and sqlreturn[i][10] is None:
        
                    #creating int value so the function knows how many people are in the raid
                    raid_members = 0

                    #beginning of notification message
                    notify = f'Notification: Raid {raid_id} is starting soon. If you are tagged then you are currently scheduled to raid.\n'
                    
                    #adding users to notification message and checking how many people we have
                    for ii in range(8):
                        if(sqlreturn[i][ii+2] != None and raid_members < 6):
                            raid_members += 1
                            notify =  notify + f'<@{sqlreturn[i][ii+2]}> '

                    #adding a @here mention if we are missing people
                    if (raid_members < 6):
                        notify = notify + f'\n@here we still need {6-raid_members} fireteam member(s) for the raid.'
                    
                    #notify everyone in the raid and ping @here if we need someone
                    raid_chan = self.bot.get_channel(raid_chan_code)
                    message = await raid_chan.send(notify)

                    #get raid post message object and set global variable
                    notify_message = message

                    #add notify message ID to DB
                    sql = "UPDATE raid_plan SET notify_message_ID = %s WHERE idRaids = %s"
                    val = (notify_message.id,  raid_id)
                    mycursor.execute(sql, val)
                    mydb.commit()

                #check to see if raid started over 30 minutes ago, if so, delete
                elif (raid_time + timedelta(minutes = 30) < now):
                    await self.delete_raid(raid_id)


def setup(bot):
    bot.add_cog(helper_cogs(bot))