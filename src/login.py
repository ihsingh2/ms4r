import os
import json
import praw
import keyring

def login():
	if (os.path.isfile("ms4r.conf")):
		file = open("ms4r.conf", "r")
		data = json.load(file)
		try:
			reddit = praw.Reddit(
				username = data["username"], 
				password = keyring.get_password("ms4r", data["username"]), 
				client_id = data["client_id"], 
				client_secret = keyring.get_password("ms4r", data["client_id"]), 
				user_agent = "ms4r",
				fetch = True
			)
			reddit.user.me().link_karma
			return reddit
		except Exception as e:
			print(e)
	return None
