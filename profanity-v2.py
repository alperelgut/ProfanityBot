from pprint import pprint
import requests
import json
import sys
import os
import sqltables
from webexteamssdk import WebexTeamsAPI
from sqlalchemy import and_, or_, not_
from sqlalchemy import func

try:
    from flask import Flask
    from flask import request
except ImportError as e:
    print(e)
    print("Looks like 'flask' library is missing.\n"
          "Type 'pip3 install flask' command to install the missing library.")
    sys.exit()

# API Calls and token retrieval

apiurl = "https://api.ciscospark.com/v1"

# Grab Bot token from env file and setup json headers
bearer = os.environ.get("BOT_ACCESS_TOKEN")
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer
}


def send_webex_get(url, payload=None, js=True):
    if payload == None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js == True:
        request = request.json()
    return request


def send_webex_post(url, data):
    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request


def send_webex_delete(url, payload=None):
    if payload is None:
        request = requests.delete(url, headers=headers)
    return request


# Help Menu
# need f in front to print curly brackets properly

def help_menu():
    return "Here is what I can do:<br/>" \
           f"plist {{add,remove,search,list}} {{value}} - Modify the profanity word list of banned words<br/>" \
           "ex. plist add cat - will add 'cat' to the banned word list" \
 \
 \

# Welcome menu when bot first joins room


def welcome_msg():
    return "Hi my name is %s.<br/>" \
           "I am here to monitor the messages in this room for profanity<br/>" \
           "Please watch your language!!<br/>" % bot_name


# Checks input if profanity matches what is in database for the room.

def profanity_check():
    global in_message
    msg = None
    webhook = request.get_json(silent=True)
    matchList = in_message.split()
    for word in matchList:
        query = sqltables.session.query(sqltables.Profanity).filter(
            and_(
                sqltables.Profanity.roomid == webhook['data']['roomId'],
                sqltables.Profanity.words == word
            )
        ).first()
        if query is not None:
            # send_webex_delete(apiurl + "/messages/" + webhook['data']['id'])
            return "Please watch your language in this room.  Profanity is NOT allowed"

