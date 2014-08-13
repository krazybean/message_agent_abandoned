#!/usr/bin/env python
import gntp.notifier
'''
No purpose here other than creating a callable library for system notifications
'''

class message:
    def __init__(self, messagex):
	growl = gntp.notifier.GrowlNotifier(
            applicationName = "RSEvent Notification",
            notifications = ["New Updates","New Messages"],
            defaultNotifications = ["New Messages"],
	    )
        growl.register()
        growl.notify(
            noteType = "New Messages",
            title = "Status: Alert",
            description = "%s" % messagex,
            icon = "http://url/to/Alert-Icon-.png",
            sticky = False,
            priority = 1,
        )



