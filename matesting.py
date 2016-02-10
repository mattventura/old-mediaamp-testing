#!/usr/bin/python

# Canvas MediaAMP LTI automated tests

import selenium.webdriver
import netid 
import time
import unittest
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import random
import delay

courseurl = 'https://canvas.uw.edu/courses/792462/external_tools/14556'

# Given a list of webelements, return the first one that is actually visible 
# on the page. Throws an exception if none are visible. 
def getFirstVisible(i):
    for e in i:
        if e.is_displayed():
            return e
        
    else:
        raise Exception('Could not find a visible element in the list provided')

def filterToVisible(i):
    out = []
    for e in i:
        if e.is_displayed():
            out.append(i)
    return out

# Class for a video in the list of search results
class videoResult():
    def __init__(self, e):
        self.e = e
        self.title = e.find_element_by_class_name('media-title').text
        descs = e.find_elements_by_class_name('media-description')
        desc1 = descs[0].text
        # Sometimes the date fails for some reason
        try:
            timestr = ' '.join(desc1.split()[1:3])
            self.time = time.strptime(timestr, '%m/%d/%y %H:%M')
        except:
            self.time = None
        try:
            self.uploader = desc1.split()[4]
        except:
            self.uploader = None
        
        self.desc = descs[1].text
        
        self.keywords = []
        
        for a in e.find_elements_by_class_name('media-keyword'):
            self.keywords.append(a.text)

    def __str__(self):
        return('Video "%s"' %self.title)

    def __repr__(self):
        return('<%s, name "%s">' %(str(self.__class__), self.title))

    def __eq__(self, other):
        return(self.title == other.title and self.desc == other.desc and self.keywords == other.keywords and self.uploader == other.uploader)

    # Use video.editButton to get the edit button. 
    # video.editButton.click() will open the edit dialog. 
    @property
    def editButton(self):
        return(self.e.find_element_by_class_name('media-edit'))
        
    def __bool__(self):
        return True

# Class for a fake video result. Mainly useful for when you want to compare
# search results to some expected result. 
class fakeVideoResult(videoResult):
    def __init__(self, title = '', desc = '', kw = [], uploader = None):
        self.title = title
        self.desc = desc
        self.keywords = kw
        self.uploader = uploader

    @property
    def editButton(self):
        return None

