import gi
import os
import json
import threading
import datetime

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class UserOverlapPage(Gtk.ScrolledWindow):

	def __init__(self, reddit, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.reddit = reddit
		self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.set_child(self.box)

		self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=87, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.label1 = Gtk.Label(label = "Items to scan in the home subreddit: ")
		self.adj1 = Gtk.Adjustment(lower=1, upper=999, step_increment=10, page_increment=25, value=100)
		self.spin1 = Gtk.SpinButton(adjustment=self.adj1, numeric=True)
		self.row1.append(self.label1)
		self.row1.append(self.spin1)
		self.box.append(self.row1)

		self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=184, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label2 = Gtk.Label(label = "Items to scan per user: ")
		self.adj2 = Gtk.Adjustment(lower=1, upper=100, step_increment=10, page_increment=25, value=25)
		self.spin2 = Gtk.SpinButton(adjustment=self.adj2, numeric=True)
		self.row2.append(self.label2)
		self.row2.append(self.spin2)
		self.box.append(self.row2)

		self.row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label3 = Gtk.Label(label = "Minimum member count for consideration: ")
		self.adj3 = Gtk.Adjustment(lower=1, upper=9999, step_increment=25, page_increment=250, value=100)
		self.spin3 = Gtk.SpinButton(adjustment=self.adj3, numeric=True)
		self.row3.append(self.label3)
		self.row3.append(self.spin3)
		self.box.append(self.row3)

		self.row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.button4 = Gtk.Button(label="Scan")
		self.button4.connect("clicked", self.start_scan)
		self.row4.append(self.button4)
		self.spinner = Gtk.Spinner()
		self.row4.append(self.spinner)
		self.box.append(self.row4)

		self.row5 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_top=20, margin_bottom=10, margin_start=10, margin_end=10)
		self.label5a = Gtk.Label()
		self.label5a.set_markup('<span foreground="red">Overlap List</span>')
		self.label5a.set_size_request(225, 15)
		self.label5b = Gtk.Label()
		self.label5b.set_markup('<span foreground="red">Participation Probability</span>')
		self.label5b.set_size_request(225, 15)
		self.label5a.set_visible(False)
		self.label5b.set_visible(False)
		self.row5.append(self.label5a)
		self.row5.append(self.label5b)
		self.box.append(self.row5)

		self.row6 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, margin_top=5, margin_bottom=10, margin_start=10, margin_end=10)
		self.window6a = Gtk.ScrolledWindow()
		self.window6a.set_size_request(225, 310)
		self.viewport6a = Gtk.Viewport()
		self.label6a = Gtk.Label()
		self.viewport6a.set_child(self.label6a)
		self.window6a.set_child(self.viewport6a)
		self.window6b = Gtk.ScrolledWindow()
		self.window6b.set_size_request(225, 310)
		self.viewport6b = Gtk.Viewport()
		self.label6b = Gtk.Label()
		self.viewport6b.set_child(self.label6b)
		self.window6b.set_child(self.viewport6b)
		self.row6.append(self.window6a)
		self.row6.append(self.window6b)
		self.box.append(self.row6)

	def start_scan(self, *args, **kwargs):
		self.spinner.start()
		file = open("ms4r.conf", "r")
		data = json.load(file)
		file.close()
		thread = threading.Thread(target=self.overlap, args=(data["subreddit"], self.spin1.get_value(), self.spin2.get_value(), self.spin3.get_value()))
		thread.daemon = True
		thread.start()

	def stop_scan(self, overlap, prob):
		self.spinner.stop()
		self.label5a.set_visible(True)
		self.label5b.set_visible(True)
		self.label6a.set_text(overlap)
		self.label6b.set_text(prob)

	def overlap(self, home, lim, ulim, filter):
		folder = datetime.datetime.now().strftime("logs-%Y-%m-%d-%H-%M-%S")
		parent = os.path.dirname(__file__)
		path = os.path.realpath(os.path.join(parent,folder))
		os.mkdir(path)
		username_log = open(folder+"/username.txt", "w")
		overlap_log = open(folder+"/overlap.txt", "w")
		prob_log = open(folder+"/probability.txt", "w")

		userlist = []
		for item in self.reddit.subreddit(home).new(limit = lim/10):
			try:
				author = item.author.name
				if author not in userlist:
					if author != "[deleted]":
						userlist.append(author)
			except:
				continue
		for item in self.reddit.subreddit(home).comments(limit = lim):
			try:
				author = item.author.name
				if author not in userlist:
					if author != "[deleted]":
						userlist.append(author)
			except:
				continue
		for author in userlist:
			print(author, file = username_log)
		print("Username logs generated.")
		username_log.close()

		overlap = {}
		for user in userlist:
			try:
				profile = {}
				for item in self.reddit.redditor(user).new(limit = ulim):
					if item.subreddit.display_name.startswith("u_") or (item.subreddit.display_name == home):
						continue
					profile[item.subreddit.display_name] = 1
				for sub in profile:
					if sub in overlap:
						overlap[sub] += 1
					else:
						overlap[sub] = 1
			except:
				continue
		i = 0
		overlap_string = ""
		overlap_sorted = {k: v for k, v in sorted(overlap.items(), key = lambda item: item[1], reverse = True)}
		for key, value in overlap_sorted.items():
			if i < 15:
				i = i + 1
				overlap_string = overlap_string + key + ' ' + str(value) + '\n'
			print(key, value, file = overlap_log)
		print("Overlap logs generated.")
		overlap_log.close()
		
		prob = {}
		scaling_factor = 100000000/(ulim*len(userlist))
		for sub in overlap:
			try:
				subcount = self.reddit.subreddit(sub).subscribers
				prob[sub] = round(overlap[sub]*scaling_factor/subcount, 2)
			except:
				prob[sub] = 0
		i = 0
		prob_string = ""
		prob_sorted = {k: v for k, v in sorted(prob.items(), key = lambda item: item[1], reverse = True)}
		for key, value in prob_sorted.items():
			if i < 15:
				i = i + 1
				prob_string = prob_string + key + ' ' + str(value) + '\n'
			print(key, value, file = prob_log)
		print("Probability logs generated.")
		prob_log.close()
		
		GLib.idle_add(self.stop_scan, overlap_string, prob_string)
