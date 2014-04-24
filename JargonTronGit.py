import peewee, traceback, sys, random
from peewee import *
from twython import Twython
from datetime import date

db = MySQLDatabase('XXX', user='XXX', passwd="XXX")
db.connect()

APP_KEY = 'XXX'
APP_SECRET = 'XXX'

OAUTH_TOKEN = 'XXX-XXX'
OAUTH_TOKEN_SECRET = 'XXX'

twitter = Twython(APP_KEY, APP_SECRET,
                  OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

lastTweet = 0

class exclamation(peewee.Model):
    text = peewee.CharField()

    class Meta:
        database = db

class player(peewee.Model):
    text = peewee.CharField()

    class Meta:
        database = db

class quip(peewee.Model):
    text = peewee.CharField()

    class Meta:
        database = db

def newRow(table, userInput):
    """ add a new row to a table """
    newText = table(text=userInput)
    newText.save()

def getLast():
    global lastTweet
    stream = twitter.get_home_timeline()
    for tweet in stream:
        if (tweet['user']['id'] == 2432961043) :
            lastTweet = tweet['in_reply_to_status_id']
            print "The last tweet is " + str(lastTweet)
            break

def strToClass(str):
    return getattr(sys.modules[__name__], str)

def prune(replies, followers):
    """ select only tweets from users the bot follows """

    prunedTweets = []

    for tweet in replies:
        if ((tweet['user']['id'] in followers) and (tweet['in_reply_to_status_id'] == None) and (int(tweet['id']) > int(lastTweet))):
            prunedTweets.append([
                tweet['text'],
                tweet['id'],
                tweet['user']['screen_name'],
                ])

    return prunedTweets

def intake(tweets):
    """ add new phrases from pruned selection """

    commands = ["player", "quip", "exclamation"]
    for tweet in reversed(tweets):

        text = tweet[0][12:].split("+", 1)
        if (text[0].lstrip().rstrip() in commands):
            tableType = text[0].lstrip().rstrip()
            userInput = text[1].lstrip().rstrip()
            try:
                newRow(strToClass(tableType), userInput)
                newTweet = "@" + tweet[2] + " Cool, adding " + userInput + " to the database."
                newTweet = newTweet[:130]
                twitter.update_status(status=newTweet, in_reply_to_status_id=int(tweet[1]))
            except:
                #exc_type, exc_value, exc_traceback = sys.exc_info()
                #traceback.print_exception(exc_type, exc_value, exc_traceback)
                newTweet = "@" + tweet[2] + " It looks like" + text[1] + " was already added. Try again?"
                newTweet = newTweet[:130]
                try:
                    twitter.update_status(status=newTweet, in_reply_to_status_id=int(tweet[1]))
                except:
                    print "Duplicate status."
        else:
            newTweet = "@" + tweet[2] + " Huh? Did you follow the format? Find it here: PLACEHOLDER."
            newTweet = newTweet[:130]
            try:
                twitter.update_status(status=newTweet, in_reply_to_status_id=int(tweet[1]))
            except:
                print "Duplicate status."

getLast()
intake(prune(twitter.get_mentions_timeline(), twitter.get_friends_ids()['ids']))
