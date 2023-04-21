import gi
import json
import praw
import time
import threading

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class PurgeContentPage(Gtk.ScrolledWindow):

	def __init__(self, reddit, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.reddit = reddit
		self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.set_child(self.box)

		self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=160, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.label1 = Gtk.Label(label = "Posted in the last () days: ")
		self.adj1 = Gtk.Adjustment(lower=0, upper=1500, step_increment=1, page_increment=30, value=0)
		self.spin1 = Gtk.SpinButton(adjustment=self.adj1, numeric=True)
		self.row1.append(self.label1)
		self.row1.append(self.spin1)
		self.box.append(self.row1)

		self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=225, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label2 = Gtk.Label(label = "Posted by banned users: ")
		self.switch2 = Gtk.Switch()
		self.row2.append(self.label2)
		self.row2.append(self.switch2)
		self.box.append(self.row2)

		self.row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=130, margin_top=15, margin_bottom=10, margin_start=20, margin_end=20)
		self.label3a = Gtk.Label(label = "Word Blacklist:")
		self.label3b = Gtk.Label(label = "Domain Blacklist:")
		self.row3.append(self.label3a)
		self.row3.append(self.label3b)
		self.box.append(self.row3)

		self.row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.window4a = Gtk.ScrolledWindow()
		self.window4a.set_size_request(215, 240)
		self.tview4a = Gtk.TextView(top_margin=10, bottom_margin=10, left_margin=10, right_margin=10)
		self.window4a.set_child(self.tview4a)
		self.window4b = Gtk.ScrolledWindow()
		self.window4b.set_size_request(215, 240)
		self.tview4b = Gtk.TextView(top_margin=10, bottom_margin=10, left_margin=10, right_margin=10)
		self.window4b.set_child(self.tview4b)
		self.row4.append(self.window4a)
		self.row4.append(self.window4b)
		self.box.append(self.row4)

		self.row5 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.button5 = Gtk.Button(label="Purge")
		self.button5.connect("clicked", self.start_purge)
		self.row5.append(self.button5)
		self.spinner = Gtk.Spinner()
		self.row5.append(self.spinner)
		self.label5 = Gtk.Label()
		self.box.append(self.row5)

	def start_purge(self, *args, **kwargs):
		self.spinner.start()
		self.label5.set_text("")
		buffer4a = self.tview4a.get_buffer()
		start4a, end4a = buffer4a.get_bounds()
		buffer4b = self.tview4b.get_buffer()
		start4b, end4b = buffer4b.get_bounds()
		file = open("ms4r.conf", "r")
		data = json.load(file)
		file.close()
		thread = threading.Thread(target = self.purge, args = [data["subreddit"], int(self.spin1.get_value()), int(self.switch2.get_state()), buffer4a.get_text(start4a, end4a, False), buffer4b.get_text(start4b, end4b, False)])
		thread.daemon = True
		thread.start()

	def stop_purge(self, num):
		self.spinner.stop()
		if (num > 0):
			self.label6.set_text(str(num) + " items purged.")

	def purge(self, home, days, rmvban, wordbl, domainbl):
		wblacklist = wordbl.splitlines()
		wblacklist = list(filter(None, wblacklist))
		dblacklist = domainbl.splitlines()
		dblacklist = list(filter(None, dblacklist))

		count = 0
		rmvafter = time.time() - days*86400
		for item in self.reddit.subreddit(home).comments(limit = 999):
			try:
				if days != 0:
					if item.created_utc > rmvafter:
						item.mod.remove()
						count += 1
						continue
				if rmvban:
					if item.author != None:
						if item.author.name != "[deleted]":
							if any(self.reddit.subreddit(home).banned(item.author.name)):
								item.mod.remove()
								count += 1
								continue
				if any(word in item.body for word in wblacklist):
					item.mod.remove()
					count += 1
			except Exception as e:
				print(e)
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				if days != 0:
					if item.created_utc > rmvafter:
						item.mod.remove()
						count += 1
						continue
				if rmvban:
					if item.author != None:	
						if item.author.name != "[deleted]":
							if any(self.reddit.subreddit(home).banned(item.author.name)):
								item.mod.remove()
								count += 1
								continue
				if any(domain in item.url for domain in dblacklist):
					item.mod.remove()
					count += 1
					continue
				if any(word in item.title for word in wblacklist):
					item.mod.remove()
					count += 1
					continue
				if item.is_self:
					if any(word in item.selftext for word in wblacklist):
						item.mod.remove()
						count += 1
			except Exception as e:
				print(e)

		GLib.idle_add(self.stop_purge, count)
