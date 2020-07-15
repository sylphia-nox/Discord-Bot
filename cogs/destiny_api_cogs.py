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


    @commands.command(name = 'next_level', help = "`~next_level <steam_name> <character: int> Character is 0, 1, 2 in order of appearance on character select.")
    async def bungie(self, ctx, steam_name: str, character: int):

        # grab manifest file for items
        global manifest
        r = requests.get("https://www.bungie.net/common/destiny2_content/json/en/DestinyInventoryItemLiteDefinition-fdddf2ca-57f5-4da0-88d9-10be10a553d5.json")
        manifest = r.json()

        # declare list to hold items
        items = []

        # base url
        base_url = "https://www.bungie.net/platform"
        user_name = steam_name
        character = character

        #make request for membership ID
        url = base_url + f'/Destiny2/SearchDestinyPlayer/3/{user_name}/'
        r = requests.get(url, headers = HEADERS)

        #convert the json object we received into a Python dictionary object
        #and print the name of the item
        get_user_return = r.json()
        print(json.dumps(get_user_return,indent = 4))

        # get member ID for user
        memberID = get_user_return['Response'][0]['membershipId']
        print(f'MemberID: {memberID}')

        membershipType = get_user_return['Response'][0]['membershipType']

        # deleting json to save resources
        del get_user_return

        url = base_url + f'/Destiny2/{membershipType}/Profile/{memberID}/?components=200'
        r = requests.get(url, headers = HEADERS)

        get_characters_return = r.json()
        #print(json.dumps(inventoryItem['Response']['characters']['data'], indent=4))
        char_ids = []
        for key in get_characters_return['Response']['characters']['data']:
            char_ids.append(key)

        char_id = char_ids[character]
        global class_type
        class_type = get_characters_return['Response']['characters']['data'][char_id]['classType']


        # get all items and info for items
        url = base_url + f'/Destiny2/{membershipType}/Profile/{memberID}/?components=102, 201, 205, 300'
        r = requests.get(url, headers = HEADERS)
        json_return = r.json()

        # pull out item_info
        global item_info
        item_info = json_return['Response']['itemComponents']['instances']['data']

        # parse vault items
        items = await self.parse_json_for_item_info(json_return['Response']['profileInventory']['data']['items'], items)

        # parse equiped and unequiped items
        for id in char_ids:
            items = await self.parse_json_for_item_info(json_return['Response']['characterInventories']['data'][id]['items'], items)
            items = await self.parse_json_for_item_info(json_return['Response']['characterEquipment']['data'][id]['items'], items)

        # deleting variable to save memory usage.
        del json_return

        # get highest light for each slot
        high_items = [0, 0, 0, 0, 0, 0, 0, 0]
        for item in items:
            if item[1] == 2:
                # if helmet
                if item[2] == 26:
                    if item[3] > high_items[3]:
                        high_items[3] = item[3]
                # if gauntlets
                elif item[2] == 27:
                    if item[3] > high_items[4]:
                        high_items[4] = item[3]
                # if chest
                elif item[2] == 28:
                    if item[3] > high_items[5]:
                        high_items[5] = item[3]
                # if legs
                elif item[2] == 29:
                    if item[3] > high_items[6]:
                        high_items[6] = item[3]
                # if class item
                elif item[2] == 30:
                    if item[3] > high_items[7]:
                        high_items[7] = item[3]
            elif item[1] == 3:
                # if kinetic
                if item[2] == 1498876634:
                    if item[3] > high_items[0]:
                        high_items[0] = item[3]
                # if energy
                elif item[2] == 2465295065:
                    if item[3] > high_items[1]:
                        high_items[1] = item[3]
                # if power
                elif item[2] == 953998645:
                    if item[3] > high_items[2]:
                        high_items[2] = item[3]

        # get class string
        if(class_type == 0):
            class_name = "Titan"
        elif(class_type == 1):
            class_name = "Hunter"
        else:
            class_name = "Warlock"

        # calculate average power
        play_pow = int(sum(high_items)/8)

        # calculate power to next level
        power_needed = 8-(sum(high_items)%8)

        #titles
        messageHeader = f'***{steam_name}: {class_name}***\n'
        message1 = f'**Current Power: {play_pow}\n'
        message2 = "**Highest Items:\n"

        # create string for displaying each item's power and then its difference from current power
        highest_items = ""
        categories = ['Kinetic','Energy','Power','Helmet','Gauntlets','Chest','Legs','Class Item']
        for i in range(8):
            power_dif = high_items[i] - play_pow
            highest_items = highest_items + f'{categories[i]}: {high_items[i]} ({power_dif:+})\n'

        # show needed increase in item power for next level.
        message3 = f'**Power needed for next level: {power_needed}'

        message_content = messageHeader + "```" + message1 + message2 + highest_items + message3 + "```"
        await ctx.send(message_content)

        # final variable cleanup
        del manifest
        del item_info

        # delete command message to keep channels clean
        await ctx.message.delete()

    # helper function to parse JSON
    async def parse_json_for_item_info(self, json, items_list):
        global manifest
        global class_type

        for item in json:
            itemHash = str(item['itemHash'])
            itemType = manifest[itemHash]['itemType']
            itemClassType = manifest[itemHash]['classType']
            #check if the item can be used by the specified character
            if((itemType == 2 and itemClassType == class_type) or itemType == 3):
                if(itemType == 2):
                    itemSubType = manifest[itemHash]['itemSubType']
                else:
                    itemSubType = manifest[itemHash]['inventory']['bucketTypeHash']

                # now that we know this is an instanced item, get its ID to get the items power level
                itemInstanceID = str(item['itemInstanceId'])
                # run api call to get power level
                power_level = item_info[itemInstanceID]['primaryStat']['value']

                items_list.append([itemInstanceID, itemType, itemSubType, power_level])

        del json
        return items_list

    @commands.command(name = 'character_ids', hidden = True)
    async def character_ids(self, ctx, name):
        # base url
        base_url = "https://www.bungie.net/platform"

        #make request for membership ID
        url = base_url + f'/Destiny2/SearchDestinyPlayer/3/{name}/'
        r = requests.get(url, headers = HEADERS)

        # convert the json object we received into a Python dictionary object
        # and print the name of the item
        inventoryItem = r.json()

        # get memberID to use in next API call
        memberID = inventoryItem['Response'][0]['membershipId']

        # get character info
        url = base_url + f'/Destiny2/3/Profile/{memberID}/?components=200'
        r = requests.get(url, headers = HEADERS)

        # store character info in dictionary object
        inventoryItem = r.json()

        # cycle through JSON to get character IDS, they are stored in the Key instead of as a value.
        char_ids = []
        for key in inventoryItem['Response']['characters']['data']:
            char_ids.append(key)

        # send message to channel with user IDs
        await ctx.send(char_ids)


def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))