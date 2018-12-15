import dotenv
import json
import os

from pyspark import SparkContext
from pyspark.streaming import StreamingContext

# load environment variables
dotenv.load_dotenv(dotenv_path='./.env', verbose=True)
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

def sampling(rdd):
    return rdd.sample(False, 0.5, 1)

def get_text_tweet(tweet):
    json_tweet = json.loads(tweet)
    tweet_data = ''

    if ("extended_tweet" in json_tweet):
        tweet_data = json_tweet["extended_tweet"]["full_text"]
    else:
        tweet_data = json_tweet["text"]
    
    tweet_data = re.sub(r"#(\w+)", "", tweet_data)
    tweet_data = re.sub(r"@(\w+)", "", tweet_data)
    tweet_data = re.sub(" +", " ", tweet_data)

    return stemmer.stem(tweet_data).lower()

if __name__ == "__main__":
    # create Spark context
    spark_context = SparkContext("local[3]", "TwitterWords")
    spark_context.setLogLevel("ERROR")
    # spark_context.setCheckpointDir("./checkpoint")

    # create streaming object
    streaming_context = StreamingContext(spark_context, 5)
    stream_object = streaming_context.socketTextStream(HOST, PORT)
    
    lines = stream_object.map(lambda line: get_text_tweet(line))
    # pairs = words.map(lambda word: (word, 1))
    # wordCounts = pairs.reduceByKey(lambda x, y: x + y)

    lines.pprint()
    
    # sampled_stream = stream_object.transform(sampling)

    # parsed = sampled_stream.map(lambda v: json.loads(v[1]))
    # parsed.count().map(lambda x:'Tweets in this batch: %s' % x).pprint()

    # start stream processing
    streaming_context.start()

    # wait stream processing or wait until timeout
    streaming_context.awaitTermination()
    # streaming_context.awaitTerminationOrTimeout(15)
