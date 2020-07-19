# this cog provides the backend functionality for destiny_api_cogs.py and interacts with the Bungie.net APIs.  It relies on helper_cogs.py for some functionality.

from discord.ext import commands
from dotenv import load_dotenv
import requests
import os
import json
import errors
import numpy as np

class destiny_api_helper_cogs(commands.Cog, name='Destiny Utilities'): 
    
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
        HEADERS = {
            'X-API-Key': api_key,  
            'User-Agent': "Sundance_Discord_Bot/1.0 AppId/##### (+https://github.com/michaelScarfi/Discord-Bot;michael@scarfi.me)"
        }
        base_url = "https://www.bungie.net/platform"

        # load helper cogs.
        global helpers
        helpers = self.bot.get_cog('Utilities')
        if(helpers is None):
            print(f'Fatal error, Destiny_api_helper_cogs failed to load helper_cogs.py')

        # load manifests
        self.initialize_manifest()

    # helper function to get Manifest file and save it to global variable
    async def get_manifest(self):
        # grab manifest file for items
        global manifest
        r = requests.get("https://www.bungie.net/common/destiny2_content/json/en/DestinyInventoryItemLiteDefinition-fdddf2ca-57f5-4da0-88d9-10be10a553d5.json")
        manifest = r.json()
        del r

    # helper function to initialize manifest file when cog is loaded, non async version of get_manifest
    def initialize_manifest(self):
        global manifest
        r = requests.get("https://www.bungie.net/common/destiny2_content/json/en/DestinyInventoryItemLiteDefinition-fdddf2ca-57f5-4da0-88d9-10be10a553d5.json")
        manifest = r.json()
        del r
        print('Manifest Initialized')

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

        # check to get user with exact display name, not full-proof but should reduce issues with grabbing the wrong player
        for user in get_user_return['Response']:
            try:
                if(user['displayName'] == steam_name):
                    # get member ID for user
                    memberID = user['membershipId']

                    # get membershipType
                    membershipType = user['membershipType']
            except IndexError:
                raise errors.PlayerNotFound("Bungie account could not be found, if there is any whitespace in your name make sure you surround it with quotes")

        if(memberID is None):
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
                char_id = key

        # if user does not have a character of that class, raise exception
        if (not has_character):
            raise errors.NoCharacterOfClass(f'You do not have a character of class {character}')

        # delete json to save memory
        del get_characters_return

        player_char_info = [memberID, membershipType, character_class, char_ids, char_id]
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

    # helper function to get milestones for a character
    async def get_player_milestones(self, player_char_info):
        global manifest

        # declare list to hold items
        active_pinnacles = []

        # get variable information from list, doing this way for ease of reading code.
        memberID = player_char_info[0]
        membershipType = player_char_info[1]
        char_id = player_char_info[4]

        # get all items and info for items
        url = base_url + f'/Destiny2/{membershipType}/Profile/{memberID}/Character/{char_id}/?components=202'
        r = requests.get(url, headers = HEADERS)
        json_return = r.json()
        del r
        
        # try to get list of milestones from return, if privacy is an issue this should fail with a KeyError
        try:
            # pull out item_info
            milestones = json_return['Response']['progressions']['data']['milestones']
            del json_return
        except KeyError:
            raise errors.PrivacyOnException("Items could not be loaded, ensure your privacy settings allow others to view your inventory.")
        
        # get list of pinnacle activities from DB
        pinnacle_activity_info = await helpers.query_db('SELECT * FROM `pinnacle_milestone_info`')
    
        # cycle through return and see if the user has not completed them already
        for info in pinnacle_activity_info:
            if str(info[1]) in milestones:
                active_pinnacles.append(info)

        # deleting variable to save memory usage.
        del milestones

        return active_pinnacles

    # helper function to determine where the player is in the powergrind and what steps to take 
    async def calculate_next_step(self, high_items, player_char_info):
        # get current power level boundaries
        sql_return = await helpers.query_db("SELECT `field_one`, `field_two`, `field_three` FROM `current_info` WHERE `name` = 'power_levels'")
        power_level_brackets = sql_return[0]

        # calculate average power
        current_play_pow = int(sum(high_items)/8)

        # check if player is below prime/powerful bracket.
        if(current_play_pow < int(power_level_brackets[0])):
            return (f'You can level up by doing anything.  Go play some Destiny!')
        # player is into prime/powerful/pinnacles
        else:
            # calculate total positive power in current loadout, for every +8 the player can go up a light level if they get at level items.
            positive_power = 0

            for item in high_items:
                if int(item) > current_play_pow:
                    positive_power += item - current_play_pow

            potential_power_increase = int(positive_power/8)

            destiny_challenge_emote = "<:destiny_challenge:734443985107419236>"
            
            # check if we are in the prime/powerful bracket
            if(current_play_pow < int(power_level_brackets[1])):
                # create message object to append values to.
                message = ""

                # check if player can go up a power level by getting at level drops
                if(potential_power_increase >= 1):
                    message += (f'Character can be leveled up by {potential_power_increase} level(s) by getting at level drops.  These can be aquired in any activity at your current power level.')
                  

                # create item slot array to ease translation
                categories = ['Kinetic','Energy','Power','Helmet','Gauntlets','Chest','Legs','Class Item']

                sub_message = ""
                for index, item in enumerate(high_items):
                    if item < current_play_pow:
                        item = current_play_pow
                        sub_message += f'- {categories[index]}\n'

                if sub_message != "":
                    message += f'The power level of the following items can be increased by getting an at-level drop in that slot.\n' + sub_message

                # calculate power to next level
                power_needed = 8-(sum(high_items)%8)
                message += f'You need +{power_needed} above your current average from prime/powerfuls to hit the next power level.```\nLook for {destiny_challenge_emote} on the map.'

                return(f'{message}')
            
            # check if chareacter is in the pinnacle bracket
            elif(current_play_pow < int(power_level_brackets[2])):
                # create item slot array to ease translation
                categories = ['Kinetic','Energy','Power','Helmet','Gauntlets','Chest','Legs','Class Item']
                
                # create sub_message contianing items that can be leveled up by getting at level drops.
                sub_message = ""
                for index, item in enumerate(high_items):
                    if item < current_play_pow:
                        item = current_play_pow
                        sub_message += f'- {categories[index]}\n'

                if(potential_power_increase >= 1):
                    # create message
                    message = f'Character can be leveled up by {potential_power_increase} level(s) by getting at level drops.  Look for {destiny_challenge_emote} on the map.'
                    # append sub message if appropriate
                    if sub_message != "":
                        message += f'```The power level of the following items can be increased by getting a prime/powerful drop in that slot.\n' + sub_message + "```"
                    
                    return (message)
                else: 
                    # create message object to append values to.
                    message = '```'
                    

                    if sub_message != "":
                        message += f'The power level of the following items can be increased by getting a prime/powerful drop in that slot.\n' + sub_message

                    # calculate power to next level
                    power_needed = 8-(sum(high_items)%8)
                    message += f'You need +{power_needed} from pinnacles to hit the next power level.\n'

                    # create list of power differences
                    power_difference = []
                    for item in high_items:
                        power_difference.append(item - current_play_pow)

                    # get active milestones and milestone info
                    active_milestones = await self.get_player_milestones(player_char_info)

                    # get probability array (returns each possible activity with percent change of increasing +2, +1, or +0, final row is if the pinnacle is a +1 or +2)
                    probability_array = await self.options(power_difference, active_milestones)
                    
                    # get recommendations
                    reccomendation_message = await self.get_recommendation(active_milestones, probability_array, power_needed, high_items, power_level_brackets)

                    # complete message to return
                    message += reccomendation_message + '```'

                    # return message
                    return (f'{message}')
            
            # check if character is at max power
            elif(current_play_pow == int(power_level_brackets[2])):
                return("Character is currently at maximum power, congratulations!")
            
            # if none of these catch we have an error
            else:
                return("Error, player power not within possible levels")

    # helper function to generate reccomendations
    async def get_recommendation(self, active_milestones, probability_array, power_needed, high_items, power_level_brackets):

        # get raid hash to allow us to isolate raid encounters from normal calculations
        sql_return = await helpers.query_db("SELECT `field_one` FROM `current_info` WHERE `name` = 'raid_hash'")
        raid_hash = int(sql_return[0][0])

        # get maximum values from probability_array, this will allow us to pull out the lines that match the max value.
        # best_probability = np.maximum

        # create message string to be returned
        message = ""

        # check if player has any pinnacles left.
        if any(active_milestones):
            # check if player is 1 away from pinnacle cap, if so, give any activity with highest chance of dropping needed item(s), including all raid encounters
            if (int(sum(high_items)/8) + 1 == int(power_level_brackets[2])):
                
                    # create header for message
                    message += 'You are in the final push, here are the pinnacles you can run and probability of getting a needed item.\n'

                    # create new array with activity name and probability
                    final_push_milestones = []

                    # cycle through and add each active_milestones to final_push_milestones
                    for i in range(len(probability_array)):
                        
                        final_push_milestones.append([active_milestones[2]],[probability_array[i][0] + probability_array[i][1]])
                        # since we have been dealing with floats, if a probabilty is almost 1.00 change it to be 1
                        if(final_push_milestones[i][1] >= .99):
                            final_push_milestones[i][1] = 1

                    # create strutured array and assign it back to active_milestones
                    dtype = [('name', 'S10'), ('probability', float)]
                    active_milestones = np.array(final_push_milestones, dtype=dtype)        # create a structured array
                    active_milestones = np.sort(active_milestones, order='probability')     # sort the array
                    active_milestones = np.flip(active_milestones)                          # flip array so it is in descending order.

                    for milestone in active_milestones:
                        message += f'{milestone[0]} {milestone[1]*100:.1f}%\n'
                

            # everything else needs to make special consideration of raid probabilities
            else:
                # split out raid information from everything else
                raid_prob = []
                raid_info = []

                for i in range(len(probability_array), -1, -1):
                    if (active_milestones[i-1][1] == raid_hash):
                        raid_prob.insert(0, probability_array[i-1])
                        raid_info.insert(0, active_milestones[i-1])
                        active_milestones.pop(i-1)
                        probability_array.pop(i-1)


                # transpose probability matrix to allow easier reading.
                prob_array = np.transpose(probability_array)

                # check if player is within +1 of next power level and has +1 pinnacles remaing, then pick +1 pinnacles that can help, if none exists, move to +2s
                if(power_needed == 1 and 1 in prob_array[3]):
                    # get +1 activities
                    valid_probs = prob_array[1][(prob_array[3] == 1)]
                    max_prob = np.max(valid_probs)
                    message += "Recommend doing +1 activities first.\n"
                    message += f'+1 activity(s) with the best chance of raising your light level ({max_prob*100:.1f}%):\n'
                    # iterate through list and print out activities with prob matching top probability and at +1 power
                    for i in range(len(prob_array[1])):
                        if prob_array[1][i] == max_prob and prob_array[3][i] == 1:
                            message += f'- {active_milestones[i][2]}\n'
                # if player is two away and has not completed the raid, check if it makes sense to run the raid.
                elif(power_needed <= 2 and any(raid_info)):
                    if(raid_prob[0][0] > .5 or raid_prob[1][0] > .5):
                        message += "Consider running the raid since there is a high chance you will go up a light level in the first two encounters:\n"
                        for i in range(len(raid_info)):
                            message += f'- {raid_info[i][2]} | +2: {raid_prob[i][0]*100:.1f}%, +1: {raid_prob[i][1]*100:.1f}%\n'

                # get best probability of a +2 drop.
                max_prob = np.max(prob_array[0])
                # confirm there are +2 activities that can raise a gear slot by 2.
                if(max_prob != 0):
                    message += f'+2 activity(s) with the best chance of raising one of your equipement slots by 2:\n'
                    # iterate through list and print out activities with prob matching top probability and at +2 power
                    for i in range(len(prob_array[1])):
                        if prob_array[0][i] == max_prob and prob_array[3][i] == 2:
                            message += f'- {active_milestones[i][2]} | +2: {probability_array[i][0]*100:.1f}%, +1: {probability_array[i][1]*100:.1f}%\n'
                else:
                    message += f'There are currently no activities that can raise an equipement slot by 2:\n'
                    # check if their are +1 activities and that we have not already sent them to the message
                    if (1 in prob_array[3] and power_needed !=1):
                        # get +1 activities
                        valid_probs = prob_array[1][(prob_array[3] == 1)]
                        max_prob = np.max(valid_probs)
                        message += f'+1 activity(s) with the best chance of raising your light level ({max_prob*100:.1f}%):\n'
                        # iterate through list and print out activities with prob matching top probability and at +1 power
                        for i in range(len(prob_array[1])):
                            if prob_array[1][i] == max_prob and prob_array[3][i] == 1:
                                message += f'- {active_milestones[i][2]}\n'
                    elif 2 in prob_array[3]:
                        # get +2 activities
                        valid_probs = prob_array[1][(prob_array[3] == 2)]
                        max_prob = np.max(valid_probs)
                        message += f'+2 activity(s) with the best chance of raising a gear slot by +1 ({max_prob*100:.1f}%):\n'
                        # iterate through list and print out activities with prob matching top probability and at +1 power
                        for i in range(len(prob_array[1])):
                            if prob_array[1][i] == max_prob and prob_array[3][i] == 2:
                                message += f'- {active_milestones[i][2]}\n'
        else:
            message += 'You do not have any pinnacles left this week.'

        return message

        

    # helper function to calculater probabilities
    async def calculate_probabilities(self, power_difference, milestone):
        # define list of possible drops
        drops = [milestone[3],milestone[4],milestone[5],milestone[6],milestone[7],milestone[8],milestone[9],milestone[10]]
        sum_drops = sum(drops)

        plus_two_prob = 0.0
        plus_one_prob = 0.0
        plus_zero_prob = 0.0

        # iterate through each drop and check if it can be a +2, +1, or cannot be increased, then increase probability
        for i in range(len(power_difference)):
            # check if this slot can be increased by 2
            if power_difference[i] <= 0:
                plus_two_prob += drops[i]/sum_drops
            # check if this slot can be be increased by 1
            elif power_difference[i] == 1:
                plus_one_prob += drops[i]/sum_drops
            else:
                plus_zero_prob += drops[i]/sum_drops

        # reformat +1 pinnacles to proper values, logic. . .
        # if the slot is already +1 it cannot be raised by a plus one pinncle, so we add the chance to go +1 to the +0.
        # in this case the +2 prob is actually the +1 probability so we assign its value to +1 and set it to 0
        if milestone[11] == 1:
            plus_zero_prob += plus_one_prob
            plus_one_prob = plus_two_prob
            plus_two_prob = 0

        # return probabilities
        return [plus_two_prob, plus_one_prob, plus_zero_prob, milestone[11]]

    async def options(self, power_difference, active_milestones):
        # list to hold the info we need
        options_list = []

        # iterate through and calculate probabilities
        for milestone in active_milestones:
            probabilities = await self.calculate_probabilities(power_difference, milestone)
            options_list.append(probabilities)

        return options_list


def setup(bot):
    bot.add_cog(destiny_api_helper_cogs(bot))

