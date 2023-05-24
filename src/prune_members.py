import gi
import os
import json
import praw
import time
import datetime
import threading

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class PruneMembersPage(Gtk.ScrolledWindow):

	def __init__(self, reddit, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.reddit = reddit
		self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.set_child(self.box)

		self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=170, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.label1 = Gtk.Label(label = "Minimum Link Karma: ")
		self.adj1 = Gtk.Adjustment(lower=0, upper=50000, step_increment=50, page_increment=500, value=0)
		self.spin1 = Gtk.SpinButton(adjustment=self.adj1, numeric=True)
		self.row1.append(self.label1)
		self.row1.append(self.spin1)
		self.box.append(self.row1)

		self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=130, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label2 = Gtk.Label(label = "Minimum Comment Karma: ")
		self.adj2 = Gtk.Adjustment(lower=0, upper=10000, step_increment=50, page_increment=500, value=0)
		self.spin2 = Gtk.SpinButton(adjustment=self.adj2, numeric=True)
		self.row2.append(self.label2)
		self.row2.append(self.spin2)
		self.box.append(self.row2)

		self.row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=170, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label3 = Gtk.Label(label = "Minimum Account Age: ")
		self.adj3 = Gtk.Adjustment(lower=0, upper=1500, step_increment=30, page_increment=150, value=0)
		self.spin3 = Gtk.SpinButton(adjustment=self.adj3, numeric=True)
		self.row3.append(self.label3)
		self.row3.append(self.spin3)
		self.box.append(self.row3)

		self.row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=100, margin_top=15, margin_bottom=10, margin_start=20, margin_end=20)
		self.label4a = Gtk.Label(label = "Subreddit Blacklist:")
		self.label4b = Gtk.Label(label = "Word Blacklist:")
		self.row4.append(self.label4a)
		self.row4.append(self.label4b)
		self.box.append(self.row4)

		self.row5 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.window5a = Gtk.ScrolledWindow()
		self.window5a.set_size_request(215, 250)
		self.tview5a = Gtk.TextView(top_margin=10, bottom_margin=10, left_margin=10, right_margin=10)
		self.window5a.set_child(self.tview5a)
		self.window5b = Gtk.ScrolledWindow()
		self.window5b.set_size_request(215, 250)
		self.tview5b = Gtk.TextView(top_margin=10, bottom_margin=10, left_margin=10, right_margin=10)
		self.window5b.set_child(self.tview5b)
		self.row5.append(self.window5a)
		self.row5.append(self.window5b)
		self.box.append(self.row5)

		self.row6 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.button6 = Gtk.Button(label="Prune")
		self.button6.connect("clicked", self.start_prune)
		self.spinner = Gtk.Spinner()
		self.label6 = Gtk.Label()
		self.row6.append(self.button6)
		self.row6.append(self.spinner)
		self.row6.append(self.label6)
		self.box.append(self.row6)

	def start_prune(self, *args, **kwargs):
		self.spinner.start()
		self.label6.set_text("")
		buffer5a = self.tview5a.get_buffer()
		start5a, end5a = buffer5a.get_bounds()
		buffer5b = self.tview5b.get_buffer()
		start5b, end5b = buffer5b.get_bounds()
		file = open("ms4r.conf", "r")
		data = json.load(file)
		file.close()
		thread = threading.Thread(target = self.prune, args = [data["subreddit"], int(self.spin1.get_value()), int(self.spin2.get_value()), int(self.spin3.get_value()), buffer5a.get_text(start5a, end5a, False),	buffer5b.get_text(start5b, end5b, False)])
		thread.daemon = True
		thread.start()

	def stop_prune(self, num):
		self.spinner.stop()
		if (num > 0):
			self.label6.set_text(str(num) + " members pruned.")

	def prune(self, home, lklim, cklim, agelim, subbl, wordbl):
		folder = datetime.datetime.now().strftime("logs-%Y-%m-%d-%H-%M-%S")
		parent = os.path.dirname(__file__)
		path = os.path.realpath(os.path.join(parent,folder))
		os.mkdir(path)
		username_log = open(folder + "/username.txt", "w")
		prune_log = open(folder + "/prune.txt", "w")
		
		userlist = []
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				author = item.author.name
				if author not in userlist:
					if author != "[deleted]":
						userlist.append(author)
			except:
				continue
		for item in self.reddit.subreddit(home).comments(limit = 999):
			try:
				author = item.author.name
				if author not in userlist:
					if author != "[deleted]":
						userlist.append(author)
			except:
				continue
		for user in userlist:
			print(user, file = username_log)
		print("Username logs generated.")
		username_log.close()
		
		sblacklist = subbl.splitlines()
		sblacklist = list(filter(None, sblacklist))
		wblacklist = wordbl.splitlines()
		wblacklist = list(filter(None, wblacklist))

		banlist = []
		currtime = time.time()
		agelimsec = agelim * 86400
		for user in userlist:
			try:
				profile = self.reddit.redditor(user)
				if profile.link_karma < lklim:
					banlist.append(user)
					continue
				if profile.comment_karma < cklim:
					banlist.append(user)
					continue
				if (currtime - profile.created_utc) < agelimsec:
					banlist.append(user)
					continue

				count = 0
				history = list(profile.new(limit = 100))
				threshold = min(1, int(len(history)/10))
				for item in history:
					try:
						if count >= threshold:
							banlist.append(user)
							break
						if item.subreddit.display_name in sblacklist:
							count += 1
						if isinstance(item, praw.models.Comment):
							if any(word in item.body for word in wblacklist):
								count += 1
						elif isinstance(item, praw.models.Submission):
							if any(word in item.title for word in wblacklist):
								count += 1
							if item.is_self:
								if any(word in item.selftext for word in wblacklist):
									count += 1
					except Exception as e:
						print(e)
			except:
				continue

		for user in banlist:
			print(user, file = prune_log)
		print("Prune logs generated.")
		prune_log.close()

		count = 0
		for user in banlist:
			try:
				if any(self.reddit.subreddit(home).banned(user)):
					pass
				else:
					self.reddit.subreddit(home).banned.add(user, ban_reason = "", ban_message = "", note = "pruned by ms4r")
					count += 1
			except Exception as e:
				print(e)

		GLib.idle_add(self.stop_prune, count)
