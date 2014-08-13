#!/usr/bin/env python
import pynotify
'''
No purpose here other than creating a callable library for system notifications
'''

class message:
    def __init__(self, messagex):
	pynotify.init('EventCall')
	m = pynotify.Notification("RSEvent Notification", "%s" % messagex)
	m.show()
