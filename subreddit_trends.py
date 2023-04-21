import gi
import json
import datetime
import threading
import numpy as np
import pandas as pd
from matplotlib.backends.backend_gtk4agg import (FigureCanvasGTK4Agg as FigureCanvas)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class SubredditTrends(Gtk.ScrolledWindow):

	def __init__(self, reddit, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.reddit = reddit
		self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.set_child(self.box)

		self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.label1 = Gtk.Label(label = "Parameter: ")
		self.label1.set_size_request(175, 15)
		self.label1.set_xalign(0)
		self.strlist = Gtk.StringList.new(['Number of Active Users', 'Number of Submissions', 'Number of Comments', 'Submission Scores', 'Type of Content', 'Link Flair Usage', 'Edit Frequency'])
		self.dropdown = Gtk.DropDown(model = self.strlist)
		self.dropdown.connect("notify::selected-item", self.on_dropdown_select)
		self.dropdown.set_size_request(225, 15)
		self.spinner = Gtk.Spinner()
		self.row1.append(self.label1)
		self.row1.append(self.dropdown)
		self.row1.append(self.spinner)
		self.box.append(self.row1)

		self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=220, margin_top=10, margin_bottom=20, margin_start=20, margin_end=20)
		self.label2 = Gtk.Label(label = "Days to plot: ")
		self.adj2 = Gtk.Adjustment(lower=1, upper=30, step_increment=1, page_increment=5, value=7)
		self.spin2 = Gtk.SpinButton(adjustment=self.adj2, numeric=True)
		self.row2.append(self.label2)
		self.row2.append(self.spin2)
		self.box.append(self.row2)

		self.viewport = Gtk.Viewport()
		self.box.append(self.viewport)
		self.on_dropdown_select()

	def on_dropdown_select(self, *args, **kwargs):
		self.spinner.start()
		index = self.dropdown.get_selected()
		days = self.spin2.get_value()
		file = open("ms4r.conf", "r")
		data = json.load(file)
		home = data["subreddit"]
		file.close()

		if index == 0:
			thread = threading.Thread(target=self.active_users, args=[home, days])
		elif index == 1:
			thread = threading.Thread(target=self.submission_count, args=[home, days])
		elif index == 2:
			thread = threading.Thread(target=self.comment_count, args=[home, days])
		elif index == 3:
			thread = threading.Thread(target=self.submission_score, args=[home, days])
		elif index == 4:
			thread = threading.Thread(target=self.content_type, args=[home, days])
		elif index == 5:
			thread = threading.Thread(target=self.flair_usage, args=[home, days])
		else:
			thread = threading.Thread(target=self.edit_frequency, args=[home, days])
			
		thread.daemon = True
		thread.start()

	def on_plot_gen(self, canvas, retindex):
		if retindex == self.dropdown.get_selected():
			self.viewport.set_child(canvas)
			self.spinner.stop()

	def active_users(self, home, days):
		count = {}
		for item in self.reddit.subreddit(home).comments(limit = 999):
			try:
				author = item.author.name
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				if key in count:
					if author not in count[key]:
						count[key].append(author)
				else:
					if len(count) == days:
						break
					count[key] = [author]
			except:
				pass
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				author = item.author.name
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				if key in count:
					if author not in count[key]:
						count[key].append(author)
				else:
					break
			except:
				pass

		for key in count.keys():
			count[key] = len(count[key])

		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		ax.plot(list(count.keys()), list(count.values()))
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 0)

	def submission_count(self, home, days):
		count = {}
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				if key in count:
					count[key] += 1
				else:
					if len(count) == days:
						break
					count[key] = 1
			except Exception as e:
				print(e)

		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		ax.plot(list(count.keys()), list(count.values()))
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 1)

	def comment_count(self, home, days):
		count = {}
		for item in self.reddit.subreddit(home).comments(limit = 999):
			try:
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				if key in count:
					count[key] += 1
				else:
					if len(count) == days:
						break
					count[key] = 1
			except Exception as e:
				print(e)

		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		ax.plot(list(count.keys()), list(count.values()))
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 2)

	def submission_score(self, home, days):
		count = {}
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				if key in count:
					count[key][0] = max(count[key][0], item.score)
					count[key][1] = min(count[key][1], item.score)
					count[key][2] += item.score
					count[key][3] += 1
				else:
					if len(count) == days:
						break
					count[key] = [item.score, item.score, item.score, 1]
			except Exception as e: 
				print(e)

		vals = np.array(list(count.values()))
		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		ax.plot(list(count.keys()), vals[:, 0], label='max_score')
		ax.plot(list(count.keys()), vals[:, 1], label='min_score')
		ax.plot(list(count.keys()), vals[:, 2] / vals[:, 3], label='avg_score')
		ax.legend()
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 3)

	def content_type(self, home, days):
		count = {}
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				if key in count:
					if item.is_original_content:
						count[key][0] += 1
					if item.is_self:
						count[key][1] += 1
					if item.over_18:
						count[key][2] += 1
					if item.spoiler:
						count[key][3] += 1
				else:
					if len(count) == days:
						break
					lst = []
					if item.is_original_content:
						lst.append(1)
					else:
						lst.append(0)
					if item.is_self:
						lst.append(1)
					else:
						lst.append(0)
					if item.over_18:
						lst.append(1)
					else:
						lst.append(0)
					if item.spoiler:
						lst.append(1)
					else:
						lst.append(0)
					count[key] = lst
			except Exception as e:
				print(e)

		vals = np.array(list(count.values()))
		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		ax.plot(list(count.keys()), vals[:, 0], label = 'is_original_content')
		ax.plot(list(count.keys()), vals[:, 1], label = 'is_self')
		ax.plot(list(count.keys()), vals[:, 2], label = 'over_18')
		ax.plot(list(count.keys()), vals[:, 3], label = 'spoiler')
		ax.legend()
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 4)

	def flair_usage(self, home, days):
		count = pd.DataFrame(columns = ['None'])
		keys = []
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				date = datetime.datetime.fromtimestamp(item.created_utc).date()
				key = str(date.day) + '-' + str(date.month)
				flair = str(item.link_flair_text)
				if key in keys:
					i = keys.index(key)
					if flair not in count.columns:
						count[flair] = 0
					count.loc[i][flair] += 1
				else:
					i = len(count)
					if i == days:
						break
					keys.append(key)
					count.loc[i] = 0
					if flair not in count.columns:
						count[flair] = 0
					count.loc[i][flair] += 1
			except Exception as e:
				print(e)

		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		for flair in count.columns:
			ax.plot(keys, list(count[flair]), label = flair)
		ax.legend()
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 5)

	def edit_frequency(self, home, days):
		count = {}
		for item in self.reddit.subreddit(home).comments(limit = 999):
			try:
				if item.edited:
					date = datetime.datetime.fromtimestamp(item.created_utc).date()
					key = str(date.day) + '-' + str(date.month)
					if key in count:
						count[key] += 1
					else:
						if len(count) == days:
							break
						count[key] = 1
			except Exception as e:
				print(e)
		for item in self.reddit.subreddit(home).new(limit = 999):
			try:
				if item.edited:
					date = datetime.datetime.fromtimestamp(item.created_utc).date()
					key = str(date.day) + '-' + str(date.month)
					if key in count:
						count[key] += 1
					else:
						break
			except Exception as e:
				print(e)

		plt.style.use('dark_background')
		fig = Figure(figsize = (5, 4), dpi = 100)
		ax = fig.add_subplot()
		ax.plot(list(count.keys()), list(count.values()))
		canvas = FigureCanvas(fig)

		GLib.idle_add(self.on_plot_gen, canvas, 6)
