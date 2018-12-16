import dotenv
import os
import json
import socket
import tweepy

from pathlib import Path
from signal import signal, SIGPIPE, SIG_DFL
from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener

env_path = Path('.') / '.env'
dotenv.load_dotenv(dotenv_path='./.env', verbose=True)

CONSUMER_KEY = os.getenv("OAUTH_KEY")
CONSUMER_SECRET = os.getenv("OAUTH_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

filter_words = ["trade war", "trade wars", "tradewar", "#tradewar", "tradewars", "#tradewars"]

class TwitterListener(StreamListener):
    def __init__(self, conn):
        self.conn = conn

    def on_data(self, data):
        try:
            data = data.replace(r'\n', '')
            json_data = json.loads(data)
            if("text" in json_data):
                username = json_data["user"]["screen_name"]
                print((username, json.dumps(json_data["text"])))
                self.conn.send(data.encode())
        except:
            print("No Tweet")

    def on_error(self, status):
        if status == 420:
            print("Stream Disconnected")
            return False

def sendTwitterData(conn):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    api = tweepy.API(auth)
    stream = tweepy.Stream(auth = api.auth, listener=TwitterListener(conn))
    stream.filter(track=["trade"])
    # stream.filter(track=["trade war", "trade wars", "tradewar", "#tradewar", "tradewars", "#tradewars"])

if __name__ == "__main__":
    host = os.getenv("HOST")
    port = int(os.getenv("PORT"))

    s = socket.socket()
    s.bind((host, port))
    print("Listening on port:", str(port))

    s.listen(5)
    conn, addr = s.accept()
    print("Received request from:", str(addr))

    sendTwitterData(conn)
