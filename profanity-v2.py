from pprint import pprint
import requests
import json
import sys
import os
import re


try:
    from flask import Flask
    from flask import request
except ImportError as e:
    print(e)
    print("Looks like 'flask' library is missing.\n"
          "Type 'pip3 install flask' command to install the missing library.")
    sys.exit()

# Load ban list and profanity list
banList = json.loads(open('banList.json').read())
profanityList = json.loads(open('profanityList.json').read())
apiurl = "https://api.ciscospark.com/v1"

# Grab Bot token from env file and setup json headers
bearer = os.environ.get("BOT_ACCESS_TOKEN")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer
}

def send_spark_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js == True:
        request= request.json()
    return request

def send_spark_post(url, data):

    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request

# Help Menu
# need f in front to print curly brackets properly
def help_menu():

    return "Here is what I can do:<br/>" \
        f"plist {{add,remove,search,list}} {{value}} - Modify the profanity word list of banned words<br/>" \
        f"blist {{add,remove,search,list}} {{value}} - Modify the list of banned users<br/>" \
        "ex. plist add butt - will add 'butt' to the banned word list" \

# Welcome menu when bot first joins room
def welcome_msg():

    return "Hi my name is %s.<br/>" \
        "I am here to monitor the messages in this room for profanity<br/>" \
        "Please watch your language or you will be removed from the room<br/>" % bot_name


def profanity_msg():

    return "You done gone messed up now A-Aron"


app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def spark_webhook():
    global in_message
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        if webhook['data']['personEmail']!= bot_email:
            pprint(webhook)
        if webhook['resource'] == "memberships" and webhook['data']['personEmail'] == bot_email:
            send_spark_post(apiurl + "/messages",
                            {
                                "roomId": webhook['data']['roomId'],
                                "markdown": (greetings() +
                                             "**Note This is a group room and you have to call "
                                             "me specifically with `@%s` for me to respond**" % bot_name)
                                                                        }
                            )
        msg = None
        if "@webex.bot" not in webhook['data']['personEmail']:
            result = send_spark_get(
                apiurl + '/messages/{0}'.format(webhook['data']['id']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            if in_message.startswith('help'):
                msg = help_menu()
            elif in_message.startswith('hello'):
                msg = welcome_msg()
            elif in_message.startswith('plist'):
                msg = botcommands()
            else: 
                msg =  "You done messed up A-Aron!"
            if msg != None:
                send_spark_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})
        return "true"
        
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Spark Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Cisco Spark!</i></b></center>" % bot_name
        return message


def botcommands():
    global in_message
    # Load profanity and ban list files
    profanityList = open('database.json', 'r')
    profanityList_data = json.load(profanityList)
    banList = open('banList.json', 'r')
    banList_data = json.load(banList)

    if in_message.startswith("plist add"):
        in_message = in_message.split()
        addProfanity = in_message[-1]
        addProfanity = addProfanity.lower()
        profanityList = open('profanityList.json', 'r')
        profanityList_data = json.load(profanityList)
        profanityList.close()

        for word in profanityList_data:
            if addProfanity in profanityList_data:
                return "That word is already on the banned word list"
                break
            else:
                profanityList_data.append(addProfanity)
                profanityList = open('profanityList.json', 'w')
                json.dump(profanityList_data, profanityList)
                profanityList.close()
                return "That word has been added to the banned word list"
                break
    elif in_message.startswith("plist search"):
        in_message = in_message.split()
        searchProfanity = in_message[-1]
        searchProfanity = searchProfanity.lower()
        profanityList = open('profanityList.json', 'r')
        profanityList_data = json.load(profanityList)
        profanityList.close()
        
        for word in profanityList_data:
            if searchProfanity in profanityList_data:
                return "That word is on the ban list"
                break
            else:
                return "That word is NOT on the ban list"
                break

    elif in_message.startswith("plist list"):
        return json.dumps(profanityList_data, indent=2)

    elif in_message.startswith("plist remove"):
        in_message = in_message.split()
        removeProfanity = in_message[-1]
        removeProfanity = removeProfanity.lower()
        profanityList = open('profanityList.json', 'r')
        profanityList_data = json.load(profanityList)
        profanityList.close()
        
        for word in profanityList_data:
            if removeProfanity in profanityList_data:
                profanityList_data.remove(removeProfanity)
                profanityList = open('profanityList.json', 'w')
                json.dump(profanityList_data, profanityList)
                profanityList.close()
                return "That word has been removed from the banned word list"
                break
            else:
                return "That word is NOT on the banned word list"
                break
    else:
        return "Sorry I didn't understand your command"
        


# Checks to make sure token is valid and for a bot
def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_spark_get(apiurl + "/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.ciscospark.com/apps.html "
                  "URL and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName","")
            bot_email = test_auth.get("emails","")[0]
    else:
        print("'bearer' variable is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.ciscospark.com/apps.html "
              "URL and generate a new access token.")
        sys.exit()
# Provided token does not match up to bot account that ends in "webex.bot"
    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access toekneview it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.ciscospark.com/apps.html "
              "URL and generate a new access token for your Bot.")
        sys.exit()
    else:
        app.run(host='localhost', port=5000)

if __name__ == "__main__":
    main()
