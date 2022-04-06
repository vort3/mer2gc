#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
import locations
import datetime
import logging
import json
import sys
import os
import re


def get_pagetext(url, login, password):
    opt = Options()
    opt.headless = True
    opt.add_argument("-private")
    s = Service('/usr/bin/geckodriver', log_path=os.devnull)

    with webdriver.Firefox(options=opt, service=s) as drv:
        drv.get(url)
        drv.find_elements(By.CLASS_NAME, "z-textbox")[0].send_keys(login)
        drv.find_elements(By.CLASS_NAME, "z-textbox")[1].send_keys(password)
        drv.find_element(By.CLASS_NAME, "z-button").click()
        drv.get(url + "/web.meridian/workplan.zul")
        pagetext = BeautifulSoup(drv.page_source, "html.parser").get_text()
        return pagetext


def get_username(pagetext, alternative=False):
    if not alternative:
        # For when bs4 eats all newlines
        pattern = "\s([A-Z]+ [A-Z]+)\s+.*?7" 
    elif alternative:
        logging.info("Using alternative pattern to parse username.")
        pattern = "\n([A-Z]+ [A-Z]+)\n"

    match = re.findall(pattern, pagetext)
    return match[0]


def get_legs(pagetext, alternative=False):
    if not alternative:
        # For when bs4 eats all newlines:
        pattern = ( "(?:(\d{2}\.\d{2}\.\d{4})\s*\([A-Z][a-z]{2}\)\n*)?\s*"
                    "(\d{2}:\d{2})([A-Z]{3})\s*"
                    "(DV\d{3,4}D?).*?"
                    "(\d{2}:\d{2})"
                    "(?:\s*\(\+1\))?"
                    "([A-Z]{3})(.*?):" )
    elif alternative:
        # When each cell is on a separate line:
        logging.info("Using alternative pattern to parse legs.")
        pattern = ( "(?:(\d{2}\.\d{2}\.\d{4})\s\([A-Z][a-z]{2}\)\n{3,4})?"
                    "(\d{2}:\d{2})"
                    "([A-Z]{3})\n"
                    "(DV\d{3,4}D?).*\n"
                    "(\d{2}:\d{2})"
                    "(?:\s\(\+1\))?"
                    "([A-Z]{3})"
                    "\n.*\n"
                    "(.*)" )

    match = re.findall(pattern, pagetext)
    legs = list(map(list, match))
    
    for i, leg in enumerate(legs):
        if leg[0] == '':
            leg[0] = legs[i-1][0]
    
    return legs


def process_leg(leg, calendar, username):
    fnumber = leg[3]
    dep = leg[2]
    dest = leg[5]
    title = f'{dep}-{dest} {fnumber} (PAX)' if f"{username} [pax]" in leg[6] \
                                            else f'{dep}-{dest} {fnumber}'
    start = datetime.datetime.strptime(leg[0]+leg[1], '%d.%m.%Y%H:%M')
    start = start.replace(tzinfo=datetime.timezone.utc)
    end = datetime.datetime.strptime(leg[0]+leg[4], '%d.%m.%Y%H:%M')
    end = end.replace(tzinfo=datetime.timezone.utc)
    if end < start:
        end += datetime.timedelta(days=1)
    flight = f"{start.date().isoformat()} {fnumber}"
    print(f"Current flight:\t{flight}")
    existing = list(calendar.get_events(time_min=start.date(),
                    time_max=end.date(), query=title, timezone='Etc/UTC'))
    if existing:
        print(f"Existing event found:\t{existing[0].start.date()}",
              f"{existing[0].summary}")
        if existing[0].start == start and existing[0].end == end:
            print("Start and end times match. Skipping…")
            return
        print("Updating event…",
              f"{str(existing[0].start)[:16]} - {str(existing[0].end)[:16]}",
              f"---> {str(start)[:16]} - {str(end)[:16]}")
        existing[0].start = start
        existing[0].end = end
        calendar.update_event(existing[0])
        return
    event = Event(title, start, end)
    event.timezone = "Etc/UTC"
    event.location = locations.locations.get(dest, "Unknown location")
    event.add_popup_reminder(minutes_before_start=180)
    event.description = "Created by Meridian2GC"
    print(f"Generated event:\t{title}")
    calendar.add_event(event)
    print("Event added")


def main():
    configpath = os.path.join(os.path.expanduser("~"), ".config", "mer2gc")
    with open(os.path.join(configpath, "config.json")) as fp:
        conf = json.load(fp)
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = os.path.join(configpath, "serviceacct.json")
    credentials = service_account.Credentials.from_service_account_file(
                  SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    calendar = GoogleCalendar(conf['calendar'], credentials=credentials)

    if "-a" in sys.argv:
        alternative = True
        logging.basicConfig(level=logging.INFO)
    else:
        alternative = False

    pagetext = get_pagetext(conf['url'], conf['login'], conf['password'])
    username = get_username(pagetext, alternative=alternative)
    legs = get_legs(pagetext, alternative=alternative)
    
    for leg in legs:
        process_leg(leg, calendar, username)


if __name__ == "__main__":
    main()

