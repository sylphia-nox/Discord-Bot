#random test stuff, not uploading to github at current.

import os

import discord
import mysql.connector

from dotenv import load_dotenv
from discord.ext import commands

return_value = "('729563478251274280',)"

id = return_value

print(f'{id}')
new_string = ''.join(filter(lambda i: i not in ['(','\'',',',')'], str(id)))
print(f'{new_string}')



load_dotenv()

mydb = mysql.connector.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    passwd = os.getenv('DB_PASSWD'),
    database = os.getenv('DATABASE'),
    auth_plugin='mysql_native_password'
)

mycursor = mydb.cursor()

#mycursor.execute(f'SELECT idRaids, name FROM raid_info')
#sqlreturn = mycursor.fetchall()
#print(f'{sqlreturn[0][0]}')
#print(f'{sqlreturn[1]}')


#mycursor.execute("SELECT * FROM raid_info")
#raid_string = mycursor.fetchone()

#print(f'{raid_string}')
#print(f'{raid_string[1]}')
#new_string = ''.join(filter(lambda i: i not in ['(',')'], raid_string))
#new_string.split(', ')
#print(f'{raid_string[0]}')
#print(f'{raid_string[1]}')

message = '6'
i = 5
print(f'{(int(message) == (i+1))}')

global sun_chan_code
global mycursor

sun_chanel = bot.get_channel(sun_chan_code)
mycursor.execute("SELECT * FROM raid_info")
response = 'here are the raids \n' 
raid_string = mycursor.fetchall()
await sun_chanel.send(response + str(raid_string))