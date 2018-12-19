from pprint import pprint
import requests
import json
import sys
import os
import sqltables
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
    # Check if message in contains profanity
    for word in matchList:
        query = sqltables.session.query(sqltables.Profanity).filter(
            and_(
                sqltables.Profanity.roomid == webhook['data']['roomId'],
                sqltables.Profanity.words == word
            )
        ).first()
        # If message does contain profanity..check if user is already on ban list
        if query is not None:
            bancheck = sqltables.session.query(sqltables.Banlist).filter(
                and_(
                    sqltables.Banlist.roomid == webhook['data']['roomId'],
                    sqltables.Banlist.user == webhook['data']['personEmail']
                )
            ).first()
            # If user is on ban list then increase the ban count by 1.  If user has a count of 3 or more then remove them from the room
            if bancheck is not None:
                bancheck.count += 1
                sqltables.session.commit()
                countcheck = sqltables.session.query(func.max(sqltables.Banlist.count)).scalar()
                if countcheck >= 3:
                    # send_webex_delete(apiurl + "/memberships/" + webhook['data']['membershipId'])
                    return webhook['data']['personEmail'] + " - Three strikes and you're out!!"
                elif countcheck == 2:
                    return webhook['data']['personEmail'] + " has two strikes"
            # If user is not on ban list then add them with next empid and with a count of 1
            else:
                lastempid = sqltables.session.query(func.max(sqltables.Banlist.empid)).scalar()
                empidnew = lastempid + 1
                newban = sqltables.Banlist(empid=empidnew,
                                           roomid=webhook['data']['roomId'],
                                           user=webhook['data']['personEmail'],
                                           count='1')
                sqltables.session.add(newban)
                sqltables.session.commit()
                return webhook['data']['personEmail'] + " has one strike"

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
            return addProfanity + " is already on the profanity list for this room"
        if msg != None:
            send_webex_post(apiurl + "/messages",
                            {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("plist search"):
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
            return "The word " + searchProfanity + " is NOT on the profanity list for this room"
        else:
            return searchProfanity + " is on the profanity list for this room"

    elif in_message.startswith("plist list"):
        msg = None
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Profanity).filter(
            sqltables.Profanity.roomid == webhook['data']['roomId'])
        for result in query:
            msg = result.words
            if msg != None:
                send_webex_post(apiurl + "/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("plist remove"):
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
            return removeProfanity + "is NOT on the profanity list"
        else:
            sqltables.session.delete(query)
            sqltables.session.commit()
            return removeProfanity + " has been removed from the profanity list for this room"

    elif in_message.startswith("blist add"):
        in_message = in_message.split()
        banAdd = in_message[-1]
        banAdd = banAdd.lower()
        webhook = request.get_json(silent=True)
        lastempid = sqltables.session.query(func.max(sqltables.Banlist.empid)).scalar()
        empidnew = lastempid + 1
        query = sqltables.session.query(sqltables.Banlist).filter(
            and_(
                sqltables.Banlist.roomid == webhook['data']['roomId'],
                sqltables.Banlist.user == banAdd
            )
        ).first()
        if query is None:
            newBan = sqltables.Banlist(empid=empidnew,
                                             roomid=webhook['data']['roomId'],
                                             user=banAdd,
                                             count='3')
            sqltables.session.add(newBan)
            sqltables.session.commit()
            return "The user " + banAdd + " was added to the banned users list for this room"
        else:
            return banAdd + " is already on the banned users list for this room"

    elif in_message.startswith("blist search"):
        in_message = in_message.split()
        banSearch = in_message[-1]
        banSearch = banSearch.lower()
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Banlist).filter(
            and_(
                sqltables.Banlist.roomid == webhook['data']['roomId'],
                sqltables.Banlist.user == banSearch
            )
        ).first()
        if query is None:
            return "The user " + banSearch + " is NOT on the banned users list for this room"
        else:
            return banSearch + " is on the banned users list for this room"

    elif in_message.startswith("blist list"):
        msg = None
        webhook = request.get_json(silent=True)
        query = sqltables.session.query(sqltables.Banlist).filter(sqltables.Banlist.roomid == webhook['data']['roomId'])
        for result in query:
            msg = result.user
            if msg != None:
                send_webex_post(apiurl + "/messages", {"roomId": webhook['data']['roomId'], "markdown": msg})

    elif in_message.startswith("blist remove"):
        in_message = in_message.split()
        userRemove = in_message[-1]
        userRemove = userRemove.lower()
        webhook = request.get_json(silent=True)
        banRemove = sqltables.session.query(sqltables.Banlist).filter(
            and_(
                sqltables.Banlist.roomid == webhook['data']['roomId'],
                sqltables.Banlist.user == userRemove
            )
        ).first()
        if banRemove is None:
            return userRemove + "is NOT on the banned users list"
        else:
            sqltables.session.delete(banRemove)
            sqltables.session.commit()
            return userRemove + " has been removed from the banned users list for this room"


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
    if "@webex.bot" in bot_email:
        print("You have provided an invalid token which does not relate to a Bot Account")
        sys.exit()
    else:
        app.run(host='localhost', port=5000)


if __name__ == "__main__":
    main()
