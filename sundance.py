#sundance.py
#Created by Michael Scarfi
#
#Function: cordinate Raids and Fireteams

#import statements
import os
import discord
import mysql.connector
import traceback

from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime

import numpy as np

#load environment variables
load_dotenv()

#create DB connection
mydb = mysql.connector.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    passwd = os.getenv('DB_PASSWD'),
    database = os.getenv('DATABASE'),
    auth_plugin='mysql_native_password'
)

#create object to access DB connection
mycursor = mydb.cursor()

#set Bot and Server Token variables
BotToken = os.getenv('BOT_TOKEN')
ServerToken = os.getenv('SERVER_TOKEN')

#set channel codes, raid channel is where Raids are published, sun channel is for diagnostic messages
sun_chan_code = int(os.getenv('SUN_CHAN_CODE'))
raid_chan_code = int(os.getenv('RAID_CHAN_CODE')) 
#raid_chan_code = int(os.getenv('TEST_RAID_CHAN'))  #secondary channel for testing
admin_role_code = int(os.getenv('ADMIN_ROLE_CODE'))
bot_admin_code = int(os.getenv('BOT_ADMIN_CODE'))

#global variables to allow the bot to know if raid setup is ongoing and its state
raid_setup_active = False
raid_setup_step = "what"
raid_setup_id = ""

#create bot object
bot = commands.Bot(command_prefix='~')

#this event dictates the actions the bot takes when it connects.
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    guild = bot.guilds[0]

    #code to confirm the bot has connected to the proper server
    print (
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

    # Setting `Listening ` status
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="commands | ~help"))


#this event activates on all messages but is for DM messages for setting up a raid, everything else goes through commands
@bot.event
async def on_message(message):
    global raid_setup_active
    global raid_setup_user
    global raid_setup_step
    global rs_message
    global mycursor
    global mydb
    global raid_setup_id

    #check if raid setup is active, if not ignore
    if(raid_setup_active):
        #check to see if the message is a DM from the raid_setup_user
        if message.channel.type is discord.ChannelType.private and message.author == raid_setup_user:
            #Check what state the raid setup is in.
            if(raid_setup_step == "what"):
                #grab number of raids for loop
                mycursor.execute(f'SELECT COUNT(*) FROM raid_info')
                sqlreturn = mycursor.fetchone()

                in_list = False

                #checking to confirm the response is valid
                for i in range(sqlreturn[0]):
                    if (int(message.content) == (i+1)):
                        #if the values match a valid raid, update SQL with the raid and respond to user
                        sql = "UPDATE raid_plan SET what = %s WHERE idRaids = %s"
                        val = (f'{message.content}', raid_setup_id)
                        mycursor.execute(sql, val)

                        #prompt user for time in DM channel and edit raid post
                        await print_raid(raid_setup_id)
                        await raid_setup_user.dm_channel.send(f'When is the raid? Response can include data and time. Limit 35 characters')
                        
                        #set global variable to "when" to change the event response
                        raid_setup_step = "when"

                        #set boolean so code knows the response was valid
                        in_list = True
                        
                        #break loop to avoid excess computing
                        break

                #if the answer is not valid, reprompt user and do not change state
                if(not in_list):
                    await raid_setup_user.dm_channel.send(f'Invalid choice, please choose a number from the list')

            #elif check if raid setup is in "when" state
            elif(raid_setup_step == "when"):
                #checking to make sure input is not too long
                if(len(message.content) <= 35):
                    #update DB with "when" value
                    sql = "UPDATE raid_plan SET time = %s WHERE idRaids = %s"
                    val = (f'{message.content}', raid_setup_id)
                    mycursor.execute(sql, val)

                    #DM user that raid setup is complete
                    await raid_setup_user.dm_channel.send(f'raid setup complete')

                    #reset global variables for next raid setup
                    raid_setup_active = False
                    raid_setup_step = "what"

                    #edit raid post to show new data
                    await print_raid(raid_setup_id)

                    #clear global variable for next setup
                    raid_setup_id = ""

                    # Reset boss display status
                    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="commands | ~help"))
                else:
                    await raid_setup_user.dm_channel.send(f'Input too long, please do not exceed 35 characters')

            #both steps run SQL so we need to commit those changes
            mydb.commit()

    #this function is needed to allow events and commands to be used, without this, none of the commands will be able to be used.     
    await bot.process_commands(message)

#this command creates a new raid post, user needs to respond to DMs to complete setup.
@bot.command(name='raid', help='Type ~raid and the bot will create a new raid post for you')
async def raid(ctx):
    #declare global variables used in command
    global raid_chan_code
    global raid_setup_active
    global raid_setup_user 
    global rs_message
    global mycursor
    global mydb
    global raid_setup_id

    #setting global variable values for new raid setup
    raid_setup_active = True
    raid_setup_user = ctx.message.author

    #create raid post
    raid_chan = bot.get_channel(raid_chan_code)
    response = f'@here let\'s raid!'
    message = await raid_chan.send(response)

    #get raid post message object and set global variable
    rs_message = message

    #ask the user which raid they want to do via DM
    await which_raid_question(raid_setup_user)

    #insert raid into DB, currently only setting Raid key and message ID
    sql = "INSERT INTO raid_plan (message_id) VALUE (%s)"
    val = (message.id,)
    mycursor.execute(sql, val)
    mydb.commit()

    #setting raid ID global variable
    raid_setup_id = mycursor.lastrowid

    # Setting `Playing ` status to show bot is setting up a raid
    await bot.change_presence(activity=discord.Game(name="setting up a raid"))

    #delete command message to keep channels clean
    await ctx.message.delete()

    
