#import traceback
import sys
import settings
import peewee #against standards, but specified in peewee docs?
from peewee import * #against standards, but specified in peewee docs?
from random import randint
from twython import Twython
from datetime import date

db = MySQLDatabase(settings.dbname,
                    user=settings.dbuser,
                    passwd=settings.dbpasswd)
db.connect()

APP_KEY = settings.APP_KEY
APP_SECRET = settings.APP_SECRET

OAUTH_TOKEN = settings.OAUTH_TOKEN
OAUTH_TOKEN_SECRET = settings.OAUTH_TOKEN_SECRET

twitter = Twython(APP_KEY, APP_SECRET,
                  OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

lastTweet = 0

tweet_less_sn = settings.tweet_less_sn


class BaseModel(peewee.Model):
    class Meta:
        database = db


class exc(BaseModel):
    text = peewee.CharField()


class player(BaseModel):
    text = peewee.CharField()


class quip(BaseModel):
    text = peewee.CharField()


def new_row(table, userInput):
    """ add a new row to a table """
    newText = table(text=userInput)
    newText.save()


def get_last():
    """ Determine where the bot left off """

    global lastTweet
    stream = twitter.get_user_timeline(user_id=settings.bot, count=100)

    for tweet in stream:
        if (tweet['user']['id'] == settings.bot) :
            if (tweet['in_reply_to_status_id'] != None):
                lastTweet = int(tweet['in_reply_to_status_id'])
                print "The last tweet is " + str(lastTweet)
                break


def str_to_class(str):
    return getattr(sys.modules[__name__], str)


def simplify(replies, followers):
    """ cut down stream JSON, eliminate replies to just get commands """

    prunedTweets = []
    for tweet in replies:
        if (tweet['in_reply_to_status_id'] is None
                and int(tweet['id']) > lastTweet):
            prunedTweets.append([
            tweet['text'],
            tweet['id'],
            tweet['user']['screen_name'],
            tweet['user']['id'] in followers
            ])
    return prunedTweets


def intake(items):
    """ add new phrases from pruned selection """

    for tweet in reversed(items):
        text = tweet[0][tweet_less_sn:].split("+", 1)
        if tweet[0][tweet_less_sn:].strip().lower() == "hit me":
            continue
        elif tweet[3]:
            if (text[0].strip() in settings.commands):
                tableType = text[0].strip()
                userInput = text[1].strip()
                try:
                    new_row(str_to_class(tableType), userInput)
                    newtweet = ("@%s Cool, adding %s to the database." %
                                    (tweet[2], userInput))
                    newTweet = newTweet[:130]
                    twitter.update_status(status=newTweet,
                                        in_reply_to_status_id=int(tweet[1]))
                except:
                    #exc_type, exc_value, exc_traceback = sys.exc_info()
                    #traceback.print_exception(exc_type, exc_value,
                                                #exc_traceback)
                    newTweet = ("@" + tweet[2] + " It looks like" + text[1] +
                                " was already added. Try again?")

                    newTweet = ("@%s It looks like %s was already added. Try again?"
                                % (tweet[2], text[1]))
                    newTweet = newTweet[:130]
                    try:
                        twitter.update_status(status=newTweet,
                                        in_reply_to_status_id=int(tweet[1]))
                    except:
                        print "Duplicate status."
            elif (tweet[3] == False):
                if (tweet[0][tweet_less_sn:].strip().lower() == "hit me"):
                    pass
                elif (text[0].strip() in settings.commands):
                    try:
                        twitter.update_status(status= "@" + tweet[2] +
                            " Sorry, I'm not following you yet. Checking to" +
                            "see if I should. You'll hear back soon.",
                            in_reply_to_status_id=int(tweet[1]))
                        twitter.update_status(status=
                            "@DoHimJob should I follow @" + tweet[2]+" ?",
                            in_reply_to_status_id=int(tweet[1]))
                    except:
                        print "Duplicate status."


def generate():
    """ Generate a new jargon tweet """

    first = exc.select().order_by(fn.Rand()).limit(1).get()
    firstP = first.text
    second = player.select().order_by(fn.Rand()).limit(1).get()
    secondP = second.text
    third = quip.select().order_by(fn.Rand()).limit(1).get()
    thirdP = third.text
    newTweet = firstP + " " + secondP + " " + thirdP
    return newTweet


def on_demand(items):
    """ Use generate() to provide a new tweet for a
    user when they tweet 'hit me' """

    for tweet in reversed(items):
        text = tweet['text'][12:]
        if ((text[:6].strip().lower() == "hit me")
                and (int(tweet['id']) > lastTweet)):
            newJargon = generate()
            newTweet = "@" + tweet['user']['screen_name'] + " " + newJargon
            newTweet = newTweet[:139]
            twitter.update_status(status=newTweet,
                                    in_reply_to_status_id=int(tweet['id']))


def periodic():
    """ Periodically tweet out a jargon phrase using generate() """

    tweetCheck = randint(0,15)
    if (tweetCheck == 5):
        newTweet = generate()
        twitter.update_status(status=newTweet)


def administration(items):
    """ follow or reject new users who put in commands """
    for tweet in reversed(items):
        if (tweet['user']['id'] == 22884755):
            text = tweet['text'][10:].split(" ")
            if (text[1] == "approve"):
                twitter.create_friendship(screen_name=text[2])
                twitter.update_status(status="@"+ text[2] +
                    " Good news, you've been approved!" +
                    " Please retry any additions prior to this message again.")
            elif (text[1] == "reject"):
                twitter.update_status(status="@"+ text[2] +
                                " Sorry, I'm not going to add you right now.")


tweets = twitter.get_mentions_timeline()
get_last()
intake(simplify(twitter.get_mentions_timeline(),
                twitter.get_friends_ids()['ids']))
on_demand(tweets)
administration(tweets)
periodic()
