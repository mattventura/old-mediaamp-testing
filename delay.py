#!/usr/bin/python

# This file lets you delay by a certain amount of time by putting the name
# and the amount here, then accessing (not calling) delay.xxxxxxx

afterlogin = 3
aftercanvaslogin = 3.5
frameswitch = 1
uploadbutton = 2
xbutton = 2
search = 2.5
edit = 3
editsubmit = 2
refresh = 2.5
addfile = 1
uploadsubmit = 2
delete = 2
closegreeting = 1
beforegreeting = 3
beforeframeswitch = 5
searchfilter = 1
searchsort = 1.5
afterupload = 3

# Delay by an amount defined in delays
class delayer():
    def __init__(self, delayset):
        self.delayset = delayset

    def __getattr__(self, attr):
        return lambda: time.sleep(getattr(self.delayset, attr))

    def __dir__(self):
        return dir(self.delayset)
        

import time
import sys
delayobj = delayer(sys.modules[__name__])

sys.modules[__name__] = delayobj
