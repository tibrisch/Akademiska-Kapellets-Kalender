#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from HTMLParser import HTMLParser
from urllib2 import urlopen
import getopt
import sys
import gdata.calendar
import gdata.calendar.service
from datetime import datetime, date, time, tzinfo
from dateutil import tz
import atom 

class Spider(HTMLParser):
    def __init__(self, url, year, month):
        self.in_calendar = False
        self.tagstack = []
        self.month = month
        self.year = year
        self.tmp_list = []
        self.main_list = []
    
        # Add month and year to urlstring
        url_str = url + "?modCaly={y}&modCalm={m}".format(y=year,m=month)
        HTMLParser.__init__(self)
        
        # Open url and decode data
        req = urlopen(url_str)
        self.feed(req.read().decode("iso-8859-1").encode("utf-8"))
          
    def handle_starttag(self, tag, attrs):
    
        # Do not start calendar parsing until we are inside "com_cal"
        if tag == "div" and attrs:
            if attrs[0][0] == "class" and attrs[0][1] == "com_cal":
                self.in_calendar = True

        # If we are in the calendar section add tag attributes to our stack
        if self.in_calendar:
            self.tagstack.append(attrs)
                
    def handle_endtag(self, tag):
    
        # If we are in the calendar section pop one item from the stack
        if self.in_calendar:
            if self.tagstack != []:
                self.tagstack.pop()
            else:
                if len(self.tmp_list) > 1:
                    self.main_list.append(self.tmp_list)
                self.in_calendar = False
                
    def get_data(self):
        return self.main_list

    def set_info(self, data):
        data = data.strip('\n').strip('\r')
        if self.tmp_list != []:
            if data != ' ' and data != '':
                self.tmp_list.append(data.lstrip(' ').rstrip(' '))

    def handle_data(self, data):
        # If our stack is not empty
        if self.tagstack != []: 
            tag_attrs = self.tagstack[-1]
            if tag_attrs != []:    
                if tag_attrs[0][1] == "daynum" or \
                   tag_attrs[0][1] == "reddaynum":
                
                    if len(self.tmp_list) > 1:
                        self.main_list.append(self.tmp_list)
                    self.tmp_list = []
                    self.tmp_list.append((self.year, self.month, int(data.split(" - ")[0])))
                    
                elif tag_attrs[0][1] == "event1":
                    self.set_info(data.rstrip(": Repschema-"))
                elif tag_attrs[0][1] == "eventdescr":                   
                    self.set_info(data)
                elif tag_attrs[0][0] == "href" or \
                     tag_attrs[0][1] == "nextprev" or \
                     tag_attrs[0][1] == "wnum":
                    pass                                  
                else:
                    self.set_info(data)
            else:
                self.set_info(data)

class GoogleCalendar:
    def __init__(self, email, password):
        self.cal_client = gdata.calendar.service.CalendarService()
        self.cal_client.email = email
        self.cal_client.password = password
        self.cal_client.source = 'Google-Calendar_Python_Sample-1.0'
        self.cal_client.ProgrammaticLogin()


        #'2010-08-29T17:58:45.000Z'
    def add_event(self, title, content, where, start_time, end_time):
        print start_time
        print end_time
        event = gdata.calendar.CalendarEventEntry()
        event.title = atom.Title(text=title)
        event.content = atom.Content(text=content)
        event.where.append(gdata.calendar.Where(value_string=where))
        event.when.append(gdata.calendar.When(start_time=start_time, end_time=end_time))      
        new_event = self.cal_client.InsertEvent(event, self.kapell_cal.content.src)
        return new_event   
            
        
    def _get_calendar(self, name): 
        feed = self.cal_client.GetOwnCalendarsFeed()
        for a_calendar in feed.entry:
            if a_calendar.title.text == name:
                return a_calendar
        return None

    def Run(self):
        cal = self._get_calendar("Akademiska Kapellet")
        if cal == None:
            print "Calendar not found, creating a new ..."
        else:
	    print "Calendar found, replacing data ..."
            self.cal_client.Delete(cal.GetEditLink().href)

        cal = gdata.calendar.CalendarListEntry()
        cal.title = atom.Title(text="Kapellet")
        cal.summary = atom.Summary(text="Kungliga Akademiska Kapellets repetitions- och konsertschema")
        cal.where = gdata.calendar.Where(value_string='Uppsala')
        cal.color = gdata.calendar.Color(value='#2952A3')
        cal.timezone = gdata.calendar.Timezone(value='Europe/Stockholm')
        cal.hidden = gdata.calendar.Hidden(value='false')

        self.kapell_cal = self.cal_client.InsertCalendar(new_calendar=cal)
        

def print_usage():
    print
    print "Usage:"
    print "--user [username] --pw [password]"
    
def main():
  # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["user=", "pw="])
    except getopt.error, msg:
        print_usage()
        sys.exit(2)

    user = ''
    pw = ''

    # Process options
    for o, a in opts:
        if o == "--user":
            user = a
        elif o == "--pw":
            pw = a

    if user == '' or pw == '':
        print_usage()
        sys.exit(2)

    cal = GoogleCalendar(user, pw)
    cal.Run()

    for month in range(date.today().month, 12 + 1):
        spider = Spider("http://www.akademiskakapellet.uu.se/node43", 2011, month)
        for event in spider.get_data():    
            year = event[0][0]
            month = event[0][1]
            day = event[0][2]
            times = event[1].split(" - ")          
            start_hour = int(times[0].split(".")[0])
            start_minute = int(times[0].split(".")[1])
            end_hour = int(times[1].split(".")[0])
            end_minute = int(times[1].split(".")[1])
     
	
          
            start = datetime(year, month, day, start_hour%24, start_minute, 0, tzinfo=cet)
            end = datetime(year, month, day, end_hour%24, end_minute, 0, tzinfo=cet)
        
            title = event[2]
            where = "Uppsala"
            content = ""         
            for s in event[3:]:
                content += s + "\n"
            utc = tz.gettz('UTC')
            cal.add_event(title, content, where, start.astimezone(utc).isoformat(), end.astimezone(utc).isoformat())

if __name__ == '__main__':
  main()



    
