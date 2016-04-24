#!/usr/bin/python3
import re
import requests
import os
from bs4 import BeautifulSoup
import json
import youtube_dl

moodleBaseURL = "https://moodle.uncc.edu/"
moodleLoginURL = "https://moodle.uncc.edu/login/index.php"
moodleNavURL = "https://moodle.uncc.edu/lib/ajax/getnavbranch.php"
moodleAssignmentURL = "https://moodle.uncc.edu/mod/assign/index.php"
moodleResourceURL = "https://moodle.uncc.edu/course/resources.php"

# moodleBaseURL = "https://moodle2.uncc.edu/"
# moodleLoginURL = "https://moodle2.uncc.edu/login/index.php"
# moodleNavURL = "https://moodle2.uncc.edu/lib/ajax/getnavbranch.php"
# moodleAssignmentURL = "https://moodle2.uncc.edu/mod/assign/index.php"
# moodleResourceURL = "https://moodle2.uncc.edu/course/resources.php"
baseSavePath = os.curdir

s = requests.Session()
loginPayload = {'username': 'Your Username', 'password': 'Your Password'}
loginRequest = s.post(moodleLoginURL, data=loginPayload)

#Real request: {'elementid': 'expandable_branch_0_mycourses', 'type': '0', 'instance': '5', 'id': 'mycourses', 'sesskey': ''}
navPayload = {
    'elementid':'expandable_branch_0_mycourses',
    'id':'mycourses',
    'type':'0',
    'sesskey':'',   #Not needed apparently...
    'instance':'5',
}

semesterRequest = s.post(moodleNavURL, data=navPayload)
semesterJson = json.loads(semesterRequest.text)     #Read in json as python object

semesters = []
for semester in semesterJson['children']:
    print("Processing semester:", semester['name'])

    #Real Request: {'haschildren': True, 'type': 11, 'key': '34', 'title': '', 'hidden': False, 'expandable': '34', 'icon': {'component': 'moodle', 'title': '', 'alt': '', 'pix': 'i/navigationitem', 'classes': ['smallicon', 'navicon']}, 'id': 'expandable_branch_11_34', 'name': 'Spring 2016', 'class': 'type_unknown expandable_branch_11_34'}
    coursesPayload = {
        'elementid':semester['id'],
        'id':semester['key'],
        'type':semester['type'],
        'sesskey':'',   #Not needed apparently...
        'instance':'5',
    }

    coursesRequest = s.post(moodleNavURL, data=coursesPayload)
    coursesJson = json.loads(coursesRequest.text)     #Read in json as python object

    for course in coursesJson['children']:
        #{'name': 'HONR-3700-H04-Fall 2015-13111', 'link': 'https://moodle2.uncc.edu/course/view.php?id=80207', 'id': 'expandable_branch_20_80207', 'key': '80207', 'type': 20, 'icon': {'title': '', 'pix': 'i/navigationitem', 'alt': '', 'component': 'moodle', 'classes': ['smallicon', 'navicon']}, 'class': 'type_course expandable_branch_20_80207', 'title': 'HONR-3700-H04-Fall 2015-Honors College Topics', 'expandable': '80207', 'haschildren': False, 'hidden': False}
        print("\tProcessing course:", course['name'])
        #Go to that course's page

        coursePayload = {'id':course['key']}

        #Get all the submitted assignments for this course
        assignmentRequest = s.get(moodleAssignmentURL, params=coursePayload)
        soup = BeautifulSoup(assignmentRequest.text, "html.parser")
        soup.prettify()
        for link in soup.find_all('a', href=re.compile(".*assign/.*")):
            #print("Getting file:",link)# link['href'])
            submissionRequest = s.get(link['href'])
            #Get link associated with submitted files
            submissionSoup = BeautifulSoup(submissionRequest.text, "html.parser")
            submissionName = submissionSoup.find('h2').text
            print("\t\tSubmission Name:",submissionName)

            submissionLinks = submissionSoup.find_all('a', href=re.compile(".*submission_files/|mod_assign/.*"))
            submissionLinks.append(link)
            for fileLink in submissionLinks:
                print("\t\t\tDownloading file:", fileLink.text)
                savePath = baseSavePath + os.sep + semester['name'] + os.sep + course['name'] + os.sep + submissionName;
                try:
                    os.makedirs(savePath)
                except FileExistsError:
                    pass
                r = s.get(fileLink['href'], stream = True)
                with open(savePath + os.sep + fileLink.text, "wb") as file:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: # filter out keep-alive new chunks
                            file.write(chunk)
                        #file.write(r.content)

        #Get all the submitted assignments for this course
        resourceRequest = s.get(moodleResourceURL, params=coursePayload)
        soup = BeautifulSoup(resourceRequest.text, "html.parser")
        soup.prettify()
        for link in soup.find_all('a', href=re.compile(".*assign/.*")):
            #print("Getting file:",link)# link['href'])
            submissionRequest = s.get(link['href'])
            #Get link associated with submitted files
            resourceSoup = BeautifulSoup(resourceRequest.text, "html.parser")
            print("\t\tGetting Resources")

            resourceLinks = resourceSoup.find_all('a', href=re.compile(".*resource/|mod/url.*"))
            resourceLinks.append(link)
            for fileLink in resourceLinks:
                print("\t\t\tDownloading file:", fileLink.text)
                savePath = baseSavePath + os.sep + semester['name'] + os.sep + course['name'] + os.sep + 'Resources'
                try:
                    os.makedirs(savePath)
                except FileExistsError:
                    pass

                r = s.get(fileLink['href'])
                youtubeSoup =  BeautifulSoup(r.text, "html.parser")
                ydl = youtube_dl.YoutubeDL({        #https://github.com/rg3/youtube-dl/blob/master/youtube_dl/YoutubeDL.py#L121-L269
                    'quiet': True,
                    'ignoreerrors': True,
                    'outtmpl': savePath + os.sep + 'Videos' + os.sep + '%(title)s.%(ext)s',
                    'retries':2,
                    'nooverwrites':True,
                    'restrictfilenames':True,
                    'no_warnings':True,
                })
                with ydl:
                    for youtubeLink in youtubeSoup.find_all('a', href=re.compile("http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?")):
                        print("\t\t\t\tDownloading youtube link:", youtubeLink['href'])
                        result = ydl.extract_info(youtubeLink['href'], download=True)
                filename = fileLink.text.replace(' ', '_').replace('/', "")
                with open(savePath + os.sep + filename, "wb") as file:
                    file.write(r.content)