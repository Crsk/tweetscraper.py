import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as bs
import pymongo
from pymongo import MongoClient
import time
import sys

user = None
desiredTweets = None
driver = None
url = None

# MongoDB initialization
try:
    client = MongoClient('localhost', 27017)
    db = client.tuits
    collection = db.tuits
except:
    print("Error al inicializar base de datos")

# webdriver initialization
try:
    driver = webdriver.Chrome()
    driver.wait = WebDriverWait(driver, 5)
    base_url = 'http://twitter.com/'
    user = input("Who to scrape (username): ")
    #user = sys.argv[1]
    url = base_url + user
except:
    print("Error al inicializar scraper")

try:
    #desiredTweets = int(sys.argv[2])
    desiredTweets = int(input("Number of desired tweets to scrape: "))
except:
    print("La cantidad de tweets debe ser numérica, intenta denuevo...")

# gets structured tweets data
def getTweetsData(page_source):
    soup = bs(page_source,'lxml')
    tweets = []
    for li in soup.find_all("li", class_='js-stream-item'):

        # Not a tweet
        if 'data-item-id' not in li.attrs:
            continue
        else:
            tweet = {
                'tweet_id': li['data-item-id'],
                'text': None,
                'user_id': None,
                'user_screen_name': None,
                'user_name': None,
                'created_at': None,
                'retweets': 0,
                'likes': 0,
                'replies': 0
            }

            # Tweet Text
            text_p = li.find("p", class_="tweet-text")
            if text_p is not None:
                tweet['text'] = text_p.get_text()

            # Tweet User ID, User Screen Name, User Name
            user_details_div = li.find("div", class_="tweet")
            if user_details_div is not None:
                tweet['user_id'] = user_details_div['data-user-id']
                tweet['user_screen_name'] = user_details_div['data-screen-name']
                tweet['user_name'] = user_details_div['data-name']

            # Tweet date
            date_span = li.find("span", class_="_timestamp")
            if date_span is not None:
                tweet['created_at'] = float(date_span['data-time-ms'])

            # Tweet Retweets
            retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if retweet_span is not None and len(retweet_span) > 0:
                tweet['retweets'] = int(retweet_span[0]['data-tweet-stat-count'])

            # Tweet Likes
            like_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if like_span is not None and len(like_span) > 0:
                tweet['likes'] = int(like_span[0]['data-tweet-stat-count'])

            # Tweet Replies
            reply_span = li.select("span.ProfileTweet-action--reply > span.ProfileTweet-actionCount")
            if reply_span is not None and len(reply_span) > 0:
                tweet['replies'] = int(reply_span[0]['data-tweet-stat-count'])

            tweets.append(tweet)
    return tweets

# gets unstructured tweets data
def getPageSource(user, desiredTweets, url):
    driver.get(url)
    time.sleep(1)
    body = driver.find_element_by_tag_name('body')

    # scroll page based on desired Tweets
    for x in range(int(desiredTweets * 0.9)):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.2)

    # extract and return the html
    return driver.page_source

# inserts all desired tweets to MongoDB
def saveTweets(tweets):
    uploadedTweets = 0
    i = 1
    for tweet in tweets:
        if uploadedTweets < int(desiredTweets):
            print('')
            retweeted = False
            if (tweet['user_screen_name'] != user):
                retweeted = True
            tweet = {
                'text': tweet['text'],
                'created_at': tweet['created_at'],
                'retweet_count': tweet['retweets'],
                'screen_name': tweet['user_screen_name'],
                'retweeted': retweeted
            }
            db.tuits.insert_one(tweet).inserted_id
            print(i)
            print(tweet['text'])
            i = i + 1
            uploadedTweets = uploadedTweets + 1

# closes the web browser
def closeDriver(driver):
    driver.close()
    return

pageSource = getPageSource(user, desiredTweets, url)
tweetsData = getTweetsData(pageSource)
saveTweets(tweetsData)
closeDriver(driver)