# Main Application for message input and routing to method

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST', 'DELETE'])
def webex_webhook():
    global in_message
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        if webhook['data']['personEmail'] != bot_email:
            pprint(webhook)
        if webhook['resource'] == "memberships" and webhook['data']['personEmail'] == bot_email:
            send_webex_post(apiurl + "/messages",
                            {
                                "roomId": webhook['data']['roomId'],
                                "markdown": ("**Note This is a group room and you have to call "
                                             "me specifically with `@%s` for me to respond**" % bot_name)
                            }
                            )
        msg = None
        if "@webex.bot" not in webhook['data']['personEmail']:
            result = send_webex_get(
                apiurl + '/messages/{0}'.format(webhook['data']['id']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            if in_message.startswith('help'):
                msg = help_menu()
            elif in_message.startswith('hello'):
                msg = welcome_msg()
            elif in_message.startswith('plist'):
                msg = botcommands()
            elif in_message.startswith('blist'):
                msg = botcommands()
            else:
                msg = profanity_check()
            if msg != None:
                send_webex_post(apiurl + "/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})
        return "true"

    elif request.method == 'GET':
        message = "<center><h2><b><i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" % bot_name
        return message


# Commands for adding and removing from database

def botcommands():
    global in_message
    if in_message.startswith("plist add"):
        msg = None
        in_message = in_message.split()
        addProfanity = in_message[-1]
        addProfanity = addProfanity.lower()
        webhook = request.get_json(silent=True)
        lastempid = sqltables.session.query(func.max(sqltables.Profanity.empid)).scalar()
        empidnew = lastempid + 1
        query = sqltables.session.query(sqltables.Profanity).filter(
            and_(
                sqltables.Profanity.roomid == webhook['data']['roomId'],
                sqltables.Profanity.words == addProfanity
            )
        ).first()
        if query is None:
            newProfanity = sqltables.Profanity(empid=empidnew,
                                               roomid=webhook['data']['roomId'],
                                               words=addProfanity)
            sqltables.session.add(newProfanity)
            sqltables.session.commit()
            msg = "The word " + addProfanity + " was added to the profanity list for this room"
        else:
            msg = addProfanity + " is already on the profanity list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("plist search"):
        msg = None
        in_message = in_message.split()
        searchProfanity = in_message[-1]
        searchProfanity = searchProfanity.lower()
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Profanity).filter(
            and_(
                sqltables.Profanity.roomid == webhook['data']['roomId'],
                sqltables.Profanity.words == searchProfanity
            )
        ).first()
        if query is None:
            msg = "The word " + searchProfanity + " is NOT on the profanity list for this room"
        else:
            msg = searchProfanity + " is on the profanity list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("plist list"):
        msg = None
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Profanity).filter(
            sqltables.Profanity.roomid == webhook['data']['roomId'])
        for result in query:
            msg = result.words
            if msg != None:
                send_webex_post(apiurl + "/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("plist remove"):
        msg = None
        in_message = in_message.split()
        removeProfanity = in_message[-1]
        removeProfanity = removeProfanity.lower()
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Profanity).filter(
            and_(
                sqltables.Profanity.roomid == webhook['data']['roomId'],
                sqltables.Profanity.words == removeProfanity
            )
        ).first()
        if query is None:
            msg = removeProfanity + "is NOT on the profanity list"
        else:
            sqltables.session.delete(query)
            sqltables.session.commit()
            msg = removeProfanity + " has been removed from the profanity list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})

    if in_message.startswith("blist add"):
        msg = None
        in_message = in_message.split()
        banAdd = in_message[-1]
        banAdd = banAdd.lower()
        webhook = request.get_json(silent=True)
        lastempid = sqltables.session.query(func.max(sqltables.Banlist.empid)).scalar()
        empidnew = lastempid + 1
        query = sqltables.session.query(sqltables.Banlist).filter(
            and_(
                sqltables.Banlist.roomid == webhook['data']['roomId'],
                sqltables.Banlist.users == banAdd
            )
        ).first()
        if query is None:
            newProfanity = sqltables.Banlist(empid=empidnew,
                                             roomid=webhook['data']['roomId'],
                                             users=banAdd)
            sqltables.session.add(newProfanity)
            sqltables.session.commit()
            msg = "The user " + banAdd + " was added to the banned users list for this room"
        else:
            msg = banAdd + " is already on the banned users list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("blist search"):
        msg = None
        in_message = in_message.split()
        banSearch = in_message[-1]
        banSearch = banSearch.lower()
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Banlist).filter(
            and_(
                sqltables.Banlist.roomid == webhook['data']['roomId'],
                sqltables.Banlist.users == banSearch
            )
        ).first()
        if query is None:
            msg = "The user " + banSearch + " is NOT on the banned users list for this room"
        else:
            msg = banSearch + " is on the banned users list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("blist list"):
        msg = None
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Banlist).filter(sqltables.Banlist.roomid == webhook['data']['roomId'])
        for result in query:
            msg = result.users
            if msg != None:
                send_webex_post(apiurl + "/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("blist remove"):
        msg = None
        in_message = in_message.split()
        banRemove = in_message[-1]
        banRemove = banRemove.lower()
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Banlist).filter(
            and_(
                sqltables.Banlist.roomid == webhook['data']['roomId'],
                sqltables.Banlist.users == banRemove
            )
        ).first()
        if query is None:
            msg = banRemove + "is NOT on the banned users list"
        else:
            sqltables.session.delete(query)
            sqltables.session.commit()
            msg = banRemove + " has been removed from the banned users list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})


# Checks to make sure token is valid and for a bot
def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_webex_get(apiurl + "/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.ciscospark.com/apps.html "
                  "URL and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName", "")
            bot_email = test_auth.get("emails", "")[0]
    else:
        print("'bearer' variable is empty! \n"
              "You are missing your BOT's access token!!")
        sys.exit()
    # Provided token does not match up to bot account that ends in "webex.bot"
    if "@webex.bot" not in bot_email:
        print("You have provided an invalid token which does not relate to a Bot Account")
        sys.exit()
    else:
        app.run(host='localhost', port=5000)


if __name__ == "__main__":
    main()