#this command allows a user to join a raid.
@bot.command(name='join', help='type ~join # # First number is the raid id to join followed by the spot you would like to take (1-6 for primary 7-8 for backup)')
async def join(ctx, raid_id: int, spot: int):
    await add_user_to_raid(ctx.message.author, raid_id, ctx.message.author, spot)

    #delete command message to keep channels clean
    await ctx.message.delete()

#command to allow a user to leave the raid, it will remove the user from the first spot it finds them in.
@bot.command(name='leave', help='type ~leave # and you will be removed from that raid')
async def leave(ctx, raid_id: int):
    await remove_user(ctx.message.author, raid_id, ctx.message.author)

    #delete command message to keep channels clean
    await ctx.message.delete()

#begin Admin command section

#this is a utility command to refresh a raid post based on data in MySQL DB
@bot.command(name='refresh', help='type ~refresh and the raid info will be refreshed')
@commands.has_role(admin_role_code)
async def refresh(ctx, raid_id: int):
    await print_raid(raid_id)

    #delete command message to keep channels clean
    await ctx.message.delete()

#this command allows a user with certain privileges to delete Raids
@bot.command(name='delete', help='type ~delete #, this command is only available to admin users.')
@commands.has_role(admin_role_code)
async def delete(ctx, raid_id: int):
    #declare global variables used in command
    global mycursor
    global mydb

    #grab raid message ID to be deleted
    mycursor.execute(f'SELECT message_id FROM raid_plan WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()

    #grab message object to delete using the message_ID stored in DB
    raid_message = await bot.get_channel(raid_chan_code).fetch_message(sqlreturn[0])

    #delete message
    await raid_message.delete()

    #delete raid from DB
    sql = "DELETE FROM raid_plan WHERE idRaids = %s"
    val = (raid_id,)
    mycursor.execute(sql, val)
    mydb.commit()

    #delete command message to keep channels clean
    await ctx.message.delete()

#this command allows an admin user to add someone to a raid post
@bot.command(name='add', help='type add @usertag # #, where # # is the raid ID followed by the spot to add them to that raid.')
@commands.has_role(admin_role_code)
async def add(ctx, user: discord.Member, raid_id: int, spot_id: int):
    #call add user command
    await add_user_to_raid(user, raid_id, ctx.message.author, spot_id)

    #delete command message to keep channels clean
    await ctx.message.delete()

#this command allows an admin user to remove someone from a raid post
@bot.command(name='remove', help='type remove @usertag #, where # is the raid ID to remove the tagged user from the raid')
@commands.has_role(admin_role_code)
async def remove(ctx, user: discord.Member, raid_id: int):
    await remove_user(user, raid_id, ctx.message.author)

    #delete command message to keep channels clean
    await ctx.message.delete()

#helper utility to update the raid post, requires raid_id input matching ID in DB
async def print_raid(raid_id):
    #declare global variable used in command
    global raid_chan_code
    global mycursor
    global mydb

    #SQL for query to pull Raid info with display values
    select = f'SELECT t.idRaids, `time`, `raid_info`.`name`, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two, message_id, `raid_info`.`dlc`, `raid_info`.`light_level` '
    from_clause = f'FROM raid_plan t '
    join_clause = f'LEFT OUTER JOIN raid_info ON `raid_info`.`idRaids`=t.what '
    where_clause = f'WHERE t.idRaids = {raid_id}'
    sql_statement = select + from_clause + join_clause + where_clause

    #execute SQL and grab results
    mycursor.execute(sql_statement)
    sqlreturn = mycursor.fetchone()

    #parse return to change values of None to "" and change ID values to tag format and store them in new array: raid_spots
    raid_spots = []
    for i in range(8):
        if(sqlreturn[i+3]==None):
            raid_spots.append("")
        else:
            raid_spots.append(f'<@{sqlreturn[i+3]}>')

    #grab message object to update using message_ID stored in DB
    raid_message = await bot.get_channel(raid_chan_code).fetch_message(sqlreturn[11])

    #text of post
    details = f'Raid {sqlreturn[0]}\nWe are raiding {sqlreturn[2]} at {sqlreturn[1]}\n'
    primaries = f'Primary 1: {raid_spots[0]}\nPrimary 2: {raid_spots[1]}\nPrimary 3: {raid_spots[2]}\nPrimary 4: {raid_spots[3]}\nPrimary 5: {raid_spots[4]}\nPrimary 6: {raid_spots[5]}\n'
    backups = f'Backup 1: {raid_spots[6]}\nBackup 2: {raid_spots[7]}\n'
    requirements = f'{sqlreturn[2]} requires {sqlreturn[12]} and a light level of {sqlreturn[13]}'

    #update post with text
    await raid_message.edit(content = f'{details}{primaries}{backups}{requirements}')

#helper function to ask user what raid they want to run
#currently this is only used once so it should potentially be merged into the event command
async def which_raid_question(user):
    #declare global variable used in function
    global mycursor

    #grab the list of Raid names from DB
    mycursor.execute(f'SELECT idRaids, name FROM raid_info')
    sqlreturn = mycursor.fetchall()

    #DM user list of Raids
    await user.create_dm()
    await user.dm_channel.send(f'What raid? (type number)')
    raids = ""
    for i in range(len(sqlreturn)):
        raids = f'{raids}{sqlreturn[i][0]}: {sqlreturn[i][1]} \n'
    await user.dm_channel.send(f'{raids}')

#helper function to add user to a raid
async def add_user_to_raid(user, raid_id, request_user, spot):
    #declare global variables used in command
    global mycursor
    global mydb

    #create array of values to allow dynamic sql
    spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

    #pull current information on raid.
    mycursor.execute(f'SELECT message_id, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()

    #check to confirm user is not already in the raid.
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

    #check to ensure the spot the user wants is not taken and add them if it is not
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
        
    #if user is not already in the raid and tries to join a taken spot
    else:
        #inform user the spot is taken
        await request_user.create_dm()
        await request_user.dm_channel.send(f'That spot is taken, please choose another.')

    #update raid post
    await print_raid(raid_id)

#helper function to remove user from a raid.
async def remove_user(user, raid_id, request_user):
    #declare global variables used in command
    global mycursor
    global mydb

    #create array of values to allow dynamic sql
    spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

    #pull current raid info
    mycursor.execute(f'SELECT prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()

    #iterate through each spot to check if the user is in that spot.
    for i in range(len(sqlreturn)):
        #check if the message author's ID matches the ID in the spot
        if (sqlreturn[i] == str(user.id)):
            #update SQL to remove user
            sql = "UPDATE raid_plan SET " + spots[i] + " = NULL WHERE idRaids = %s"
            val = (raid_id,)
            mycursor.execute(sql, val)
            mydb.commit()

            #notify request_user that the user has been removed from the raid.
            if(user.id==request_user.id):
                #inform user they were removed from the raid
                await request_user.create_dm()
                await request_user.dm_channel.send(f'You have been removed from the raid.')
            else:
                #inform request user that the user was removed to the raid.
                await request_user.create_dm()
                await request_user.dm_channel.send(f'User has been removed from the raid.')

            #update raid post with new data
            await print_raid(raid_id)

            #break loop to avoid excess computing
            break

#this event catches errors from commands
@bot.event
async def on_command_error(ctx, error):
    print(f'error occured and was caught by on_command_error')
    #import global variables
    global bot_admin_code

    #grab admin user object
    admin = bot.get_user(bot_admin_code)

    #grab the name of the command that the user tried to execute
    #this is grabbing what the user typed, taking the first word, and then removing the "~"
    command_name = ctx.message.content.split()[0].strip("~")

    #because we only have role checks we know if the checks fail it was a role error
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'You do not have the correct role to use {command_name}.')

    #checking if the input was bad
    elif isinstance(error, commands.BadArgument):
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Incorrect arguments for command: {command_name}, type `~help {command_name}` for more information.')

    #checking if the command is missing arguments
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Missing arguments for command: {command_name}, type `~help {command_name}` for more information.')

    #unkown errors, sends user message and bot admin the error code.
    else:
        #inform user an unkown error occured
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'Unkown error, please retry your command or contact <@{bot_admin_code}> for assistance.')
        
        #grab time for error message
        now = datetime.now().time()

        #send error message to server admin
        await admin.create_dm()
        await admin.dm_channel.send(f'Command error occured at {now}\nUser: {ctx.message.author.name}\nMessage: {ctx.message.content}\nTraceback: {traceback.format_exc()}\nError: {error}')

    #delete message that caused error to keep channels clean
    await ctx.message.delete()

#this event catches errors from event coroutines 
@bot.event
async def on_error(event, *args, **kwargs):
    #import global variables
    global bot_admin_code

    #grab admin user object
    admin = bot.get_user(bot_admin_code)
    
    #Gets the message object
    message = args[0] 
    
    #grab time for error message
    now = datetime.now().time()

    #inform user an error occured
    await message.author.create_dm()
    await message.author.dm_channel.send(f'An error occured, please correct your input and try again.  If the issue continues to occur please contact <@{bot_admin_code}>.')

    #send error message to server admin
    await admin.create_dm()
    await admin.dm_channel.send(f'On_message error occured at {now}\nUser: {message.author.name}\nMessage: {message.content}\nError: {traceback.format_exc()}')

#execute Bot 
bot.run(BotToken)