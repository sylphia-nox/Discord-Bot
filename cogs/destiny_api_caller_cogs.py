# this cog provides the backend functionality for destiny_api_cogs.py and interacts with the Bungie.net APIs.  It relies on helper_cogs.py for some functionality.

from discord.ext import commands
from dotenv import load_dotenv
import discord
import requests
import os
import json
import errors
import numpy as np
import base64
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import asyncio

class destiny_api_caller_cogs(commands.Cog, name='Destiny API Utilities'): 
    
    # this method is called on loading of the cog.
    def __init__(self, bot):
        self.bot = bot

        # load environment file into environment variables
        load_dotenv()

        #declare global varibles for API calls
        global api_key
        global HEADERS
        global base_url
        
        # create HEADERS and base_url
        api_key = os.getenv('DESTINY_API_KEY')
        bot_name = os.getenv('BOT_NAME')
        bot_version = os.getenv('BOT_VERSION')
        client_id = os.getenv('DESTINY_OATH_CLIENT_ID')
        email = os.getenv('EMAIL')
        HEADERS = {
            'X-API-Key': api_key,  
            'User-Agent': bot_name + "/" + bot_version + " AppId/" + client_id + " (+https://github.com/michaelScarfi/Discord-Bot;" + email + ")",
            'Accept-Encoding': 'gzip'
        }
        base_url = "https://www.bungie.net/platform"

        # load bot OAuth info
        bot_oauth = os.getenv('DESTINY_OATH_CLIENT_ID')
        bot_secret = os.getenv('BOT_SECRET')
        
        # declare global
        global id_and_secret

        # encode bot ID and secret
        message = f'{bot_oauth}:{bot_secret}'
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        id_and_secret = base64_bytes.decode('ascii')

        

        # load helper cogs.
        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, Destiny_api_helper_cogs failed to load helper_cogs.py')

    # helper function to call get on Bungie.net api's
    async def get(self, api_url, OAuth = False, access_token = ""):
        # create copy of HEADERS to ensure we do not permanently modify HEADERS
        headers = HEADERS.copy()
        
        # if OAuth is set to True, add access token to header
        if OAuth:
            headers.update({'Authorization':f'Bearer {access_token}'})

        #make request for membership ID
        url = base_url + api_url

        # run requests in seperate thread
        loop = asyncio.get_event_loop()
        r_json = await loop.run_in_executor(ThreadPoolExecutor(), self.get_sync, url, headers)

        #convert the json object we received into a Python dictionary object and return that object
        return r_json

    def get_sync(self, url, headers):
        r = requests.get(url, headers = headers)

        status = r.status_code
        if status != 200:
            raise errors.ApiError(f'Status code {status} received from API')

        #convert the json object we received into a Python dictionary object and return that object
        return r.json()


    # helper function to call get without header or base url
    async def get_simple_async(self, url):
        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(ThreadPoolExecutor(), requests.get, url)

        # confirm 200 Good response
        status = r.status_code
        if status != 200:
            raise errors.ApiError(f'Status code {status} received from API')
        return r.json()


    # helper function to update oauth
    async def refresh_token(self, refresh_token, discordID):
        header = {'Authorization':f'Basic {id_and_secret}', 'Content-Type':'application/x-www-form-urlencoded'}
        data = {'grant_type':'refresh_token','refresh_token':f'{refresh_token}'}

        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(ThreadPoolExecutor(), self.post, 'https://www.bungie.net/platform/app/oauth/token/', header, data)

        user_tokens = r.json()

        sql = "UPDATE oauth_tokens SET access_token = %s, expires_in = %s, refresh_token = %s, refresh_expires_in = %s WHERE discordID = %s"
        val = (
            user_tokens['access_token'], 
            datetime.now() + timedelta(seconds = int(user_tokens['expires_in'])), 
            user_tokens['refresh_token'],
            datetime.now() + timedelta(seconds = int(user_tokens['refresh_expires_in'])), 
            discordID
        )
        # write new values to DB
        await helpers.write_db(sql, val)

        # return access token to avoid unecessary DB calls
        return user_tokens['access_token']

    def post(self, url, header, data):
        r = requests.post('https://www.bungie.net/platform/app/oauth/token/', headers = header, data = data)

        # confirm 200 Good response
        status = r.status_code
        if status != 200 or status != 201:
            raise errors.ApiError(f'Status code {status} received from API')

        return r.json()



def setup(bot):
    bot.add_cog(destiny_api_caller_cogs(bot))

