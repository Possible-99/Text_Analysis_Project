from tweepy import API 
from tweepy import Cursor
import tweepy
from tweepy import OAuth2BearerHandler
from tweepy import Stream
from textblob import TextBlob
from tabulate import tabulate
 
import twitter_credentials

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re


# Getting our api objects, which contains the methods for accessing twitter data
class TwitterFetch():
    def __init__(self, twitter_user = None):
        self.auth = TwitterAuthenticator().authenticate()
        self.twitter_api = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_api(self):
        return self.twitter_api

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_api.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friends(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_api.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_api.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets


# Authenticating the credentials to the twitter api
class TwitterAuthenticator():

    def authenticate(self):
        auth = OAuth2BearerHandler(twitter_credentials.BEARER_TOKEN)
        return auth

# Processing tweets in real time.
class TwitterStream():
    def __init__(self):
        self.twitter_autenticator = TwitterAuthenticator()    

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list):
        #Connect to twitter streaming api
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate() 
        stream = Stream(auth, listener)

        # Filter data with some paramters
        stream.filter(track=hash_tag_list)


# Configuration of twitter streamer
class TwitterListener(tweepy.Stream):
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error %s" % str(e))
        return True
          
    def on_error(self, status):
        if status == 420:
            return False
        print(status)


# Preprocessing the string and getting the sentiment value.
class TweetAnalyzer():

    #Remove characters that we don't want
    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet):
        analysis = TextBlob(self.clean_tweet(tweet))
        
        if analysis.sentiment.polarity > 0:
            return 1
        elif analysis.sentiment.polarity == 0:
            return 0
        else:
            return -1

    # We give a dataframe format to our tweets.
    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data = [tweet.text for tweet in tweets], columns=['tweets'])

        df['id'] = np.array([tweet.id for tweet in tweets])
        df['length'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        df['platform'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df

 
if __name__ == '__main__':

    twitter_api = TwitterFetch()
    tweet_analyzer = TweetAnalyzer()

    api = twitter_api.get_twitter_api()

    #Modify this line for analyzing other twitter user(ej. : elonmusk)
    user_to_analyze = "elonmusk"

    tweets = api.user_timeline(screen_name= user_to_analyze, count = 200)

    df = tweet_analyzer.tweets_to_data_frame(tweets)
    df['sentiment'] = np.array([tweet_analyzer.analyze_sentiment(tweet) for tweet in df['tweets']])

    print(tabulate(df, headers = 'keys', tablefmt = 'pretty'))
