#!/usr/bin/env python
# Module     : SysTrayIcon.py
# Synopsis   : Windows System tray icon.
# Programmer : Simon Brunning - simon@brunningonline.net
# Date       : 11 April 2005
# Notes      : Based on (i.e. ripped off from) Mark Hammond's
#              win32gui_taskbar.py and win32gui_menu.py demos from PyWin32
'''TODO

For now, the demo at the bottom shows how to use it...'''

import os
import sys
import win32api
import win32con
import win32gui_struct
try:
	import winxpgui as win32gui
except ImportError:
	import win32gui

import os.path
import __init__

class SysTrayIcon(object):
	'''TODO'''
	QUIT = 'QUIT'
	SPECIAL_ACTIONS = [QUIT]

	FIRST_ID = 1023

	def __init__(self,
			icon,
			hover_text,
			menu_options,
			on_quit=None,
			default_menu_index=None,
			window_class_name=None,
			call_on_startup=None
			):

		self.icon = icon
		self.hover_text = hover_text
		self.on_quit = on_quit

		menu_options = menu_options + [('Quit', None, self.QUIT)]
		self._next_action_id = self.FIRST_ID
		self.menu_actions_by_id = set()
		self.menu_options = self._add_ids_to_menu_options(list(menu_options))
		self.menu_actions_by_id = dict(self.menu_actions_by_id)
		del self._next_action_id


		self.default_menu_index = (default_menu_index or 0)
		self.window_class_name = window_class_name or "SysTrayIconPy"

		message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
				   win32con.WM_DESTROY: self.destroy,
				   win32con.WM_COMMAND: self.command,
				   win32con.WM_USER+20 : self.notify,}
		if self.on_quit:
			message_map[win32con.WM_QUERYENDSESSION] = self.on_quit
		# Register the Window class.
		window_class = win32gui.WNDCLASS()
		hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
		window_class.lpszClassName = self.window_class_name
		window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
		window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
		window_class.hbrBackground = win32con.COLOR_WINDOW
		window_class.lpfnWndProc = message_map # could also specify a wndproc.
		classAtom = win32gui.RegisterClass(window_class)
		# Create the Window.
		style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
		self.hwnd = win32gui.CreateWindow(classAtom,
										  self.window_class_name,
										  style,
										  0,
										  0,
										  win32con.CW_USEDEFAULT,
										  win32con.CW_USEDEFAULT,
										  0,
										  0,
										  hinst,
										  None)
		win32gui.UpdateWindow(self.hwnd)
		self.notify_id = None
		self.refresh_icon()

		if call_on_startup is not None:
			call_on_startup(self)
		win32gui.PumpMessages()

	def _add_ids_to_menu_options(self, menu_options):
		result = []
		for menu_option in menu_options:
			option_text, option_icon, option_action = menu_option
			if callable(option_action) or option_action in self.SPECIAL_ACTIONS or option_text=="-":
				self.menu_actions_by_id.add((self._next_action_id, option_action))
				result.append(menu_option + (self._next_action_id,))
			elif non_string_iterable(option_action):
				result.append((option_text,
							   option_icon,
							   self._add_ids_to_menu_options(option_action),
							   self._next_action_id))
			else:
				print 'Unknown item', option_text, option_icon, option_action
			self._next_action_id += 1
		return result

	def refresh_icon(self, recreate=False):
		# Try and find a custom icon
		hinst = win32gui.GetModuleHandle(None)
		if isinstance(self.icon, str):
			if os.path.isfile(self.icon):
				icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
				hicon = win32gui.LoadImage(hinst,
					self.icon,
					win32con.IMAGE_ICON,
					0,
					0,
					icon_flags)
			else:
				hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
		else:
			hinst = win32api.GetModuleHandle(None)
			hicon = win32gui.LoadIcon(hinst, int(self.icon))

		if not self.notify_id or recreate:
			message = win32gui.NIM_ADD
		else:
			message = win32gui.NIM_MODIFY
		self.notify_id = (self.hwnd,
						  0,
						  win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
						  win32con.WM_USER+20,
						  hicon,
						  self.hover_text)
		try:
			win32gui.Shell_NotifyIcon(message, self.notify_id)
		except: # just catch strange error
			pass

	def set_icon(self, filename, hover_text=None):
		if hover_text is not None:
			self.hover_text = hover_text
		self.icon = filename
		self.refresh_icon()

	def set_hover_text(self, hover_text):
		self.hover_text = hover_text
		self.refresh_icon()

	def restart(self, hwnd, msg, wparam, lparam):
		self.refresh_icon(recreate=True)

	def destroy(self, hwnd, msg, wparam, lparam):
		if self.on_quit:
			self.on_quit(self)
		nid = (self.hwnd, 0)
		win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
		win32gui.PostQuitMessage(0) # Terminate the app.

	def notify(self, hwnd, msg, wparam, lparam):
		if lparam==win32con.WM_LBUTTONDBLCLK:
			self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
		elif lparam==win32con.WM_RBUTTONUP:
			self.show_menu()
		elif lparam==win32con.WM_LBUTTONUP:
			pass
		return True

	def show_menu(self):
		menu = win32gui.CreatePopupMenu()
		self.create_menu(menu, self.menu_options)
		#win32gui.SetMenuDefaultItem(menu, 1000, 0)

		pos = win32gui.GetCursorPos()
		# See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
		win32gui.SetForegroundWindow(self.hwnd)
		win32gui.TrackPopupMenu(menu,
								win32con.TPM_LEFTALIGN,
								pos[0],
								pos[1],
								0,
								self.hwnd,
								None)
		win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

	def create_menu(self, menu, menu_options):
		for option_text, option_icon, option_action, option_id in menu_options[::-1]:
			if option_icon: # has icon
				if not callable(option_icon):
					option_icon = self.prep_menu_icon(option_icon)
			if option_text == "-": # separator
				win32gui.InsertMenu(menu, 0, win32con.MF_BYPOSITION, win32con.MF_SEPARATOR, None)
			elif option_id in self.menu_actions_by_id: # normal item
				checked = False
				if callable(option_icon): # checkbox item
					checked = option_icon()
					option_icon = None # no icon
				if checked:
					item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text, fState=win32con.MFS_CHECKED, wID=option_id)
				else:
					item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text, hbmpItem=option_icon, wID=option_id)
				win32gui.InsertMenuItem(menu, 0, 1, item)
			else: # submenu
				submenu = win32gui.CreatePopupMenu()
				self.create_menu(submenu, option_action)
				item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text, hbmpItem=option_icon, hSubMenu=submenu)
				win32gui.InsertMenuItem(menu, 0, 1, item)

	def prep_menu_icon(self, icon):
		assert os.path.exists(icon)

		# First load the icon.
		ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
		ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
		hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

		hdcBitmap = win32gui.CreateCompatibleDC(0)
		hdcScreen = win32gui.GetDC(0)
		hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
		hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
		# Fill the background.
		brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
		win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
		# unclear if brush needs to be feed.  Best clue I can find is:
		# "GetSysColorBrush returns a cached brush instead of allocating a new
		# one." - implies no DeleteObject
		# draw the icon
		win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
		win32gui.SelectObject(hdcBitmap, hbmOld)
		win32gui.DeleteDC(hdcBitmap)

		return hbm

	def command(self, hwnd, msg, wparam, lparam):
		id = win32gui.LOWORD(wparam)
		self.execute_menu_option(id)

	def execute_menu_option(self, id):
		menu_action = self.menu_actions_by_id[id]
		if menu_action == self.QUIT:
			win32gui.DestroyWindow(self.hwnd)
		else:
			menu_action(self)

