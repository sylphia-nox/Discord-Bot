#bot.py
import os

import discord
import mysql.connector

from dotenv import load_dotenv
from discord.ext import commands

#load environment variables
load_dotenv()

mydb = mysql.connector.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    passwd = os.getenv('DB_PASSWD'),
    database = os.getenv('DATABASE'),
    auth_plugin='mysql_native_password'
)

mycursor = mydb.cursor()

BotToken = os.getenv('BOT_TOKEN')
ServerToken = os.getenv('SERVER_TOKEN')

sun_chan_code = 683409608987115740
raid_chan_code = 667741313105395712

raid_setup_active = False
raid_setup_step = "what"
raid_setup_id = ""

#create bot object
#client = discord.Client()
bot = commands.Bot(command_prefix='~')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    guild = bot.guilds[0]

    print (
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )
    global sun_chan_code
    global mycursor

    sun_chanel = bot.get_channel(sun_chan_code)
    mycursor.execute("SELECT * FROM raid_info")
    response = 'here are the raids \n' 
    raid_string = mycursor.fetchall()
    await sun_chanel.send(response + str(raid_string))


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

                for i in range(sqlreturn[0]):
                    if (int(message.content) == (i+1)):
                        print(f'We have a match!')
                        #do the thing
                        sql = "UPDATE raid_plan SET what = %s WHERE idRaids = %s"
                        val = (f'{message.content}', raid_setup_id)
                        mycursor.execute(sql, val)

                        await print_raid(raid_setup_id)
                        await raid_setup_user.dm_channel.send(f'when?')
                        
                        raid_setup_step = "when"
                        in_list = True
                        break

                if(not in_list):
                    await raid_setup_user.dm_channel.send(f'Invalid choice, please choose a number from the list')

            elif(raid_setup_step == "when"):
                await rs_message.edit(content = f'{rs_message.content} at {message.content}\nRaid ID: {raid_setup_id}')
                await raid_setup_user.dm_channel.send(f'raid setup complete')

                raid_setup_active = False
                raid_setup_step = "what"

                sql = "UPDATE raid_plan SET time = %s WHERE idRaids = %s"
                val = (f'{message.content}', raid_setup_id)
                mycursor.execute(sql, val)

                await print_raid(raid_setup_id)

                raid_setup_id = ""

            mydb.commit()
                
    await bot.process_commands(message)

@bot.command(name='raid', help='I want to raid')
async def raid(ctx):
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
    sun_chan = bot.get_channel(raid_chan_code)
    response = f'let\'s raid'
    message = await sun_chan.send(response)

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
    

@bot.command(name='join', help='type join and then the raid id to join')
async def join(ctx, raid_id, spot):
    global mycursor
    global mydb

    spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

    mycursor.execute(f'SELECT message_id, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()
    
    sql = "INSERT IGNORE INTO players (DiscordID, Display_Name) VALUE (%s, %s)"
    val = (ctx.message.author.id, ctx.message.author.name)
    mycursor.execute(sql, val)
    mydb.commit()

    if(sqlreturn[int(spot)] == None):
        sql = "UPDATE raid_plan SET " + spots[int(spot)-1] + " = %s WHERE idRaids = %s"
        val = (f'{ctx.message.author.id}', raid_id)
        mycursor.execute(sql, val)
        mydb.commit()

        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'You have been added to the raid.')
        await print_raid(raid_id)
    else:
        await ctx.message.author.create_dm()
        await ctx.message.author.dm_channel.send(f'That spot is taken, please choose another.')

@bot.command(name='refresh', help='type refresh and the raid info will be refreshed')
async def refresh(ctx, raid_id):
    global sun_chan_code
    global mycursor
    global mydb

    await print_raid(raid_id)


@bot.command(name='leave', help='type leave # and you will be removed from that raid')
async def leave(ctx, raid_id):
    global sun_chan_code
    global mycursor
    global mydb

    spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

    mycursor.execute(f'SELECT prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()

    for i in range(len(sqlreturn)):
        if (sqlreturn[i] == str(ctx.message.author.id)):
            print(f'Removing user from raid position {i+1}')
            
            sql = "UPDATE raid_plan SET " + spots[i] + " = NULL WHERE idRaids = %s"
            val = (raid_id,)
            mycursor.execute(sql, val)
            mydb.commit()

            await ctx.message.author.create_dm()
            await ctx.message.author.dm_channel.send(f'You have been removed from raid {raid_id}.')
            await print_raid(raid_id)
            break


async def print_raid(raid_id):
    global raid_chan_code
    global mycursor
    global mydb

    select = f'SELECT t.idRaids, `time`, `raid_info`.`name`, t1.Display_Name, t2.Display_Name, t3.Display_Name, t4.Display_Name, t5.Display_Name, t6.Display_Name, t7.Display_Name, t8.Display_Name, message_id, `raid_info`.`dlc`, `raid_info`.`light_level` '
    from_clause = f'FROM raid_plan t '
    join_clause = f'LEFT OUTER JOIN raid_info ON `raid_info`.`idRaids`=t.what LEFT OUTER JOIN players t1 ON t1.DiscordID=t.prime_one LEFT OUTER JOIN players t2 ON t2.DiscordID=t.prime_two LEFT OUTER JOIN players t3 ON t3.DiscordID=t.prime_three LEFT OUTER JOIN players t4 ON t4.DiscordID=t.prime_four LEFT OUTER JOIN players t5 ON t5.DiscordID=t.prime_five LEFT OUTER JOIN players t6 ON t6.DiscordID=t.prime_six LEFT OUTER JOIN players t7 ON t7.DiscordID=t.back_one LEFT OUTER JOIN players t8 ON t8.DiscordID=t.back_two '
    where_clause = f'WHERE t.idRaids = {raid_id}'
    sql_statement = select + from_clause + join_clause + where_clause

    mycursor.execute(sql_statement)
    sqlreturn = mycursor.fetchone()

    raid_message = await bot.get_channel(raid_chan_code).fetch_message(sqlreturn[11])

    details = f'Raid {sqlreturn[0]}\nWe are raiding {sqlreturn[2]} at {sqlreturn[1]}\n'
    primaries = f'Primary 1: {sqlreturn[3]}\nPrimary 2: {sqlreturn[4]}\nPrimary 3: {sqlreturn[5]}\nPrimary 4: {sqlreturn[6]}\nPrimary 5: {sqlreturn[7]}\nPrimary 6: {sqlreturn[8]}\n'
    backups = f'Backup 1: {sqlreturn[9]}\nBackup 2: {sqlreturn[10]}\n'
    requirements = f'{sqlreturn[2]} requires {sqlreturn[12]} and a light level of {sqlreturn[13]}'

    await raid_message.edit(content = f'{details}{primaries}{backups}{requirements}')


async def which_raid_question(user):
    global mycursor

    mycursor.execute(f'SELECT idRaids, name FROM raid_info')
    sqlreturn = mycursor.fetchall()

    await user.create_dm()
    await user.dm_channel.send(f'What raid?')
    raids = ""
    for i in range(len(sqlreturn)):
        raids = f'{raids}{sqlreturn[i][0]}: {sqlreturn[i][1]} \n'
    await user.dm_channel.send(f'{raids}')



bot.run(BotToken)