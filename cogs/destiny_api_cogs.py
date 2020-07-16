from discord.ext import commands
from dotenv import load_dotenv
import requests
import os
import json
import errors

class destiny_api_cogs(commands.Cog, name='Destiny Commands'): 
    
    # this method is called on loading of the cog.
    def __init__(self, bot):
        self.bot = bot

        load_dotenv()

        global api_key
        global HEADERS
        global base_url
        
        api_key = os.getenv('DESTINY_API_KEY')
        HEADERS = {"X-API-Key": api_key}
        base_url = "https://www.bungie.net/platform"

    # this command shows a user their current power, highest power level of each equipement piece, and needed power to hit the next level.
    @commands.command(name = 'power', help = "`~next_level <steam_name> <class: str> Class should be warlock/hunter/titan (not case sensitive).")
    async def power(self, ctx, steam_name: str, character: str):

        # load manifest
        await self.get_manifest()

        # get memberID and membershipType
        player_info = await self.get_member_info(steam_name)
        
        # get player character info
        player_char_info = await self.get_player_char_info(player_info[0], player_info[1], character)
        char_type = player_char_info[2]

        # declare list to hold items and get items
        items = await self.get_player_items(player_char_info)
        
        # get highest light for each slot
        high_items = await self.get_max_power_list(items)

        # get formatted message string
        message_content = await self.format_power_message(high_items, char_type, steam_name)

        # send message to channel
        await ctx.send(message_content)

        # delete command message to keep channels clean
        await ctx.message.delete()

    # this helper function generates the formatted message for the ~power command
    async def format_power_message(self, high_items, class_type, steam_name):
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
        return message_content

    # this function returns the a list with the highest power level for each equipement slot.
    async def get_max_power_list(self, items):
        high_items = [0, 0, 0, 0, 0, 0, 0, 0]
        # parse entire list, for each type of item, if current item has a higher power level, update power level to new level.
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

        # return list of power levels
        return high_items

    # helper function to get Manifest file and save it to global variable
    async def get_manifest(self):
        # grab manifest file for items
        global manifest
        r = requests.get("https://www.bungie.net/common/destiny2_content/json/en/DestinyInventoryItemLiteDefinition-fdddf2ca-57f5-4da0-88d9-10be10a553d5.json")
        manifest = r.json()
        del r

    # helper function to get memberID and membershipType from steam_name
    async def get_member_info(self, steam_name:str):
        # base url
        global base_url

        #make request for membership ID
        url = base_url + f'/Destiny2/SearchDestinyPlayer/3/{steam_name}/'
        r = requests.get(url, headers = HEADERS)

        #convert the json object we received into a Python dictionary object
        #and print the name of the item
        get_user_return = r.json()
        del r

        try:
            # get member ID for user
            memberID = get_user_return['Response'][0]['membershipId']

            # get membershipType
            membershipType = get_user_return['Response'][0]['membershipType']
        except IndexError:
            raise errors.PlayerNotFound("Bungie account could not be found, if there is any whitespace in your name make sure you surround it with quotes")

        # deleting json to save resources
        del get_user_return

        # return memberID and membershipType
        return [memberID, membershipType]

    # helper function to get player info as player[memberID, membershipType, class_type, char_ids]
    async def get_player_char_info(self, memberID, membershipType, character: str):
        global base_url

        # convert character as string to int, 0 = Titan, 1 = Hunter, 2 = Warlock
        if(character.lower() == "titan"):
            character_class = 0
        elif(character.lower() == "hunter"):
            character_class = 1
        elif(character.lower() == "warlock"):
            character_class = 2
        else:
            raise errors.NotaDestinyClass("Class name not recognized, please input a valid Destiny class")

        # make request for player info, getting character info.
        url = base_url + f'/Destiny2/{membershipType}/Profile/{memberID}/?components=200'
        r = requests.get(url, headers = HEADERS)
        get_characters_return = r.json()
        del r

        # get character IDs and confirm user has a character of the requested class
        char_ids = []
        has_character = False
        for key in get_characters_return['Response']['characters']['data']:
            char_ids.append(key)
            if (get_characters_return['Response']['characters']['data'][str(key)]['classType'] == character_class):
                has_character = True

        # if user does not have a character of that class, raise exception
        if (not has_character):
            raise errors.NoCharacterOfClass(f'You do not have a character of class {character}')

        # delete json to save memory
        del get_characters_return

        player_char_info = [memberID, membershipType, character_class, char_ids]
        return player_char_info

    # helper function to get list of items as items[InstanceID, itemType, itemSubType, power_level]
    async def get_player_items(self, player_char_info):
        global manifest

        # declare list to hold items
        items = []

        # get variable information from list, doing this way for ease of reading code.
        memberID = player_char_info[0]
        membershipType = player_char_info[1]
        class_type = player_char_info[2]
        char_ids = player_char_info[3]

        # get all items and info for items
        url = base_url + f'/Destiny2/{membershipType}/Profile/{memberID}/?components=102, 201, 205, 300'
        r = requests.get(url, headers = HEADERS)
        json_return = r.json()
        del r

        with open('test_api_return.json', 'w') as data_file:
            json.dump(json_return, data_file, indent = 4)

       
        # pull out item_info
        global item_info
        item_info = json_return['Response']['itemComponents']['instances']['data']
        
        # if user has privacy on, the json will not have the 'data' tag, so we can use this assignment to raise a PrivacySettings exception
        try:
            # parse vault items
            items = await self.parse_json_for_item_info(json_return['Response']['profileInventory']['data']['items'], items, class_type)

            # parse equiped and unequiped items
            for id in char_ids:
                items = await self.parse_json_for_item_info(json_return['Response']['characterInventories']['data'][id]['items'], items, class_type)
                items = await self.parse_json_for_item_info(json_return['Response']['characterEquipment']['data'][id]['items'], items, class_type)
        except KeyError:
            raise errors.PrivacyOnException("Items could not be loaded, ensure your privacy settings allow others to view your inventory.")
        

        # deleting variable to save memory usage.
        del manifest
        del item_info
        del json_return

        return items

    # helper function to parse JSON, returns items[] that can be equiped by class_type
    async def parse_json_for_item_info(self, json, items_list, class_type):
        global manifest

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




def setup(bot):
    bot.add_cog(destiny_api_cogs(bot))