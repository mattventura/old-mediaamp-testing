#!/usr/bin/python

from private import testnetid

from selenium.webdriver.common.keys import Keys
import selenium.common.exceptions

# Function to login with netid
def weblogin(d, user = testnetid[0], pwd = testnetid[1]):

    userid = user
    password = pwd

    try:
        userbox = d.find_element_by_id('weblogin_netid')
        userbox.send_keys(userid)
    except selenium.common.exceptions.NoSuchElementException:
        e = d.find_element_by_xpath('//li[@class="login-static-name"]/span')
        if (e.text == userid):
            pass
        else:
            raise Exception('The browser has a pre-filled netID which does not match the one provided')
    passbox = d.find_element_by_id('weblogin_password')

    passbox.send_keys(password)
    
    passbox.submit()

    #submitbtn = d.find_element_by_xpath('//input[@name="submit"]')
    #submitbtn.click()


def prelogin(d):
    d.get('https://weblogin.washington.edu/')
    weblogin(d)



