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

bot_oauth = os.getenv('DESTINY_OATH_CLIENT_ID')
bot_secret = os.getenv('BOT_SECRET')

# create DB connection
mydb = mysql.connector.connect(
    host = os.getenv('DB_HOST'),
    user = os.getenv('DB_USER'),
    passwd = os.getenv('DB_PASSWD'),
    database = os.getenv('DATABASE'),
    auth_plugin='mysql_native_password'
)

# create object to access DB connection
mycursor = mydb.cursor()

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

    message = f'{bot_oauth}:{bot_secret}'
    message_bytes = message.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    id_and_secret = base64_bytes.decode('ascii')

    header = {'Authorization':f'Basic {id_and_secret}', 'Content-Type':'application/x-www-form-urlencoded'}
    data = {'grant_type':'authorization_code','code':f'{auth_code}'}

    r = requests.post('https://www.bungie.net/platform/app/oauth/token/', headers = header, data = data)

    user_tokens = r.json()
    print(user_tokens)

    #sql = "UPDATE raid_plan SET access_token = %s, expires_in = %s, refresh_token = %, refresh_expires_in = %, membership_id = % WHERE state = %s"
    #val = (f'{user.id}', raid_id)
    #mycursor.execute(sql, val)
    #mydb.commit()
    #now + timedelta(minutes = 70)

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

    seed(datetime.now)
    # generate random state value
    state = randint(1000, 99999)
    
    sql = 'INSERT IGNORE INTO `oauth_tokens` SET `discordID` = %s, state = %s'
    val = (discordID,  state)
    mycursor.execute(sql, val)
    mydb.commit()

    # add code to generate random statecode
    # add statecode to end of url + "&state=statecode"
    
    return redirect(authorization_url + f'&state={state}')
    

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', ssl_context = ('cert.pem', 'key.pem'))