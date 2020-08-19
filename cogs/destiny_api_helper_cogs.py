# this cog provides the backend functionality for destiny_api_cogs.py and interacts with the Bungie.net APIs.  It relies on helper_cogs.py for some functionality.

from discord.ext import commands
from dotenv import load_dotenv
import discord
import requests
import os
import json
import errors
import numpy as np
import pandas as pd
import base64
from datetime import datetime, timedelta
from dateutil.parser import parse

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

        # load api cogs.
        global api
        api = self.bot.get_cog('Destiny API Utilities')
        if(api is None):
            print(f'Fatal error, Destiny_api_helper_cogs failed to load destiny_api_caller_cogs')

        # load manifests
        self.initialize_manifest()

    # helper function to get Manifest file and save it to global variable
    async def get_manifest(self):
        # grab manifest file for items
        global manifest
        full_manifest = await api.get("/Destiny2/Manifest/")
        manifest_url = full_manifest['Response']['jsonWorldComponentContentPaths']['en']['DestinyInventoryItemLiteDefinition']
        del full_manifest

        manifest = await api.get_simple_async("https://www.bungie.net/" + manifest_url)

    # helper function to initialize manifest file when cog is loaded, non async version of get_manifest
    def initialize_manifest(self):
        global manifest
        full_manifest = api.get_sync("/Destiny2/Manifest/")
        manifest_url = full_manifest['Response']['jsonWorldComponentContentPaths']['en']['DestinyInventoryItemLiteDefinition']
        del full_manifest

        manifest = api.get_simple("https://www.bungie.net/" + manifest_url)
        print('Manifest Initialized')

    # this helper function generates the formatted message for the ~power command
    async def format_power_message(self, high_items, player_char_info, steam_name):
        class_type = player_char_info[2]
        emblem = player_char_info[5]

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

        # create string for displaying each item's power and then its difference from current power
        highest_items = ""
        categories = ['Kinetic','Energy','Power','Helmet','Gauntlets','Chest','Legs','Class Item']
        for i in range(8):
            power_dif = high_items[i] - play_pow
            highest_items = highest_items + f'{categories[i]}: {high_items[i]} ({power_dif:+})\n'

        # create embed
        embed = discord.Embed(title=f'***{steam_name}: {class_name}***', colour=discord.Colour(0x0033cc))

        # set image to player emblem
        embed.set_thumbnail(url=emblem)

        # set embed footer
        embed.set_footer(text="Sundance | created by Michael Scarfi", icon_url="https://drive.google.com/uc?export=view&id=1GRYmllW4Ig9LvsNldcOyU3rpbZPb6fD_")

        # show current power and highest level items
        embed.add_field(name=f'Current Power:', value=play_pow, inline = True)
        # show needed increase in item power for next level.
        embed.add_field(name=f'Power for next level:', value= power_needed, inline = True)

        embed.add_field(name="Highest Items:", value = highest_items, inline = False)


        return embed

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
    async def get_member_info(self, name:str, platform: int = 3):
        # 3 = steam, 2 = xbox, 1 = psn, (4 = stadia?)

        # base url
        global base_url

        # create blank MemberID, needed to raise proper error
        memberID = ""

        #make request for membership ID
        get_user_return = await api.get(f'/Destiny2/SearchDestinyPlayer/{platform}/{name}/')

        # check to get user with exact display name, not full-proof but should reduce issues with grabbing the wrong player
        for user in get_user_return['Response']:
            try:
                if(user['displayName'] == name):
                    
                    # get member ID for user
                    memberID = user['membershipId']

                    # get membershipType
                    membershipType = user['membershipType']
                    print(f'Found matching user {memberID} {membershipType}')
            except IndexError:
                raise errors.PlayerNotFound("Bungie account could not be found, if there is any whitespace in your name make sure you surround it with quotes")

        # could not get exact match, return first results
        if(memberID == ""):
            try: 
                print('could not find user')
                # get member ID for user
                memberID = get_user_return['Response'][0]['membershipId']

                # get membershipType
                membershipType = get_user_return['Response'][0]['membershipType']
            except IndexError:
                raise errors.PlayerNotFound("Bungie account could not be found, if there is any whitespace in your name make sure you surround it with quotes")


        # deleting json to save resources
        del get_user_return

        # return memberID and membershipType
        return [memberID, membershipType, name]

    # helper function to get player info using Oauth token, returns [memberID, membershipType, displayName]
    async def get_member_info_Oauth(self, discordID):
        sql = f'SELECT `access_token`, `expires_in`, `refresh_token`, `refresh_expires_in`, `membership_id` FROM oauth_tokens WHERE discordID = {discordID};'
        sql_return = await helpers.query_db(sql)
        if sql_return:
            now = datetime.now() + timedelta(minutes = 1)
            # check if access token is expired
            if now < parse(sql_return[0][1]):
                token = sql_return[0][0]
            elif now < parse(sql_return[0][3]):
                token = await api.refresh_token(sql_return[0][2], discordID)
            else:
                raise errors.OauthError("Oauth Error, please authenticate or provide the account name in the command.")
        else:
            raise errors.OauthError("Oauth Error, please authenticate or provide the account name in the command.")

        user_info = await api.get("/User/GetMembershipsForCurrentUser/", True, access_token = token)
        memberID = user_info['Response']['destinyMemberships'][0].get('membershipId')
        memberID = user_info['Response'].get('primaryMembershipId', memberID)
        for account in user_info['Response']['destinyMemberships']:
            if int(account.get('membershipId')) == int(memberID):
                membershipType = account.get('membershipType')
                displayName = account.get('LastSeenDisplayName')
                break

        return [memberID, membershipType, displayName, token]


    # helper function to get player info as player[memberID, membershipType, class_type, char_ids]
    async def get_player_char_info(self, memberID, membershipType, character: str, OAuth = False, access_token = ""):
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
        get_characters_return = await api.get(f'/Destiny2/{membershipType}/Profile/{memberID}/?components=200', OAuth, access_token)

        # get character IDs and confirm user has a character of the requested class
        char_ids = []
        has_character = False
        for key in get_characters_return['Response']['characters']['data']:
            char_ids.append(key)
            if (get_characters_return['Response']['characters']['data'][str(key)]['classType'] == character_class):
                has_character = True
                char_id = key
                emblem = get_characters_return['Response']['characters']['data'][str(key)]['emblemPath']

        # if user does not have a character of that class, raise exception
        if (not has_character):
            raise errors.NoCharacterOfClass(f'You do not have a character of class {character}')

        emblem = "https://www.bungie.net" + emblem

        # delete json to save memory
        del get_characters_return

        player_char_info = [memberID, membershipType, character_class, char_ids, char_id, emblem]
        return player_char_info

    # helper function to get list of items as items[InstanceID, itemType, itemSubType, power_level]
    async def get_player_items(self, player_char_info, OAuth = False, access_token = ""):
        global manifest

        # declare list to hold items
        items = []

        # get variable information from list, doing this way for ease of reading code.
        memberID = player_char_info[0]
        membershipType = player_char_info[1]
        class_type = player_char_info[2]
        char_ids = player_char_info[3]

        # get all items and info for items
        json_return = await api.get(f'/Destiny2/{membershipType}/Profile/{memberID}/?components=102, 201, 205, 300', OAuth, access_token)
       
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
            raise errors.PrivacyOnException("Items could not be loaded, ensure your privacy settings allow others to view your inventory or authenticate using `~authenticate`.")
        

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
                try:
                    power_level = item_info[itemInstanceID]['primaryStat']['value']
                except:
                    power_level = 0

                items_list.append([itemInstanceID, itemType, itemSubType, power_level])

        del json
        return items_list

    # helper function to get milestones for a character
    async def get_player_milestones(self, player_char_info, OAuth = False, access_token = ""):
        global manifest

        # declare list to hold items
        active_pinnacles = []

        # get variable information from list, doing this way for ease of reading code.
        memberID = player_char_info[0]
        membershipType = player_char_info[1]
        char_id = player_char_info[4]

        # get all items and info for items
        json_return = await api.get(f'/Destiny2/{membershipType}/Profile/{memberID}/Character/{char_id}/?components=202', OAuth, access_token)
        
        # try to get list of milestones from return, if privacy is an issue this should fail with a KeyError
        try:
            # pull out item_info
            milestones = json_return['Response']['progressions']['data']['milestones']
            del json_return
        except KeyError:
            raise errors.PrivacyOnException("Items could not be loaded, ensure your privacy settings allow others to view your inventory or authenticate using `~authenticate`.")
        
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
    async def calculate_next_step(self, high_items, player_char_info, embed, OAuth = False, access_token = ""):
        # get current power level boundaries
        sql_return = await helpers.query_db("SELECT `field_one`, `field_two`, `field_three` FROM `current_info` WHERE `name` = 'power_levels'")
        power_level_brackets = sql_return[0]

        # calculate average power
        current_play_pow = int(sum(high_items)/8)

        # check if player is below prime/powerful bracket.
        if(current_play_pow < int(power_level_brackets[0])):
            embed.add_field(name="Next Level:", value = "You can level up by doing anything.  Go play some Destiny!", inline = False)
            return embed
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

                # check if player can go up a power level by getting at level drops
                if(potential_power_increase >= 1):
                    embed.add_field(name="Levels that can be gained by at-level drops:", value = f'**{potential_power_increase}**: These can be aquired in any activity at your current power level.', inline = False)
                  

                # create item slot array to ease translation
                categories = ['Kinetic','Energy','Power','Helmet','Gauntlets','Chest','Legs','Class Item']

                sub_message = ""
                for index, item in enumerate(high_items):
                    if item < current_play_pow:
                        high_items[index] = current_play_pow
                        sub_message += f'- {categories[index]}\n'

                if sub_message != "":
                    embed.add_field(name = "Items that can be increased by at-level drops:", value = sub_message, inline = False)

                
                # if player needs prime/powerfuls to level up, let them know how much in each slot.
                if(potential_power_increase <= 0):
                    # calculate power to next level
                    power_needed = 8-(sum(high_items)%8)

                    # add to message string
                    embed.add_field(name="Next Level:", value = f'You need +{power_needed} above your current average from prime/powerfuls to hit the next power level.\nLook for {destiny_challenge_emote} on the map.', inline = False)

                # add message to embed and return embed
                return embed
            
            # check if chareacter is in the pinnacle bracket
            elif(current_play_pow < int(power_level_brackets[2])):
                # create item slot array to ease translation
                categories = ['Kinetic','Energy','Power','Helmet','Gauntlets','Chest','Legs','Class Item']
                
                # create sub_message contianing items that can be leveled up by getting at level drops.
                sub_message = ""
                for index, item in enumerate(high_items):
                    if item < current_play_pow:
                        high_items[index] = current_play_pow
                        sub_message += f'- {categories[index]}\n'

                if(potential_power_increase >= 1):
                    # create message
                    embed.add_field(name="Levels that can be gained by at-level drops:", value = f'**{potential_power_increase}**: Look for {destiny_challenge_emote} on the map.', inline = False)
                    # append sub message if appropriate
                    if sub_message != "":
                        embed.add_field(name = "Items that can be increased by getting prime/powerful drops:", value = sub_message, inline = False)
                    
                    return embed
                else: 
                    
                    # check if there are items below average power
                    if sub_message != "":
                        embed.add_field(name = "Items that can be increased by getting prime/powerful drops:", value = sub_message, inline = False)

                    # calculate power to next level
                    power_needed = 8-(sum(high_items)%8)
                    embed.add_field(name = "Pinnacle Power needed:", value = power_needed, inline = True)

                    # create list of power differences
                    power_difference = []
                    for item in high_items:
                        power_difference.append(item - current_play_pow)

                    # get active milestones and milestone info
                    active_milestones = await self.get_player_milestones(player_char_info, OAuth, access_token)

                    # get probability array (returns each possible activity with percent change of increasing +2, +1, or +0, final row is if the pinnacle is a +1 or +2)
                    probability_array = await self.options(power_difference, active_milestones)
                    
                    # get recommendations
                    recommendation_message = await self.get_recommendation(active_milestones, probability_array, power_needed, high_items, power_level_brackets)

                    # add recommendation to embed
                    embed.add_field(name = "Pinnacle Sources:", value = recommendation_message, inline = False)

                    # return message
                    return embed
            
            # check if character is at max power
            elif(current_play_pow == int(power_level_brackets[2])):
                embed.add_field(name="Next Level:", value = "Character is currently at maximum power, congratulations!", inline = False)
                return embed
            
            # if none of these catch we have an error
            else:
                embed.add_field(name="Next Level:", value = "Error, player power not within possible levels", inline = False)
                return embed

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
                    message += 'You are in the final push\n *Pinnacles you can run and probability of getting a needed item:*\n'

                    # create new array with just activity name and probability of +1/+2 increase (since we are 1 away we want the non +0 probability)
                    final_push_milestones = []

                    # cycle through and add each active_milestones to final_push_milestones
                    for i, activity in enumerate(probability_array):
                        # We need the odds of increasing the power level in that slot, since we can't go up +1 here we need to adjust, at this point, the formula thinks that any +2 drop can give +1 to slots already at max power
                        # so, we need to remove those from the equation, for +1s, the +1 odd is correct.
                        if(activity[3] == 2):
                            probability = activity[0]
                        else:
                            probability = activity[1]
                        
                        final_push_milestones.append([active_milestones[i][2], probability])
                        # since we have been dealing with floats, if a probabilty is almost 1.00 change it to be 1
                        if(final_push_milestones[i][1] >= .99):
                            final_push_milestones[i][1] = 1


                    # create dtype to format structured array
                    dtype = np.dtype([('name', 'O'), ('probability', '<f8')])

                    # convert array to nparray 
                    temp = np.array(final_push_milestones)

                    # transform nparray to structured array with column names so it can be sorted
                    active_milestones = np.rec.fromarrays(temp.T, dtype=dtype)
                    del temp                                                                # del temp array to save resources
                    
                    active_milestones = np.sort(active_milestones, order='probability')     # sort the array
                    active_milestones = np.flip(active_milestones)                          # flip array so it is in descending order.

                    for milestone in active_milestones:
                        message += f'{milestone[1]*100:.1f}%: {milestone[0]}\n'
                
                    # del array to save memory since it contains large strings
                    del active_milestones

            # everything else needs to make special consideration of raid probabilities
            else:
                # split out raid information from everything else
                raid_prob = []
                raid_info = []

                # sadly, a non-pythonic loop but this is the easiest way to iterate backwards, there is probably a more pythonic way to accomplish this task
                # we need to split out the raid activities from the rest the filter is if the active_milestones hash [1] == the raid hash
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
                    message += "Do +1 activities first.\n"
                    message += f'+1 activity(s) with the best chance of raising your light level ({max_prob*100:.1f}%):\n'

                    # iterate through list and print out activities with prob matching top probability and at +1 power
                    for i, activity_prob in enumerate(probability_array):
                        if activity_prob[1] == max_prob and activity_prob[3] == 1:
                            message += f'- {active_milestones[i][2]}\n'

                # if player is two away and has not completed the raid, check if it makes sense to run the raid.
                elif(power_needed <= 2 and any(raid_info)):
                    if(raid_prob[0][0] > .5 or raid_prob[1][0] > .5):
                        message += "Consider running the raid since there is a high chance you will go up a light level in the first two encounters:\n"
                        for i, encounter in enumerate(raid_info):
                            message += f'- {encounter[2]} | +2: {raid_prob[i][0]*100:.1f}%, +1: {raid_prob[i][1]*100:.1f}%\n'

                # get best probability of a +2 drop.
                max_prob = np.max(prob_array[0])
                # confirm there are +2 activities that can raise a gear slot by 2.
                if(max_prob != 0):
                    message += f'+2 activity(s) with the best chance of raising one of your equipement slots by 2:\n'

                    # iterate through list and print out activities with prob matching top probability and at +2 power
                    for i, activity_prob in enumerate(probability_array):
                        if activity_prob[0] == max_prob and activity_prob[3] == 2:
                            message += f'- {active_milestones[i][2]} | +2: {activity_prob[0]*100:.1f}%, +1: {activity_prob[1]*100:.1f}%\n'

                else:
                    message += f'There are currently no activities that can raise an equipement slot by 2:\n'
                    # check if their are +1 activities and that we have not already sent them to the message
                    if (1 in prob_array[3] and power_needed !=1):
                        # get +1 activities
                        valid_probs = prob_array[1][(prob_array[3] == 1)]
                        max_prob = np.max(valid_probs)
                        message += f'+1 activity(s) with the best chance of raising your light level ({max_prob*100:.1f}%):\n'

                        # iterate through list and print out activities with prob matching top probability and at +1 power
                        for i, activity_prob in enumerate(probability_array):
                            if activity_prob[1] == max_prob and activity_prob[3] == 1:
                                message += f'- {active_milestones[i][2]}\n'

                    elif 2 in prob_array[3]:
                        # get +2 activities
                        valid_probs = prob_array[1][(prob_array[3] == 2)]
                        max_prob = np.max(valid_probs)
                        message += f'+2 activity(s) with the best chance of raising a gear slot by +1 ({max_prob*100:.1f}%):\n'
                        # iterate through list and print out activities with prob matching top probability and at +1 power
                        for i, activity_prob in enumerate(probability_array):
                            if activity_prob[1] == max_prob and activity_prob[3] == 1:
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
        for i, diff in enumerate(power_difference):
            # check if this slot can be increased by 2
            if diff <= 0:
                plus_two_prob += drops[i]/sum_drops
            # check if this slot can be be increased by 1
            elif diff == 1:
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

    # helper function to get Oauth token for user
    async def get_user_token(self, discordID, memberID):
        sql = f'SELECT * FROM oauth_tokens WHERE discordID = {discordID} and membership_id = {memberID}'
        sql_return = await helpers.query_db(sql)
        if sql_return:
            now = datetime.now() + timedelta(minutes = 1)
            # check if access token is expired
            if now < parse(sql_return[0][3]):
                return sql_return[0][2]
            elif now < parse(sql_return[0][5]):
                return await api.refresh_token(sql_return[0][4], discordID)
            else:
                return "refresh token expired"
        else:
            print (sql_return)
            return "token not found"

    # helper function to update the plug DB info.
    def update_plugs(self):
        full_manifest = api.get_sync("/Destiny2/Manifest/")
        manifest_url = full_manifest['Response']['jsonWorldComponentContentPaths']['en']['DestinyInventoryItemDefinition']
        del full_manifest

        item_manifest = api.get_simple("https://www.bungie.net/" + manifest_url)


        for key, item in item_manifest.items():
            if "plug" in item:
                # print("found plug:" + f'{item["hash"]}')
                if item["plug"]["plugCategoryIdentifier"] == "intrinsics":
                    stats = item["investmentStats"]
                    values = []
                    if stats:
                        isPlug = True
                    
                        for stat in stats:
                            category = int(stat["statTypeHash"])
                            if category == 2996146975:
                                category = "mobility"
                            elif category == 392767087:
                                category = "recovery"
                            elif category == 1943323491:
                                category = "resilience"
                            elif category == 1735777505:
                                category = "discipline"
                            elif category == 144602215:
                                category = "intellect"
                            elif category == 4244567218:
                                category = "strength"
                            else:
                                isPlug = False
                            
                            value = int(stat["value"])
                            values.append([category, value])

                        if isPlug:
                            sql = f'REPLACE INTO `plugs` (`hash`, `{values[0][0]}`, `{values[1][0]}`, `{values[2][0]}`) ' + 'VALUES (%s, %s, %s, %s)'
                            vals = [int(key), values[0][1], values[1][1], values[2][1]]

                            helpers.write_db_sync(sql, vals)

    # helper function to get list of items as items[InstanceID, itemType, itemSubType, power_level]
    async def get_player_armor(self, player_char_info, OAuth = False, access_token = ""):
        global manifest

        # declare list to hold items
        items = []

        # get variable information from list, doing this way for ease of reading code.
        memberID = player_char_info[0]
        membershipType = player_char_info[1]
        class_type = player_char_info[2]
        char_ids = player_char_info[3]

        # get all items and info for items
        json_return = await api.get(f'/Destiny2/{membershipType}/Profile/{memberID}/?components=102, 201, 205, 305', OAuth, access_token)
       
        # pull out armor item info
        armor_sockets = json_return['Response']['itemComponents']['sockets']['data']
        
        # if user has privacy on, the json will not have the 'data' tag, so we can use this assignment to raise a PrivacySettings exception
        try:
            # parse vault items
            items = await self.parse_json_for_armor_info(json_return['Response']['profileInventory']['data']['items'], items, class_type, armor_sockets)

            # parse equiped and unequiped items
            for id in char_ids:
                items = await self.parse_json_for_armor_info(json_return['Response']['characterInventories']['data'][id]['items'], items, class_type, armor_sockets)
                items = await self.parse_json_for_armor_info(json_return['Response']['characterEquipment']['data'][id]['items'], items, class_type, armor_sockets)
        except KeyError:
            raise errors.PrivacyOnException("Items could not be loaded, ensure your privacy settings allow others to view your inventory or authenticate using `~authenticate`.")
        

        # deleting variable to save memory usage.
        del armor_sockets
        del json_return

        return items

    # helper function to parse JSON, returns items[] that can be equiped by class_type
    async def parse_json_for_armor_info(self, json, items_list, class_type, armor_sockets):
        global manifest

        for item in json:
            itemHash = str(item['itemHash'])
            itemType = manifest[itemHash]['itemType']
            itemClassType = manifest[itemHash]['classType']
            # check if the item can be used by the specified character
            if itemType == 2 and itemClassType == class_type:
                itemSubType = manifest[itemHash]['itemSubType']

                # now that we know this is an instanced item, get its ID to get the items power level
                itemInstanceID = str(item['itemInstanceId'])
                # run api call to get power cap
                try:
                    power_cap = manifest[itemHash]['quality']['versions'][0]['powerCapHash']
                    exotic = int(manifest[itemHash]['inventory']['tierType']) == 6
                except:
                    power_cap = 0
                    exotic = False

                item_stats = await self.get_armor_stats(itemInstanceID, armor_sockets)

                items_list.append([itemInstanceID, itemType, itemSubType, power_cap, exotic, item_stats, itemHash])

        del json
        return items_list

    async def get_armor_stats(self, itemID, armor_sockets):
        sockets = armor_sockets[itemID]['sockets']
        intrinsic_sockets = []
        stats = [0,0,0,0,0,0]
        for socket in sockets:
            if "plugHash" in socket and (socket["isEnabled"] and not socket["isVisible"]):
                intrinsic_sockets.append(socket["plugHash"])
        # confirm we have 4 intrinsic plugs, helps avoid outliers like class items.
        if len(intrinsic_sockets) == 4:
            # query DB to get plug info
            select = f'SELECT IFNULL(mobility,0) as `mobility`, IFNULL(recovery,0) as `recovery`, IFNULL(resilience,0) as `resilience`, IFNULL(discipline,0) as `discipline`, IFNULL(intellect,0) as `intellect`, IFNULL(strength,0) as `strength` FROM plugs '
            where = f'WHERE hash = {intrinsic_sockets[0]} OR hash = {intrinsic_sockets[1]} OR hash = {intrinsic_sockets[2]} OR hash = {intrinsic_sockets[3]};'
            sql = select + where
            plugs = await helpers.query_db(sql)

            # if we have dupe plugs the SQL will not return that so we need to add them in.
            if intrinsic_sockets[0] == intrinsic_sockets[1]:
                # I want to see if this is possible so adding in a print statement
                plugs.insert(0, plugs[0])
            elif intrinsic_sockets[2] == intrinsic_sockets[3]:
                # I want to see if this is possible so adding in a print statement
                plugs.insert(2, plugs[2])

            # iterate through plugs to get total stat values
            for plug in plugs:
                for i, stat in enumerate(plug):
                    stats[i] += int(stat)

        return stats

    # this function returns the armor with the highest stats in the 2 primary stat columns and a reduced list of armor items.
    async def get_max_stat_items(self, items, stat1, stat2):
        high_items = [[],[],[],[]]
        high_values = [0,0,0,0]
        reduced_item_list = []
        # parse entire list, for each type of item, if current item has a higher power level, update power level to new level.
        for item in items:
            # if helmet
            if item[2] == 26:
                # update item slot for easier use down the road and append to reduced list
                item[2] = 0
                reduced_item_list.append(item)

                # check if item is better than current in that slot
                value = item[5][stat1-1] + item[5][stat2-1]
                if  value > high_values[0]:
                    high_values[0] = value
                    high_items[0] = item
            # if gauntlets
            elif item[2] == 27:
                item[2] = 1
                reduced_item_list.append(item)

                value = item[5][stat1-1] + item[5][stat2-1]
                if  value > high_values[1]:
                    high_values[1] = value
                    high_items[1] = item
            # if chest
            elif item[2] == 28:
                item[2] = 2
                reduced_item_list.append(item)

                value = item[5][stat1-1] + item[5][stat2-1]
                if  value > high_values[2]:
                    high_values[2] = value
                    high_items[2] = item
            # if legs
            elif item[2] == 29:
                item[2] = 3
                reduced_item_list.append(item)

                value = item[5][stat1-1] + item[5][stat2-1]
                if  value > high_values[3]:
                    high_values[3] = value
                    high_items[3] = item

        # return list of best items
        return high_items, reduced_item_list, high_values

    # this function returns a list of optimized gear
    async def optimize_armor(self, items, trait1, trait2, trait3, traction: bool = False, friends: bool = False):
        high_items, items, high_values = await self.get_max_stat_items(items, trait1, trait2)
        
        #setup variables to work with
        stat1_goal = 100
        stat2_goal = 100
        stat3_goal = 100
        stat1 = 0
        stat2 = 0
        stat3 = 0

        # if optimizing mobility and traction or friends, adjust goal
        if trait1 == 1:
            if traction:
                stat1_goal -= 15
            if friends:
                stat1_goal -= 20
        elif trait2 == 1:
            if traction:
                stat2_goal -= 15
            if friends:
                stat2_goal -= 20
        elif trait3 == 1:
            if traction:
                stat3_goal -= 15
            if friends:
                stat3_goal -= 20

        # get stat values for best armor
        for item in high_items:
            stat1 += item[5][trait1-1]
            stat2 += item[5][trait2-1] 
            stat3 += item[5][trait3-1] 

        # get deficiencies
        stat1_deficiency = stat1_goal - stat1
        stat2_deficiency = stat2_goal - stat2
        stat3_deficiency = stat3_goal - stat3

        # get tiers away from 100/100, we will use this to calculate score later on
        neg_trait1_tiers = int((stat1_deficiency+99)/10) -9
        neg_trait2_tiers = int((stat2_deficiency+99)/10) -9
        neg_trait3_tiers = int((stat3_deficiency+99)/10) -9

        # remove negative values since tiers over 100 are worthless
        if neg_trait1_tiers < 0:
            neg_trait1_tiers = 0
        if neg_trait2_tiers < 0:
            neg_trait2_tiers = 0
        if neg_trait3_tiers < 0:
            neg_trait3_tiers = 0

        neg_primary_tiers = neg_trait1_tiers + neg_trait2_tiers

        true_surplus = await self.calculate_surplus(stat1_deficiency, stat2_deficiency)

        ###
        # if we have more total points then needed, do something crazy
        #
        #
        #
        ###
        if (stat1 + stat2) > (stat1_goal + stat2_goal + 10):
            true_surplus += (int(((stat1 + stat2) - (stat1_goal + stat2_goal))/10)) * 10
        
        # [itemInstanceID, itemType, itemSubType, power_cap, exotic, item_stats, itemHash]
        item_df = pd.DataFrame(items, columns = ['id', 'itemType', 'itemSubType', 'power_cap', 'exotic', 'item_stats', 'itemHash'])

        ###
        # To-do: Insert code to remove items that don't meet powercap or are not the correct exotic/ in the requested exotic slot
        # 
        #
        ###

        # removing uneeded columns
        item_df = item_df.drop(['itemType','power_cap','exotic'], axis=1)

        # adding column containing total value of primary stats and remove any columns with value of 0
        item_df['desired_total'] = item_df.item_stats.str[trait1-1] + item_df.item_stats.str[trait2-1]

        temp_item_df = item_df    

        # calculate cost for swapping each item and add to DF
        costs = []
        for row in temp_item_df.itertuples(index=False):
            # calculate cost and append to list
            costs.append(high_values[int(row.itemSubType)] - int(row.desired_total))

        temp_item_df['cost'] = costs

        # remove all items that result in a reduction in potential tiers if we have too many items.
        if(len(temp_item_df.index) > 100):
            temp_item_df = temp_item_df[temp_item_df.cost <= (true_surplus)]
            temp_item_df = temp_item_df.reset_index(drop=True)

        # current DF format = ['id', 'itemSubType', [item_stats], 'itemHash', 'desired_total', 'cost']
        # desired dF format = ['id', 'itemSubType', 'desired_total', 'cost', 'trai1', trait2', 'trait3', 'primary_score', 'trait3_score']
        calc_item_df = temp_item_df.copy()
        calc_item_df['trait1'] = calc_item_df.item_stats.str[trait1-1]
        calc_item_df['trait2'] = calc_item_df.item_stats.str[trait2-1]
        calc_item_df['trait3'] = calc_item_df.item_stats.str[trait3-1]

        # clear uneeded rows
        calc_item_df.drop(['item_stats', 'itemHash'], axis = 1)

        # create adjusted list of high_items with only the needed values
        temp_test_items = []
        for item in high_items:
            temp_test_items.append([item[5][trait1-1], item[5][trait2-1], item[5][trait3-1]], 0)

        # if we get any piece that increases the tier by at least one we want to reduce surplus by the highest primary_score * 10 since we now know we can hit higher tiers.
        surplus = true_surplus # could set to true_surplus - 10 for a much stricter check process.
        highest_primary_score = 0

        # next we need to reduce the calculations to a manageable amount, but if we are already in range we can avoid that
        if(len(calc_item_df.index) > 100):
            # calculate scores
            primary_scores = []
            trait3_scores = []

            for row in calc_item_df.itertuples(index=False):
                # create temp copy of high_items for manipulation
                test_items = temp_test_items.copy()
                test_items.remove(int(row.itemSubType))

                # add test item to test_items
                test_items.append([row.trait1, row.trait2, row.trait3])

                # get deficiency values
                primary_deficiency, tier3_deficiency, temp_stat1, temp_stat2, temp_stat3 = await self.calculate_scores(test_items, stat1_goal, stat2_goal, stat3_goal)

                # calculate scores
                primary_score = neg_primary_tiers - primary_deficiency
                trait3_score = neg_trait3_tiers - tier3_deficiency

                # check if armor is just a direct decrease in stat values
                if temp_stat1 < stat1 and temp_stat2 < stat2:
                    primary_score -= 1
                if temp_stat3 < stat3:
                    trait3_score -= 1

                # append score values to lists
                primary_scores.append(primary_score)
                trait3_scores.append(neg_trait3_tiers - tier3_deficiency)

                if(primary_score < highest_primary_score):
                    highest_primary_score == primary_score
                
            # del temp_test_items to save resources
            del temp_test_items

            
            calc_item_df['primary_score'] = primary_scores
            calc_item_df['trait3_score'] = trait3_scores

            # remove all items that will decrease score/cannot results in score increase
            if(len(calc_item_df.index) > 100):
                calc_item_df = calc_item_df[calc_item_df.primary_score >= 0]
                calc_item_df = calc_item_df.reset_index(drop=True)
            # if still not under 100 remove items that will not results in increase and will leave no surplus for other armor pieces
            if(len(calc_item_df.index) > 100):
                calc_item_df = calc_item_df[not (calc_item_df.primary_score == 0 and calc_item_df.cost >= (true_surplus-10))]
                calc_item_df = calc_item_df.reset_index(drop=True)
            if(len(calc_item_df.index) > 100):
                calc_item_df = calc_item_df.sort_values(by=['primary_score','cost','trait3_score'], ascending=[False, True, False])
                calc_item_df = calc_item_df.head(100)

        # create list of high_item ids
        high_item_ids = []
        for item in high_items:
            high_item_ids.append(item[0])

        # declare variables for the most unpythonic looping ever.
        helmets = calc_item_df[calc_item_df.itemSubType == 0].sort_values(by='cost', ascending=True)
        arms = calc_item_df[calc_item_df.itemSubType == 1].sort_values(by='cost', ascending=True)
        chests = calc_item_df[calc_item_df.itemSubType == 2].sort_values(by='cost', ascending=True)
        boots = calc_item_df[calc_item_df.itemSubType == 3].sort_values(by='cost', ascending=True)

        surplus = surplus - (highest_primary_score *10)
        
        temp_combo_list = []
        helmet_active = True
        helmet_i = -1
        while helmet_active and helmet_i < len(helmets.index):
            # end goal: [[item_ids], cost, trait1, trait2, trait3, primary_score, trait3_score]
            temp_stats = high_items.copy()
            temp_id = high_item_ids.copy()
            # if value is -1 we want to use the default items, else, substitute item from lists
            if(helmet_i != -1):
                # assign stat values
                temp_stats[0] = [helmets.iloc[helmet_i]['trait1'], helmets.iloc[helmet_i]['trait2'], helmets.iloc[helmet_i]['trait3'], helmets.iloc[helmet_i]['cost']]
                # store id
                temp_id[0] = helmets.iloc[helmet_i]['id']

            # calculate cost
            cost = temp_stats[0][3] + temp_stats[1][3] + temp_stats[2][3] + temp_stats[3][3]

            # if cost is less than surplus continue, otherwise, we will exit current loop level.
            if(cost <= surplus):
                # repeat down to the bottom
                arms_active = True
                arms_i = -1
                while arms_active and arms_i < len(arms.index):
                    if(arms_i != -1):
                        temp_stats[1] = [helmets.iloc[arms_i]['trait1'], helmets.iloc[arms_i]['trait2'], helmets.iloc[arms_i]['trait3'], helmets.iloc[arms_i]['cost']]
                        temp_id[1] = helmets.iloc[arms_i]['id']
                    cost = temp_stats[0][3] + temp_stats[1][3] + temp_stats[2][3] + temp_stats[3][3]
                    if(cost <= surplus):
                        chest_active = True
                        chest_i = -1
                        while chest_active and chest_i < len(chests.index):
                            if(chest_i != -1):
                                temp_stats[2] = [helmets.iloc[chest_i]['trait1'], helmets.iloc[chest_i]['trait2'], helmets.iloc[chest_i]['trait3'], helmets.iloc[chest_i]['cost']]
                                temp_id[2] = helmets.iloc[chest_i]['id']
                            cost = temp_stats[0][3] + temp_stats[1][3] + temp_stats[2][3] + temp_stats[3][3]
                            if(cost <= surplus):
                                boots_active = True
                                boots_i = -1
                                while boots_active and boots_i < len(boots.index):
                                    if(boots_i != -1):
                                        temp_stats[3] = [helmets.iloc[boots_i]['trait1'], helmets.iloc[boots_i]['trait2'], helmets.iloc[boots_i]['trait3'], helmets.iloc[boots_i]['cost']]
                                        temp_id[3] = helmets.iloc[boots_i]['id']
                                    cost = temp_stats[0][3] + temp_stats[1][3] + temp_stats[2][3] + temp_stats[3][3]
                                    if(cost <= surplus):
                                        # get raw scores
                                        primary_deficiency, tier3_deficiency, temp_stat1, temp_stat2, temp_stat3 = await self.calculate_scores(temp_stats, stat1_goal, stat2_goal, stat3_goal)

                                        # calculate scores
                                        primary_score = neg_primary_tiers - primary_deficiency
                                        trait3_score = neg_trait3_tiers - tier3_deficiency

                                        # check if armor is just a direct decrease in stat values
                                        if temp_stat1 < stat1 and temp_stat2 < stat2:
                                            primary_score -= 1
                                        if temp_stat3 < stat3:
                                            trait3_score -= 1
                                        
                                        # store scores
                                        temp_combo_list.append([[temp_id[0][0], temp_id[1][0], temp_id[2][0], temp_id[3][0]], cost, temp_stat1, temp_stat2, temp_stat3, primary_score, trait3_score])

                                        # loop succes, iterate
                                        boots_i += 1
                                    # exiting boots loop
                                    else:
                                        boots_active = False
                                # reset slot to default
                                temp_stats[3] = high_items[3]
                                temp_id[3] = high_item_ids[3]
                                # loop succes, iterate
                                chest_i +=1
                            # exiting chest loop
                            else:
                                chest_active = False
                        # reset slot to default
                        temp_stats[2] = high_items[2]
                        temp_id[2] = high_item_ids[2]
                        # loop succes, iterate
                        arms_i +=1
                    # exiting arms loop
                    else:
                        arms_active = False
                # reset slot to default
                temp_stats[1] = high_items[1]
                temp_id[1] = high_item_ids[1]
                # loop succes, iterate
                helmet_i += 1
            # exiting helmet loop
            else:
                helmet_active = False

        # we now have a list of every item combination with stat values.           
        results_df = pd.DataFrame(temp_combo_list, columns = ['ids', 'cost', 'stat1', 'stat2', 'stat3', 'prim_score', 'trait3_score']).sort_values(by=['primary_score','trait3_score','cost'], ascending=[False, False, True]).head()
        return results_df




    # helper function to calculate scores input [trait1, trait2, trait3]
    async def calculate_scores(self, items, stat1_goal, stat2_goal, stat3_goal):
        #setup variables to work with
        stat1 = 0
        stat2 = 0
        stat3 = 0

        # get stat values for best armor
        for item in items:
            stat1 += item[0]
            stat2 += item[1] 
            stat3 += item[2] 

        # get deficiencies
        stat1_deficiency = stat1_goal - stat1
        stat2_deficiency = stat2_goal - stat2
        stat3_deficiency = stat3_goal - stat3

        # get tiers away from 100/100, we will use this to calculate score later on
        neg_trait1_tiers = int((stat1_deficiency+99)/10) -9
        neg_trait2_tiers = int((stat2_deficiency+99)/10) -9
        neg_trait3_tiers = int((stat3_deficiency+99)/10) -9

        # remove negative values since tiers over 100 are worthless
        if neg_trait1_tiers < 0:
            neg_trait1_tiers = 0
        if neg_trait2_tiers < 0:
            neg_trait2_tiers = 0
        if neg_trait3_tiers < 0:
            neg_trait3_tiers = 0

        # calculate combined negative tiers for 2 primary traits
        neg_prim_tiers = neg_trait1_tiers + neg_trait2_tiers

        # return values
        return neg_prim_tiers, neg_trait3_tiers, stat1, stat2, stat3

    async def calculate_surplus(self, stat1_deficiency, stat2_deficiency):
        # get extra points
        if (stat1_deficiency < 0):
            stat1_surplus = abs(stat1_deficiency)
        else:
            stat1_surplus = 10 - stat1_deficiency%10

        if (stat2_deficiency < 0):
            stat2_surplus = abs(stat2_deficiency)
        else:
            stat2_surplus = 10 - stat2_deficiency%10 

        # calculate true surplus
        true_surplus = stat1_surplus + stat2_surplus

        # return values
        return true_surplus

    

        

        



def setup(bot):
    bot.add_cog(destiny_api_helper_cogs(bot))

