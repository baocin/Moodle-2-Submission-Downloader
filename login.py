#!/usr/bin/python2
#sadly mechanize isn't ported to python 3..
#import urllib2.request
import mechanize
import re
import requests
import os
from bs4 import BeautifulSoup

#~ def downloadFile(url, outputPath):
	#~ r = requests.get(url)
	#~ with open(outputPath, "wb") as code:
		#~ code.write(r.content.encode('utf-8'))

def dumpclean(obj):							#https://stackoverflow.com/questions/15785719/how-to-print-a-dictionary-line-by-line-in-python
    if type(obj) == dict:
        for k, v in obj.items():
            if hasattr(v, '__iter__'):
                print k
                dumpclean(v)
            else:
                print '%s : %s' % (k, v)
    elif type(obj) == list:
        for v in obj:
            if hasattr(v, '__iter__'):
                dumpclean(v)
            else:
                print v
    else:
        print obj

moodleLoginURL = "https://moodle2.uncc.edu/login/index.php"

br = mechanize.Browser()
page = br.open(moodleLoginURL)
#Get the form used by normal user to logon
br.select_form(nr=1)
#send login information
br.form.set_all_readonly(False)			#Allow all forms(really everything) to be written to
br.set_handle_robots(False)
br.form["username"] = raw_input("Enter your Moodle 2 Username: ");
#Select the form you want to use.
br.select_form(nr=1)
br.form["password"] = raw_input("Enter your Moodle 2 Password: ");
#submit form
response = br.submit()

html = response.read()

soup = BeautifulSoup(html)
soup.prettify()

courses = {}
for link in soup.find_all("a"):
	#Identify course links
	if re.search("course/view.php\?id=\d+",link.get('href')):
	#get linkText, year, semester, and course subject, section number and course code for each link, use it as the course's key in the dictionary
		linkText = link.get_text()
		year = re.search("20\d{2}",linkText)
		year = year.group() if year else -1
		course = re.search("([A-Z]{4})-?(\d{3,}L?)", linkText)
		courseNum = course.groups()[1] if course else -1
		courseSub = course.groups()[0] if course else -1
		semester = re.search("(Fall)|(Spring)", linkText)
		semester = semester.group() if semester else "Unknown"
		sectionNum = re.search("-(H?\d{2,3})-",linkText)
		sectionNum = sectionNum.groups()[0] if sectionNum  else -1
		key = (linkText, courseSub, courseNum, sectionNum, semester, year)
		#print key
		courses[key] = [link.get('href')]


#dumpclean(courses)

#go to each course link and get all assignments
for key in courses:
	print "Downloading : " + key[0]
	print "\t URL: " + courses[key][0]
	br.open(courses[key][0])				#open the course page
	print "\t Page Title: " + br.title()	#check if browser is on right page
	html = br.response().read()
	soup = BeautifulSoup(html)
	soup.prettify()
	for link in br.links():
		print "\t\t url: " + link.url
		isCourseResourceLink = re.compile("moodle2\.uncc\.edu/mod/resource/view\.php\?id=").search(link.url)	#Course resource (powerpoint/notes/syllabus)
		if isCourseResourceLink:
			print "\t\t\tisCourseResourceLink"
			#make hierarchy of "College" - year - semester - class
			path = "./College/" + key[5] + "/" + key[4] + "/" + key[0] + "/"
			if not os.path.exists(path): os.makedirs(path)		#make directories if they don't exist already
			print "\t\t\t downloading to: " + path + link.text.decode('utf-8')
			br.open(link.url)		#open the download link
			#find the direct link to the file     ex. https://moodle2.uncc.edu/pluginfile.php/792645/mod_resource/content/1/Course%20Information-Logic%20%20Algorithms%20-Spring%202014.docx
			#~ print br.response().read()
			#~ br._factory.is_html = True
			try:
				for l in br.links():
					isDirectLink = re.search("/mod_resource/content/", l.url)
					if isDirectLink:
						downloadPath = path + l.text.decode('utf-8')
						if not os.path.exists(downloadPath):
							br.retrieve(l.url, filename = downloadPath)		#download the file
			except mechanize._mechanize.BrowserStateError, e:			#direct link from main moodle course page, no subpage
				print e
				print "\t\t\tDirect Link detected"
				#~ print br.response().read()
				downloadPath = path + link.text.decode('utf-8')
				if not os.path.exists(downloadPath):
						br.retrieve(link.url, filename = downloadPath)		#download the file
						#warning - this file will lack filetype extension
				#~ exit()
			#br.back()
		#~ br.back()
		#if re.search(link.get_text()

