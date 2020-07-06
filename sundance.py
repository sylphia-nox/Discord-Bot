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
bot = commands.Bot(command_prefix='!')



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
async def on_raw_reaction_add(reaction):
    sun_chan = bot.get_channel(683409608987115740)
    response = 'someone added a reaction!'
    await sun_chan.send(response)

@bot.event
async def on_reaction_add(reaction, user):
    sun_chan = bot.get_channel(683409608987115740)
    response = f'@{user} added a reaction!'
    await sun_chan.send(response)

@bot.event
async def on_message(message):
    global raid_setup_active
    global raid_setup_user
    global raid_setup_step
    global rs_message
    global mycursor
    global mydb
    global raid_setup_id

    if(raid_setup_active):
        if message.channel.type is discord.ChannelType.private and message.author == raid_setup_user:
            if(raid_setup_step == "what"):
                await rs_message.edit(content = f'{rs_message.content} {message.content}')
                await raid_setup_user.dm_channel.send(f'when?')

                raid_setup_step = "when"

                sql = "UPDATE raid_plan SET what = %s WHERE idRaids = %s"
                val = (f'{message.content}', raid_setup_id)
                mycursor.execute(sql, val)

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

    raid_setup_active = True
    raid_setup_user = ctx.message.author

    sun_chan = bot.get_channel(raid_chan_code)
    response = f'let\'s raid'
    message = await sun_chan.send(response)
    rs_message = message

    await raid_setup_user.create_dm()
    await raid_setup_user.dm_channel.send(f'What raid?')

    sql = "INSERT INTO raid_plan (message_id) VALUE (%s)"
    val = (message.id,)
    mycursor.execute(sql, val)
    mydb.commit()

    raid_setup_id = mycursor.lastrowid
    

@bot.command(name='spot', help='type join and then the raid id to join')
async def spot(ctx, raid_id, spot):
    global sun_chan_code
    global mycursor
    global mydb

    spots = ["prime_one", "prime_two", "prime_three", "prime_four", "prime_five", "prime_six", "back_one", "back_two"]

    mycursor.execute(f'SELECT message_id, prime_one, prime_two, prime_three, prime_four, prime_five, prime_six, back_one, back_two FROM raid_plan WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()
    print(f'{sqlreturn}')
    
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




async def print_raid(raid_id):
    global raid_chan_code
    global mycursor
    global mydb

    mycursor.execute(f'SELECT idRaids, time, what, t1.Display_Name AS prime_one, t2.Display_Name AS prime_two, t3.Display_Name AS prime_three, t4.Display_Name AS prime_four, t5.Display_Name AS prime_five, t6.Display_Name AS prime_six, t7.Display_Name AS back_one, t7.Display_Name AS back_two, message_id FROM raid_plan t LEFT OUTER JOIN players t1 ON t1.DiscordID=t.prime_one LEFT OUTER JOIN players t2 ON t2.DiscordID=t.prime_two LEFT OUTER JOIN players t3 ON t3.DiscordID=t.prime_three LEFT OUTER JOIN players t4 ON t4.DiscordID=t.prime_four LEFT OUTER JOIN players t5 ON t5.DiscordID=t.prime_five LEFT OUTER JOIN players t6 ON t6.DiscordID=t.prime_six LEFT OUTER JOIN players t7 ON t7.DiscordID=t.back_one LEFT OUTER JOIN players t8 ON t8.DiscordID=t.back_two WHERE idRaids = {raid_id}')
    sqlreturn = mycursor.fetchone()

    raid_message = await bot.get_channel(raid_chan_code).fetch_message(sqlreturn[11])

    await raid_message.edit(content = f'Raid {sqlreturn[0]}\nWe are raiding {sqlreturn[2]} at {sqlreturn[1]}\nPrimary 1: {sqlreturn[3]}\nPrimary 2: {sqlreturn[4]}\nPrimary 3: {sqlreturn[5]}\nPrimary 4: {sqlreturn[6]}\nPrimary 5: {sqlreturn[7]}\nPrimary 6: {sqlreturn[8]}\nBackup 1: {sqlreturn[9]}\nBackup 2: {sqlreturn[10]}')



bot.run(BotToken)

