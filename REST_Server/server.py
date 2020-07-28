from flask import (
    Flask, 
    request, 
    render_template,
    redirect
)
import os
from dotenv import load_dotenv
import base64
import requests
import mysql.connector
from datetime import datetime, timedelta
from random import seed
from random import randint

load_dotenv()

bot_oauth = os.getenv('DESTINY_OATH_CLIENT_ID')
bot_secret = os.getenv('BOT_SECRET')
api_key = os.getenv('DESTINY_API_KEY')

# create DB connection
mydb = mysql.connector.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    passwd = os.getenv('DB_PASSWD'),
    database = os.getenv('DATABASE'),
    auth_plugin='mysql_native_password',
    pool_name='sundance_db_pool',
    pool_size=3
)
mydb.close()



# Create the application instance
app = Flask(__name__, template_folder="templates")
authorization_url = f'https://www.bungie.net/en/OAuth/Authorize?client_id={bot_oauth}&response_type=code'


# Create a URL route in our application for "/"
@app.route('/', methods=['GET'])
def home():
  
    return render_template('home.html')

@app.route('/api/v1/oauth', methods=['GET'])
def api_oath():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'code' in request.args:
        auth_code = request.args['code']
    else:
        return "Error: No id field provided. Please specify an id."

    # Get state code from response to match to requester
    if 'state' in request.args:
        state = request.args['state']
    else:
        return "Error: No id field provided. Please specify an id."


    message = f'{bot_oauth}:{bot_secret}'
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    id_and_secret = base64_bytes.decode('ascii')

    header = {'Authorization':f'Basic {id_and_secret}', 'Content-Type':'application/x-www-form-urlencoded'}
    data = {'grant_type':'authorization_code','code':f'{auth_code}'}

    r = requests.post('https://www.bungie.net/platform/app/oauth/token/', headers = header, data = data)

    user_tokens = r.json()
    del r

    access_token = user_tokens['access_token']
    
    ###
    # Need to consider using GetLinkedProfiles using Bungie.net id instead
    #
    #



    header = {'X-API-Key':f'{api_key}', 'Authorization':f'Bearer {access_token}'}
    r = requests.get('https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/', headers = header)
    user_info = r.json()
    del r
    memberID = user_info['Response']['primaryMembershipId']

    # connect to DB
    mydb1 = mysql.connector.connect(pool_name='sundance_db_pool')

    # create object to access DB connection
    mycursor = mydb1.cursor()

    sql = "UPDATE oauth_tokens SET access_token = %s, expires_in = %s, refresh_token = %s, refresh_expires_in = %s, membership_id = %s WHERE state = %s"
    val = (
        user_tokens['access_token'], 
        datetime.now() + timedelta(seconds = int(user_tokens['expires_in'])), 
        user_tokens['refresh_token'],
        datetime.now() + timedelta(seconds = int(user_tokens['refresh_expires_in'])), 
        memberID,
        state
    )
    mycursor.execute(sql, val)
    mydb1.commit()
    mydb1.close()

    # r = requests.get('https://www.bungie.net/Platform/User/GetCurrentBungieNetUser/', headers = header)
    # user_info = r.json()
    # del r

    # bungieName = user_info['Response'].get('displayName', 'Bungie account name not found')
    # steamName = user_info['Response'].get('steamDisplayName', "No Steam name found")
    # xboxName = user_info['Response'].get('xboxDisplayName', "No Xbox name found")
    # psnName = user_info['Response'].get('psnDisplayName', "No PSN name found")
    # stadiaName = user_info['Response'].get('stadiaDisplayName', "No Stadia name found")

    

    # Use the jsonify function from Flask to convert our list of
    # Python dictionaries to the JSON format.
    return render_template('success.html')

@app.route('/api/v1/authenticate', methods=['GET'])
def api_auth():
    # Check if an ID was provided as part of the URL.
    # If ID is provided, assign it to a variable.
    # If no ID is provided, display an error in the browser.
    if 'id' in request.args:
        discordID = request.args['id']
    else:
        return "Error: No id field provided. Please specify an id."

    seed(datetime.now())
    # generate random state value
    state = randint(1000, 99999)
    
    mydb2 = mysql.connector.connect(pool_name='sundance_db_pool')
    mycursor = mydb2.cursor()

    sql = 'REPLACE INTO `oauth_tokens` SET `discordID` = %s, state = %s'
    val = (discordID,  state)
    mycursor.execute(sql, val)
    mydb2.commit()
    mydb2.close()

    # add code to generate random statecode
    # add statecode to end of url + "&state=statecode"
    
    return redirect(authorization_url + f'&state={state}')
    

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', ssl_context = ('/etc/letsencrypt/live/destiny.scarfi.me/fullchain.pem', '/etc/letsencrypt/live/destiny.scarfi.me/privkey.pem'))