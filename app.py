import sys
import gi
import os
import praw
import json
import keyring
import traceback

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from prune_members import PruneMembersPage
from purge_content import PurgeContentPage
from subreddit_trends import SubredditTrends
from user_overlap import UserOverlapPage
from login import login

DEV_MODE = False

class MainWindow(Adw.ApplicationWindow):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.set_default_size(800, 650)
		
		self.leaflet = Adw.Leaflet(can_navigate_back = True, height_request = 650, hexpand = True)
		self.lbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request = 250, vexpand = True)
		self.rbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, width_request = 500, vexpand = True)

		self.ltitle = Adw.WindowTitle(title = "ms4r")
		self.rtitle = Adw.WindowTitle(title = "Getting Started")

		self.lheader = Adw.HeaderBar(title_widget=self.ltitle, show_end_title_buttons = False)
		self.rheader = Adw.HeaderBar(title_widget=self.rtitle, hexpand = True)
		self.leaflet.bind_property("folded", self.lheader, "show-end-title-buttons")
		self.leaflet.bind_property("folded", self.rheader, "show-start-title-buttons")

		self.backbtn = Gtk.Button(icon_name="go-previous-symbolic", visible=False)
		self.backbtn.connect("clicked", self.on_back_clicked)
		self.rheader.pack_start(self.backbtn)

		self.stack = Gtk.Stack(vexpand = True)
		self.sidebar = Gtk.StackSidebar(stack = self.stack, vexpand = True)
		self.stack.connect("notify::visible-child", self.stack_page_changed)

		self.reddit = login()

		self.overlay1 = Adw.ToastOverlay()
		self.window1 = Gtk.ScrolledWindow()
		self.overlay1.set_child(self.window1)
		self.stack.add_titled(self.overlay1, "Getting Started", "Getting Started")
		if (self.reddit == None):
			self.login_prompt()
		else:
			self.user_info()

		self.lbox.append(self.lheader)
		self.lbox.append(self.sidebar)
		self.rbox.append(self.rheader)
		self.rbox.append(self.stack)

		self.leaflet.append(self.lbox)
		self.leaflet.append(self.rbox)
		self.leaflet.set_visible_child(self.rbox)
		self.set_content(self.leaflet)

	def on_back_clicked(self, *args, **kwargs):
		self.leaflet.set_visible_child(self.lbox)

	def stack_page_changed(self, *args, **kwargs):
		if (self.leaflet.get_folded()):
			self.leaflet.set_visible_child(self.rbox)
		self.rtitle.set_title(self.stack.get_visible_child_name())

	def load_full_stack(self):
		self.window2 = PruneMembersPage(self.reddit)
		self.stack.add_titled(self.window2, "Prune Members", "Prune Members")
		self.window3 = PurgeContentPage(self.reddit)
		self.stack.add_titled(self.window3, "Purge Content", "Purge Content")
		self.window4 = SubredditTrends(self.reddit)
		self.stack.add_titled(self.window4, "Subreddit Trends", "Subreddit Trends")
		self.window5 = UserOverlapPage(self.reddit)
		self.stack.add_titled(self.window5, "User Overlap", "User Overlap")

	def remove_full_stack(self):
		self.stack.remove(self.window2)
		self.stack.remove(self.window3)
		self.stack.remove(self.window4)
		self.stack.remove(self.window5)

	def login_prompt(self):
		self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.window1.set_child(self.box)

		self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=210, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.label1 = Gtk.Label(label = "Username: ")
		self.entry1 = Gtk.Entry(placeholder_text="Username")
		self.row1.append(self.label1)
		self.row1.append(self.entry1)
		self.box.append(self.row1)

		self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=215, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label2 = Gtk.Label(label = "Password: ")
		self.entry2 = Gtk.PasswordEntry(placeholder_text="Password")
		self.entry2.connect("notify::cursor-position", self.toggle_peek_icon)
		self.row2.append(self.label2)
		self.row2.append(self.entry2)
		self.box.append(self.row2)

		self.row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=222, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label3 = Gtk.Label(label = "Client ID: ")
		self.entry3 = Gtk.Entry(placeholder_text="Client ID")
		self.row3.append(self.label3)
		self.row3.append(self.entry3)
		self.box.append(self.row3)

		self.row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=190, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label4 = Gtk.Label(label = "Client Secret: ")
		self.entry4 = Gtk.PasswordEntry(placeholder_text="Client Secret")
		self.entry4.connect("notify::cursor-position", self.toggle_peek_icon)
		self.row4.append(self.label4)
		self.row4.append(self.entry4)
		self.box.append(self.row4)

		self.row5 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.button = Gtk.Button(label="Login")
		self.button.connect("clicked", self.on_login_clicked)
		self.row5.append(self.button)
		self.box.append(self.row5)

	def on_login_clicked(self, *args, **kwargs):
		self.reddit = praw.Reddit(
			username = self.entry1.get_text(), 
			password = self.entry2.get_text(), 
			client_id = self.entry3.get_text(), 
			client_secret = self.entry4.get_text(), 
			user_agent = "ms4r", 
			fetch = True
		)
		try:
			if (self.reddit.user.me() == None):
				toast = Adw.Toast(title="Invalid credentials.", timeout=5)
				self.overlay1.add_toast(toast)
				return
			if (len(self.reddit.user.me().moderated()) < 1):
				toast = Adw.Toast(title="Sorry, you need moderator permissions on a subreddit to use this app.", timeout=10)
				self.overlay1.add_toast(toast)
				return
		except:
			toast = Adw.Toast(title="Login failed.", timeout=5)
			self.overlay1.add_toast(toast)
		else:
			file = open("ms4r.conf", "w")
			data = {
				"username": self.entry1.get_text(),
				"client_id": self.entry3.get_text(),
				"subreddit": self.reddit.user.me().moderated()[0].display_name
			}
			json.dump(data, file)
			file.close()
			keyring.set_password("ms4r", self.entry1.get_text(), self.entry2.get_text())
			keyring.set_password("ms4r", self.entry3.get_text(), self.entry4.get_text())
			self.user_info()

	def toggle_peek_icon(self, *args, **kwargs):
		if (args[0].get_position() > 0):
			args[0].set_show_peek_icon(True)
		else:
			args[0].set_show_peek_icon(False)

	def user_info(self):
		self.leaflet.bind_property("folded", self.backbtn, "visible")
		self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
		self.window1.set_child(self.box)

		self.row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=115, margin_top=20, margin_bottom=10, margin_start=20, margin_end=20)
		self.label1 = Gtk.Label(label = "Logged in as u/" + self.reddit.user.me().name)
		self.row1.append(self.label1)
		self.button = Gtk.Button(label="Logout")
		self.button.connect("clicked", self.sign_out)
		self.row1.append(self.button)
		self.box.append(self.row1)

		self.row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=135, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20)
		self.label2 = Gtk.Label(label = "Home Subreddit: ")
		self.row2.append(self.label2)
		if not DEV_MODE:
			self.list = []
			subreddits = self.reddit.user.me().moderated()
			for sub in subreddits:
				self.list.append(sub.display_name)
			self.strlist = Gtk.StringList.new(self.list)
			file = open("ms4r.conf", "r+")
			data = json.load(file)
			try:
				self.dropdown = Gtk.DropDown(model=self.strlist, selected=self.list.index(data["subreddit"]))
			except:
				self.dropdown = Gtk.DropDown(model=self.strlist)
				newdata = {
					"username": data["username"],
					"client_id": data["client_id"],
					"subreddit": self.list[0]
				}
				file.seek(0)
				json.dump(newdata, file)
			self.dropdown.connect("notify::selected-item", self.on_subreddit_changed)
			self.dropdown.set_size_request(200, 15)
			file.close()
			self.row2.append(self.dropdown)
		else:
			file = open("ms4r.conf", "r")
			data = json.load(file)
			self.label2b = Gtk.Label(label = data["subreddit"])
			file.close()
			self.label2b.set_size_request(200, 15)
			self.label2b.set_xalign(1)
			self.row2.append(self.label2b)

		self.box.append(self.row2)
		self.load_full_stack()

	def on_subreddit_changed(self, *args, **kwargs):
		index = self.dropdown.get_selected()
		file = open("ms4r.conf", "r+")
		data = json.load(file)
		newdata = {
			"username": data["username"],
			"client_id": data["client_id"],
			"subreddit": self.list[index]
		}
		file.seek(0)
		json.dump(newdata, file)
		file.close()

	def sign_out(self, *args, **kwargs):
		file = open("ms4r.conf", "r")
		data = json.load(file)
		keyring.delete_password("ms4r", data["username"])
		keyring.delete_password("ms4r", data["client_id"])
		file.close()
		os.remove("ms4r.conf")
		self.login_prompt()
		self.remove_full_stack()

class MyApp(Adw.Application):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.connect('activate', self.on_activate)

	def on_activate(self, app):
		try:
			self.win = MainWindow(application=app)
			self.win.present()
		except Exception as e: 
			traceback.print_exc()
			exit()

app = MyApp(application_id="com.example.GtkApplication")
app.run(sys.argv)