def non_string_iterable(obj):
	try:
		iter(obj)
	except TypeError:
		return False
	else:
		return not isinstance(obj, basestring)

def password_dialog():
	def line(n):
		return 9+24*n
	template = [
		["pynetkey %s" % __init__.version, (200, 200, 156, line(4)), -2134376256, None, (8, 'MS Sans Serif')],
		[130, "This program was not made by IT and is not supported by IT! -jantod@gmail.com", -1, (7, line(0), 150, 30), 1342177280, 0],
		[130, 'Username:', -1, (7, line(1), 43, 10), 1342177280, 0],
		[129, '', 1000, (59, line(1)-2, 59, 14), 1350631552, 0],
		[130, 'Password:', -1, (7, line(2), 43, 10), 1342177280, 0],
		[129, '', 1001, (59, line(2)-2, 60, 15), 1350631552|win32con.ES_PASSWORD, 0],
		[128, 'OK', 1, (59, line(3), 50, 14), 1342242817, 0],
	]
	data = {}
	def OnCommand(hwnd, msg, wparam, lparam):
		id = win32api.LOWORD(wparam)
		if id in [win32con.IDOK]:
			data["username"] = win32gui.GetWindowText(win32gui.GetDlgItem(hwnd, 1000))
			data["password"] = win32gui.GetWindowText(win32gui.GetDlgItem(hwnd, 1001))
			win32gui.EndDialog(hwnd, id)
	def OnClose(hwnd, msg, wparam, lparam):
		id = win32api.LOWORD(wparam)
		win32gui.EndDialog(hwnd, id)
	message_map = {
			#~ win32con.WM_INITDIALOG: self.OnInitDialog,
			win32con.WM_CLOSE: OnClose,
			#~ win32con.WM_DESTROY: OnDestroy,
			win32con.WM_COMMAND: OnCommand,
		}
	win32gui.DialogBoxIndirect(0, template, 0, message_map)
	return data.get("username"), data.get("password")

class TrayIcon:
	def __init__(self):
		pass
	def construct(self, menu_options, startup, on_quit):
		SysTrayIcon("icons/orange.ico", "inetkey", menu_options, call_on_startup=startup, on_quit=on_quit, default_menu_index=0)

def gui_quit():
	pass

# Minimal self test. You'll need a bunch of ICO files in the icons directory in order for this to work...
if __name__ == '__main__':
	import itertools, glob, random
	#~ print prompt_username_password()
	icons = itertools.imap(os.path.abspath, itertools.cycle(sorted(glob.glob('icons\\*.ico'))))
	hover_text = "SysTrayIcon.py Demo"
	def hello(sysTrayIcon): print "Hello World."
	def simon(sysTrayIcon): print "Hello Simon."
	def switch_icon(sysTrayIcon):
		sysTrayIcon.icon = icons.next()
		sysTrayIcon.refresh_icon()
	def check():
		return random.choice([True, False])
	menu_options = [
		('Say Hello', icons.next(), hello),
		('Switch Icon', None, switch_icon),
		('-', None, None),
		('hello', icons.next(), hello),
		('checked?', check, hello),
		('-', None, None),
		('A sub-menu', icons.next(),
			(
			('Say Hello to Simon', icons.next(), simon),
				('Switch Icon', icons.next(), switch_icon),
			)
		)
	]
	def bye(sysTrayIcon): print 'Bye, then.'

	SysTrayIcon(icons.next(), hover_text, menu_options, on_quit=bye, default_menu_index=1)
