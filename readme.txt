# ProfanityBot
WebEx Teams Profanity Bot

**Project Description:** \
Profanity Bot allows you to monitor language in a WebEx Teams room.  Words are set in a database and can be dynamically updated by
interacting with the BOT.  When a user in the room users a word on the profanity list for the room the BOT will reply with a message
to watch language.

**Release notes:** \
Version 4 (FUTURE RELEASE) - \
This version will support the removal of users from the room who use profanity three or more times.  
It will support the removal of user's messages which contain profanity.
The BOT will need to be run as a user account with the compliance role in order to remove messages and users from the room.

Version 3 (current version) - \
Updated with "blist" commands and a counter to keep track of how many times users have used profanity
Warns users how many times they have used profanity up to 3 (after 3 get same message)

Version 2 - \
Submitted for WebEx Professional Ambassador certification. \
This version allows use of the "plist" command and warns users when they use profanity

**How to use:** \
"plist" <command> allows you to manage the profanity word list \
"blist" <command> allows you to amnage the ban user list 

plist add <word> - add the specified word to the rooms profanity list \
plist remove <word> - remove the specified word from the rooms profanity list \
plist search <word> - search if the specified word is the rooms profanity list \
plist list - list all words in the rooms profanity list

blist add <email> - add the specified word to the rooms banned user list \
blist remove <email> - remove the specified user from the rooms banned user list \
blist search <email> - search if the specified user is the rooms banned user list \
blist list - list all users in the rooms profanity list
