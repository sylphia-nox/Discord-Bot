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

bot_oauth = os.getenv('DESTINY_OATH_CLIENT_ID')
bot_secret = os.getenv('BOT_SECRET')

# Create the application instance
app = Flask(__name__, template_folder="templates")
authorization_url = f'https://www.bungie.net/en/OAuth/Authorize?client_id={bot_oauth}&response_type=code'
# &state=33443

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

    print(r)
    #user_tokens = r.json()
    #print(user_tokens)

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
        print(discordID)
    else:
        return "Error: No id field provided. Please specify an id."

   

    




    # add code to generate random statecode
    # add statecode to end of url + "&state=statecode"
    
    return redirect(authorization_url)
    

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    app.run(debug=True, host = '0.0.0.0', ssl_context = ('cert.pem', 'key.pem'))