class matesting(unittest.TestCase):

    # Easy driver switching
    driverfunc = selenium.webdriver.Firefox
    driverargs = ()
    
    # Setup: Enable long test messages, enable unlimited length messages,
    # set up Firefox driver, do netid login, and switch to the actual
    # content frame. 
    def setUp(self):
        self.videosUploaded = False
        self.longMessage = True
        self.maxDiff = None
        self.driver = self.driverfunc(*self.driverargs)
        self.driver.maximize_window()
        netid.prelogin(self.driver)
        delay.afterlogin()
        self.driver.get(courseurl)
        self.canvasLogin()
        self.switchToContentFrame()
        delay.frameswitch()

    # If a video was uploaded in a test, the test should 
    # set videosEuploaded to true, so that the tearDown func
    # can delete any videos left by the test. 
    def tearDown(self):
        if self.videosUploaded:
            self.driver.get(courseurl)
            self.switchToContentFrame()
            delay.frameswitch()
            l = self.listVideoResults()
            for v in l:
                if 'deleteme' in v.title:
                    v.editButton.click()
                    delay.edit()
                    self.clickDeleteButton()
                    delay.delete()
                    self.confirmDelete()
                    delay.delete()
        self.driver.close()
        pass

    # Handle the canvas login screen
    def canvasLogin(self):
        e = self.driver.find_element_by_css_selector('button#login')
        e.click()
        delay.aftercanvaslogin()

    
    # Switch into the actual content frame
    # Also close the "Greetings beta user" popup
    def switchToContentFrame(self):
        delay.beforeframeswitch()
        self.driver.switch_to.frame('tool_content')
        delay.beforegreeting()
        e = getFirstVisible(self.driver.find_elements_by_css_selector('button.btn.btn-default'))
        e.click()
        delay.closegreeting()

    # Make sure there's no problems enumerating videos
    def test_video_list(self):
        l = self.listVideoResults()
        #print(l)

    # Test the upload popup
    def test_create_popup(self):
        self.clickUploadButton()
        delay.uploadbutton()
        self.clickPopupXButton()
        delay.xbutton()
        
    # Test the edit popup, including pressing the delete button (but cancelling)
    def test_edit_popup(self):
        l = self.listVideoResults()
        video = l[0]
        video.editButton.click()
        time.sleep(2)
        self.clickDeleteButton()
        time.sleep(2)
        self.cancelDelete()
        time.sleep(2)
        self.clickCloseButton()
        time.sleep(2)

    # Test a very simple search
    def test_simple_search(self):
        self.focusSearchBox()
        self.typeInSearch('asdf' + Keys.RETURN)
        delay.search()
        self.assertTrue(self.checkForVideo(title = 'Sample Media'))

    # Test various search capabilities
    # Currently broken
    #@unittest.expectedFailure
    def test_search_multi_1(self):
        self.focusSearchBox()
        self.typeInSearch('video' + Keys.RETURN)
        delay.search()
        self.searchFilterTitle()
        self.assertTrue(self.checkForVideo(title = 'Test media 1 videos'))
        self.searchFilterDesc()
        self.assertTrue(self.checkForVideo(title = 'Test media 2'))
        self.searchFilterKW()
        self.assertTrue(self.checkForVideo(title = 'Test media 3'))
        self.searchFilterAll()
        self.chooseSearchSort('Title')
        self.checkTitleSort(False)
        self.chooseSearchSort('Title')
        self.checkTitleSort(True)
        self.chooseSearchSort('Upload date')
        self.checkDateSort(False)
        self.chooseSearchSort('Upload date')
        self.checkDateSort(True)

    # Test a multi-word search
    def test_search_multi_2(self):
        self.focusSearchBox()
        self.typeInSearch('series1 videos' + Keys.RETURN)
        delay.search()
        l = self.listVideoResults()
        self.assertEqual(len(l), 3)
        #self.searchFilterTitle()
        #l = self.listVideoResults()
        #self.assertEqual(len(l), 0)

    # Make sure a blank title is rejected when editing
    def test_reject_blank_title(self):
        self.focusSearchBox()
        self.typeInSearch('sample' + Keys.RETURN)
        delay.search()
        l = self.listVideoResults()
        v = l[0]
        e = v.editButton
        e.click()
        delay.edit()
        # Unfinished
        # Clear title field
        # Try to submit
        # Check for error message
        self.enterTitle('')
        self.clickSubmitButton()
        delay.editsubmit()
        try:
            self.driver.find_element_by_css_selector('span.mediaCreateErrors')
        except NoSuchElementException:
            self.fail('Could not find blank title error')

    # Test editing, make sure changes are actually saved
    def test_edit_video(self):
        self.focusSearchBox()
        self.typeInSearch('zxcvbnm' + Keys.RETURN)
        randoms = (str(random.randint(1000, 9999)), str(random.randint(1000, 9999)), str(random.randint(1000, 9999)))
        delay.search()
        l = self.listVideoResults()
        v = l[0]
        v.editButton.click()
        delay.edit()
        self.enterTitle('zxcvbnm ' + randoms[0])
        self.enterDesc(randoms[1])
        self.enterKW(str(randoms[2]))
        self.clickSubmitButton()
        delay.editsubmit()
        self.reloadPage()


        delay.refresh()

        expectedVideo = fakeVideoResult('zxcvbnm ' + randoms[0], randoms[1], [randoms[2]], 'lisatest')

        #self.typeInSearch(randoms[0] + Keys.ENTER)
        self.typeInSearch('zxcvbnm' + Keys.ENTER)
        delay.search()
        self.searchFilterTitle()
        delay.search()
        self.assertEqual(self.listVideoResults(), [expectedVideo])

        # Can't do these because the search tags take a bit of time to update. 

        #self.typeInSearch(randoms[1] + Keys.ENTER)
        #self.typeInSearch('zxcvbnm' + Keys.ENTER)
        #time.sleep(1)
        ##self.searchFilterDesc()
        #time.sleep(1)
        #self.assertEqual(self.listVideoResults(), [expectedVideo])

        #self.typeInSearch(randoms[2] + Keys.ENTER)
        #self.typeInSearch('zxcvbnm' + Keys.ENTER)
        ##time.sleep(1)
        #self.searchFilterKW()
        #time.sleep(1)
        #self.assertEqual(self.listVideoResults(), [expectedVideo])
        

    # Test uploading of a single video
    def test_video_upload(self):
        self.clickUploadButton()
        delay.uploadbutton()
        self.addFile('/home/mattventura/MediaAMP/deletemeplease.MOV')
        #self.addFile('./deletemeplease.MOV')
        delay.addfile()
        self.clickUploadSubmitButton()
        self.videosUploaded = True
        delay.uploadsubmit()
        #self.waitForUploads()
        self.waitForUploads2()
        delay.afterupload()
        self.validatePagination()
        self.reloadPage()
        delay.refresh()
        
        ev = fakeVideoResult('deletemeplease.MOV', uploader = 'woodkin')

        l = self.listVideoResults()
        v = l[0]
        self.assertEqual(ev, v)

        v.editButton.click()    
        delay.edit()
        self.clickDeleteButton()
        delay.delete()
        self.confirmDelete()
        delay.delete()
        self.validatePagination()



    # Test uploading of multiple videos
    def test_video_upload_multi(self):
        self.clickUploadButton()
        delay.uploadbutton()
        self.addFile('/home/mattventura/MediaAMP/deletemeplease.MOV')
        delay.addfile()
        self.addFile('/home/mattventura/MediaAMP/alsodeleteme.MOV')
        delay.addfile()
        self.clickUploadSubmitButton()
        self.videosUploaded = True
        delay.uploadsubmit()
        #self.waitForUploads()
        self.waitForUploads2()
        delay.afterupload()
        self.validatePagination()
        self.reloadPage()
        delay.refresh()
        
        evs = [
            fakeVideoResult('deletemeplease.MOV', uploader = 'woodkin'), 
            fakeVideoResult('alsodeleteme.MOV', uploader = 'woodkin')
        ]

        l = self.listVideoResults()
        todelete = []
        failed = False
        for ev in evs:
            if ev in l:
                todelete.append(l[l.index(ev)])
            else:
                failed = True

        if failed:
            self.fail('Could not find an expected video after uploading')

        for v in todelete:
            v.editButton.click()    
            delay.edit()
            self.clickDeleteButton()
            delay.delete()
            self.confirmDelete()
            delay.delete()

        self.validatePagination()

        time.sleep(1)
            
        

        
    # Gets the current video list and makes sure they're sorted by title
    def checkTitleSort(self, reverse = False):
        l = self.listVideoResults()
        sl = sorted(l, key = lambda v: v.title, reverse = reverse)
        self.assertEqual(l, sl, 'Video list did not sort correctly')

    # Gets the current video list and makes sure they're sorted by date
    def checkDateSort(self, reverse = False):
        l = self.listVideoResults()
        sl = sorted(l, key = lambda v: v.time, reverse = reverse)
        self.assertEqual(l, sl, 'Video list did not sort by date correctly')

    # Focus the search box
    def focusSearchBox(self):
        e = self.driver.find_element_by_name('query')
        e.click()
    
    # Manually click the magnifying glass
    # I don't think this is ever used, all the tests just press enter
    def clickSearchButton(self):
        e = self.driver.find_element_by_id('media-search-icon')
        e.click()

    # Type things in search. This will NOT press enter for you, 
    # your search string has to be "whatever" + Keys.ENTER
    def typeInSearch(self, searchTerms):
        e = self.driver.find_element_by_name('query')
        e.send_keys(searchTerms)

    # Change search filter to all fields
    def searchFilterAll(self):
        self.chooseSearchFilter('All')

    # Change search filter to title
    def searchFilterTitle(self):
        self.chooseSearchFilter('Title')

    # Change search filter to title
    def searchFilterDesc(self):
        self.chooseSearchFilter('Description')

    # Change search filter to title
    def searchFilterKW(self):
        self.chooseSearchFilter('Keywords')

    # This is the function that actually changes the search filter.
    # Special logic is required for 'Title' because the 'Sort by Title' link
    # comes before the 'Show matches in Title' link.  
    def chooseSearchFilter(self, sfilter):
        if sfilter == 'Title':
            e = self.driver.find_elements_by_link_text('Title')[1]
        else:
            e = self.driver.find_element_by_link_text(sfilter)
        e.click()
        delay.searchfilter()

    # Change search sort. Just call this with the exact link text,
    # e.g. 'Title', 'Upload date'
    def chooseSearchSort(self, sortby):
        e = self.driver.find_elements_by_link_text(sortby)[0]
        e.click()
        delay.searchsort()

    # Return a list of videoResult objects corresponding to the videos 
    # currently on the screen. 
    def listVideoResults(self):
        es = self.driver.find_elements_by_class_name('media-item')
        #es = self.driver.find_elements_by_css_selector('li.media-item')
        videos = []
        for e in es:
            if e.is_displayed():
                video = videoResult(e)
                videos.append(video)
        return(videos)

    def listPageButtons(self):
        navContainer = self.driver.find_element_by_xpath('//ul[@id="media-current-page"]')
        buttons = navContainer.find_elements_by_xpath('./li/a[@class="current-page-button"]')
        return(buttons)

    def numPages(self):
        buttons = self.listPageButtons()
        #print buttons
        return(len(buttons) - 2)

    def curItemsPerPage(self):
        e = self.driver.find_element_by_xpath('//div[@class="dropdown"]//span[@id="items-per-page"]')
        return int(e.text)
        

    # Checks for the presense of a video with particular properties in the 
    # video results. If 'exclusive' is true, then that video must be the only
    # video in the list. 
    def checkForVideo(self, title = None, desc = None, keywords = None, exclusive = False):
        l = self.listVideoResults()
        if exclusive and len(l) > 1:
            return(False)
        for video in l:
            if title and (title != video.title):
                continue
            if desc and (desc != video.desc):
                continue
            if keywords:
                for k in keywords:
                    if k not in video.keywords:
                        continue
            break
        return video

    # Click the 'X' button in the search box. 
    def clickXButton(self):
        e = self.driver.find_element_by_class_name('glyphicon-remove')
        e.click()

    # Click upload button
    def clickUploadButton(self):
        e = self.driver.find_element_by_class_name('import-media')
        e.click()

    # Click the X button on a popup
    def clickPopupXButton(self):
        getFirstVisible(self.driver.find_elements_by_css_selector('button.close')).click()

    # Click the close button on the edit dialog. 
    def clickCloseButton(self):
        getFirstVisible(self.driver.find_elements_by_xpath('//button[text()="Close"]')).click()

    # Click the submit button on a dialog. 
    def clickSubmitButton(self):
        e = self.driver.find_element_by_xpath('//button[@type="submit"]')
        e.click()

    # Click the delete button on the edit dialog
    def clickDeleteButton(self):
        e = self.driver.find_element_by_id('media-delete')
        e.click()

    # Say 'No' to the delete confirmation
    def cancelDelete(self):
        e = self.driver.find_element_by_xpath('//a[@class="cancel"]')
        e.click()
    # Say 'Yes' to the delete confirmation
    def confirmDelete(self):
        e = self.driver.find_element_by_xpath('//a[@class="delete"]')
        e.click()

    # Fill in a title on the edit dialog. By default, clears the old title out. 
    def enterTitle(self, title, clear = True):
        e = self.driver.find_element_by_xpath('//textarea[@name="title"]')
        if clear:
            e.clear()
        e.send_keys(title)

    # Same as above, but for description. 
    def enterDesc(self, desc, clear = True):
        e = self.driver.find_element_by_xpath('//textarea[@name="description"]')
        if clear:
            e.clear()
        e.send_keys(desc)

    # Same as above, but for keywords. 
    def enterKW(self, kws, clear = True):
        e = self.driver.find_element_by_xpath('//textarea[@name="keywords"]')
        if clear:
            e.clear()
        e.send_keys(kws)

    # Same as above, but for admins. 
    def enterAdmins(self, admins, clear = True):
        e = self.driver.find_element_by_xpath('//textarea[@name="pl1$netID"]')
        if clear:
            e.clear()
        e.send_keys(admins)

    # Reload the entire page and get back in the content frame. 
    def reloadPage(self):
        self.driver.refresh()
        time.sleep(1)
        self.switchToContentFrame()
    
    # Choose a file to upload
    def addFile(self, path):
        e = self.driver.find_element_by_css_selector('input#input-file')
        e.send_keys(path)

    # Remove a file from the upload list
    def removeFile(self, index):
        e = self.driver.find_elements_by_css_selector('span.mediaUploadRemove')[index]
        e.click()

    # Wait for uploads to finish
    def waitForUploads(self):
        timeout = 0600
        maxt = time.time() + timeout
        while time.time() < maxt:
            time.sleep(1)
            for e in self.driver.find_elements_by_css_selector('div.mediaFileProgress'):
                if 'Uploading...' in e.text:
                    break
            else:
                break
        else:
            self.fail('File upload took too long')

    # Since the upload dialog now closes automatically when all
    # files have finished uploading, we now just have to wait
    # for the upload dialog to disappear. 
    # We're looking for the header on the upload dialog since it's 
    # easier to identify. 
    # Technically, the old one still works, but the new one is cleaner. 
    def waitForUploads2(self):
        timeout = 600
        maxt = time.time() + timeout
        while time.time() < maxt:
            time.sleep(1)
            el = self.driver.find_elements_by_css_selector('div.upload-header')
            el = filterToVisible(el)
            if len(el) == 0:
                break

        else:
            self.fail('File upload took too long')

    # Click the button to start uploading selected files
    def clickUploadSubmitButton(self):
        self.driver.find_element_by_css_selector('button#upload-select').click()

    def validatePagination(self):
        l = len(self.listVideoResults())
        n = self.curItemsPerPage() # Expected number of items per page
        p = self.numPages()
        #print(l, n, p)
        if l == n:
            pass
        elif l < n and p > 1:
            self.fail('Not enough videos on page despite there being multiple pages')
        elif l > n:
            self.fail('Too many videos on page')
        

class matesting_chrome(matesting):
    driverfunc = selenium.webdriver.Chrome
    
    @unittest.skip('Uploading broken on Chrome')
    def test_video_upload(self):
        pass

    @unittest.skip('Uploading broken on Chrome')
    def test_video_upload_multi(self):
        pass

@unittest.skip('iWebDriver chokes on MediaAMP')
class matesting_ipad(matesting):
    driverfunc = selenium.webdriver.Remote
    driverargs = ('http://108.179.183.228:3001/wd/hub', selenium.webdriver.DesiredCapabilities.IPHONE)

    @unittest.skip('No uploading on iDevices')
    def test_video_upload(self):
        pass

    @unittest.skip('No uploading on iDevices')
    def test_video_upload_multi(self):
        pass



if __name__ == '__main__':
    unittest.main()
