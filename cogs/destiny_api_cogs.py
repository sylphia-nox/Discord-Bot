from discord.ext import commands
from dotenv import load_dotenv
import requests
import os
import json

class destiny_api_cogs(commands.Cog, name='Destiny Commands'): 
    
    # this method is called on loading of the cog.
    def __init__(self, bot):
        self.bot = bot

        load_dotenv()

        global api_key
        global HEADERS
        api_key = os.getenv('DESTINY_API_KEY')
        HEADERS = {"X-API-Key": api_key}


    @commands.command(name = 'bungie', hidden = True)
    async def bungie(self, ctx):

        #make request for Gjallarhorn
        r = requests.get("https://www.bungie.net/platform/Destiny/Manifest/InventoryItem/1274330687/", headers=HEADERS)

        #convert the json object we received into a Python dictionary object
        #and print the name of the item
        inventoryItem = r.json()
        print(inventoryItem['Response']['data']['inventoryItem']['itemName'])
        print(inventoryItem)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this helper utility is what actually calls the Bungie Destiny 2 APIs
    async def destiny2_api_public(self, url: str, api_key: str):


        my_headers = my_headers = {"X-API-Key": api_key}
        # response = requests.get(url, headers = my_headers)
        # return ResponseSummary(response)


    @commands.command(name = 'character_ids', hidden = True)
    async def character_ids(self, ctx, name):
        # base url
        base_url = "https://www.bungie.net/platform"

        #make request for membership ID
        url = base_url + f'/Destiny2/SearchDestinyPlayer/3/{name}/'
        r = requests.get(url, headers = HEADERS)

        #convert the json object we received into a Python dictionary object
        #and print the name of the item
        inventoryItem = r.json()


        #print(json.dumps(inventoryItem, indent=4))
        #print(json.dumps(inventoryItem['Response'], indent=4))
        #print(json.dumps(inventoryItem['Response'][0], indent=4))
        memberID = inventoryItem['Response'][0]['membershipId']

        url = base_url + f'/Destiny2/3/Profile/{memberID}/?components=200'
        r = requests.get(url, headers = HEADERS)

        inventoryItem = r.json()
        # print(json.dumps(inventoryItem['Response']['characters']['data'], indent=4))
        char_ids = []
        for key in inventoryItem['Response']['characters']['data']:
            char_ids.append(key)

        await ctx.send(char_ids)


def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))