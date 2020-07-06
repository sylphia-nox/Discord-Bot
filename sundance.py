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

#create bot object
#client = discord.Client()
bot = commands.Bot(command_prefix='!')

sun_chan = None
raid_chan = None



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    guild = bot.guilds[0]

    print (
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

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

@bot.command(name='raid', help='I want to raid')
async def raid(ctx, what, when):
    sun_chan = bot.get_channel(683409608987115740)
    response = f'let\'s go raid {what} at {when}'
    await sun_chan.send(response)



        




bot.run(BotToken)
