import dotenv
import json
import re
import os

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from pyspark import SparkContext
from pyspark.mllib.fpm import FPGrowth
from pyspark.streaming import StreamingContext

# load environment variables
dotenv.load_dotenv(dotenv_path='./.env', verbose=True)
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

stopwords = set(stopwords.words("english"))
stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

filter_words = ["trade", "wars", "wars"]

# sampling function
def sampling(rdd):
    return rdd.sample(False, 0.5, 1)

# remove @, #, link, unicode char from tweet
def get_clean_tweet(tweet):
    json_tweet = json.loads(tweet)
    tweet_data = ''

    if ("extended_tweet" in json_tweet):
        tweet_data = json_tweet["extended_tweet"]["full_text"]
    else:
        tweet_data = json_tweet["text"]
    
    tweet_data = re.sub(r"#(\w+)", "", tweet_data)
    tweet_data = re.sub(r"@(\w+)", "", tweet_data)
    tweet_data = re.sub(r"https?:\/\/.*[\r\n]*", "", tweet_data)
    tweet_data = re.sub(" +", " ", tweet_data)
    tweet_data = tweet_data.encode('ascii', 'ignore')

    if ("retweet_count" in json_tweet):
        if tweet_data[:2] == "RT":
            tweet_data = tweet_data[5:]

    return tweet_data

# stem words in tweet
def get_stemmed_tweet(tweet):
    words = []

    tweet = tweet.lower()
    tokens = tokenizer.tokenize(tweet)
    for word in tokens:
        if word not in stopwords and word != '':
            words.append(stemmer.stem(word))
    
    return " ".join(words)

# get distinct words in tweet and remove filter words
# this function is used for itemset counting
def get_distinct_words(tweet):
    words = []

    for word in tweet.split(" "):
        if word not in words and word not in filter_words:
            words.append(word)
    
    return words

if __name__ == "__main__":
    # create Spark context
    spark_context = SparkContext("local[2]", "TwitterWords")
    spark_context.setLogLevel("ERROR")

    # create streaming object
    streaming_context = StreamingContext(spark_context, 15)
    stream_object = streaming_context.socketTextStream(HOST, PORT)
    
    # clean tweets
    lines = stream_object.map(lambda line: get_clean_tweet(line))
    lines.pprint(5)
    
    # stem tweets
    stemmed_lines = lines.map(lambda line: get_stemmed_tweet(line))
    stemmed_lines.pprint(5)

    # store to file for itemset counting
    stemmed_lines.repartition(1).saveAsTextFiles("./tweet_words/result")

    # create words from tweets
    words = stemmed_lines.flatMap(lambda line: line.split(" "))
    words.pprint(5)
    
    # count distict words
    pairs = words.map(lambda word: (word, 1))
    wordCounts = pairs.reduceByKey(lambda x, y: x + y)
    wordCounts = wordCounts.transform(lambda rdd: rdd.sortBy(lambda y: -y[1]))
    wordCounts.pprint(5)

    # start stream processing
    streaming_context.start()

    # wait stream processing then stop
    streaming_context.awaitTermination(65)
    streaming_context.stop(stopSparkContext=False)

    # read stored tweets
    data = spark_context.textFile("tweet_words/result-*/part-*")
    transactions = data.map(lambda line: get_distinct_words(line))
    
    # count itemsets
    model = FPGrowth.train(transactions, minSupport=0.025, numPartitions=10)
    result = model.freqItemsets().collect()
    for fi in result:
        print(fi)
