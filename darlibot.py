from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from scrape import find_episode as find_episode_helper
from datetime import datetime

import os
import sys
import logging
import json
import time

BOT_COUNT = 2
db_filename = 'db.json'

def start(bot, update):
    reply_str = "Hello World!"
    reply_str += str(update.effective_chat.id)
    update.message.reply_text(reply_str)

def watched(bot, update):
    reply_str = ''
    chat_id = str(update.effective_chat.id) # Cast to a string to avoid weirdness with checking its presence in db later

    # Safely add new chat ID to database if it doesn't exist
    if chat_id not in db:
        db[chat_id] = []
    watched_users = db[chat_id]

    # Find out who called /watched, and add them to the watched users list if they aren't in
    who_watched = update.message.from_user.username
    if who_watched not in watched_users:
        watched_users.append(who_watched)
        with open(db_filename, 'w') as dbfile:
            json.dump(db, dbfile)
        reply_str += "{} has now watched the newest episode.\n".format(who_watched)

    # Return a list of users who have watched
    reply_str += "Users who have watched the newest episode:\n"
    for name in watched_users:
        reply_str += "{}\n".format(name)

    # Return a message if all the users in the channel have watched
    if len(watched_users) >= bot.get_chat_members_count(chat_id) - BOT_COUNT:
        reply_str += "\nAll users have watched the newest episode!"

    update.message.reply_text(reply_str)

def find_episode(bot, job):
    last_find_date = datetime.fromtimestamp(db["last_found_date"])
    timediff = datetime.now() - last_find_date

    # Search for newest episode only if it's been more than 6 days since the last episode was found.
    if timediff.days >= 6:
        # Get None or a magnet uri
        magnet_link = find_episode_helper("Darling", "http://horriblesubs.info/rss.php?res=1080")
        # Found newest episode!
        if magnet_link is not None:
            db["last_found_date"] = time.mktime(datetime.now().timetuple())
            with open(db_filename, 'w') as dbfile:
                json.dump(db, dbfile)
            # Send update to chats, and reset their watched users list
            for chat_id in db:
                if chat_id != 'last_found_date':
                    db[chat_id] = []
                    bot.send_message(chat_id, text="HorribleSubs has uploaded the newest episode! Magnet link here: {}".format(magnet_link))

# MAIN PROGRAM
if "DARLIBOT_KEY" in os.environ:
    u = Updater(os.environ.get("DARLIBOT_KEY"))
    j = u.job_queue
else:
    sys.exit("Telegram Bot API key not in DARLIBOT_KEY environment variable")

dbstr = open(db_filename, 'r').read()
db_raw = json.loads(dbstr)
db = dict(db_raw)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

find_episode_job = j.run_repeating(find_episode, interval=300, first=10)

u.dispatcher.add_handler(CommandHandler('start', start))
u.dispatcher.add_handler(CommandHandler('watched', watched))
u.start_polling()
u.idle()
