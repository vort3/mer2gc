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
        logging.debug(pagetext)
        return pagetext


def get_username(pagetext, alternative=False):
    if not alternative:
        # For when bs4 eats all newlines
        pattern = "\s(?P<username>[A-Z]+ [A-Z]+)\s+.*?7"
    elif alternative:
        logging.info("Using alternative pattern to parse username.")
        pattern = "\n(?P<username>[A-Z]+ [A-Z]+)\n"

    match = re.search(pattern, pagetext)
    if match is None:
        return
    return match.group(1)


def get_legs(pagetext, alternative=False):
    if not alternative:
        # For when bs4 eats all newlines:
        pattern = ( "(?:(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
                    "\([A-Z][a-z]{2}\)\n*)?\s*"
                    "(?P<start>\d{2}:\d{2})"
                    "(?P<dep>[A-Z]{3})\s*"
                    "(?P<fnumber>DV\d{3,4}D?).*?"
                    "(?P<end>\d{2}:\d{2})"
                    "(?:\s*\(\+1\))?"
                    "(?P<dest>[A-Z]{3})"
                    "(?P<crew>.*?):" )
    elif alternative:
        # When each cell is on a separate line:
        logging.info("Using alternative pattern to parse legs.")
        pattern = ( "(?:(?P<date>\d{2}\.\d{2}\.\d{4})\s"
                    "\([A-Z][a-z]{2}\)\n{3,4})?"
                    "(?P<start>\d{2}:\d{2})"
                    "(?P<dep>[A-Z]{3})\n"
                    "(?P<fnumber>DV\d{3,4}D?).*\n"
                    "(?P<end>\d{2}:\d{2})"
                    "(?:\s\(\+1\))?"
                    "(?P<dest>[A-Z]{3})"
                    "\n.*\n"
                    "(?P<crew>.*)" )

    legs = [m.groupdict() for m in re.finditer(pattern, pagetext)]
    
    for i, leg in enumerate(legs):
        if leg["date"] == None:
            leg["date"] = legs[i-1]["date"]
    
    return legs


def get_reserves(pagetext, alternative=False):
    if not alternative:
        # For when bs4 eats all newlines:
        pattern = ( "(?:(?P<date>\d{2}\.\d{2}\.\d{4})\s*"
                    "\([A-Z][a-z]{2}\)\n*)?\s*"
                    "(?P<start>\d{2}:\d{2})\s*"
                    "(?P<title>Рез.*?)\s*"
                    "(?P<end>\d{2}:\d{2})" )
    elif alternative:
        logging.info("Using alternative pattern to parse reserves.")
        logging.info("Warning: Not implemented yet")
        pattern = ""

    reserves = [m.groupdict() for m in re.finditer(pattern, pagetext)]
    
    for i, reserve in enumerate(reserves):
        if reserve["date"] == None:
            reserve["date"] = reserves[i-1]["date"]
    
    return reserves


def process_leg(leg, calendar, username):
    fnumber = leg["fnumber"]
    dep = leg["dep"]
    dest = leg["dest"]
    title = f"{dep}-{dest} {fnumber} (PAX)" if f"{username} [pax]" in leg["crew"] \
                                            else f"{dep}-{dest} {fnumber}"
    start = datetime.datetime.strptime(leg["date"]+leg["start"], "%d.%m.%Y%H:%M")
    start = start.replace(tzinfo=datetime.timezone.utc)
    end = datetime.datetime.strptime(leg["date"]+leg["end"], "%d.%m.%Y%H:%M")
    end = end.replace(tzinfo=datetime.timezone.utc)
    if end < start:
        end += datetime.timedelta(days=1)
    flight = f"{start.date().isoformat()} {fnumber}"
    logging.info(f"Current flight:\t{flight}")
    existing = list(calendar.get_events(time_min=start.date(),
                    time_max=end.date(), query=title, timezone="Etc/UTC"))
    if existing:
        if existing[0].start == start and existing[0].end == end:
            logging.info("Start and end times match. Skipping…")
            return
        print(f"{fnumber}:\t"
              f"{str(existing[0].start)[:16]} - {str(existing[0].end)[:16]}")
        print(f"{fnumber}:\t"
              f"{str(start)[:16]} - {str(end)[:16]}")
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
    logging.info("Event added")


def process_reserve(reserve, calendar):
    title = "RESERVE"
    start = datetime.datetime.strptime(reserve["date"]+reserve["start"], "%d.%m.%Y%H:%M")
    start = start.replace(tzinfo=datetime.timezone.utc)
    end = datetime.datetime.strptime(reserve["date"]+reserve["end"], "%d.%m.%Y%H:%M")
    end = end.replace(tzinfo=datetime.timezone.utc)
    if end < start:
        end += datetime.timedelta(days=1)
    existing = list(calendar.get_events(time_min=start.date(),
                    time_max=end.date(), query=title, timezone="Etc/UTC"))
    if existing:
        if existing[0].start == start and existing[0].end == end:
            logging.info("Start and end times match. Skipping…")
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
    
    last_event = list(calendar.get_events(time_min=datetime.datetime.now() -
                             datetime.timedelta(days=30),
                             time_max=start))[-1]
    event.location = last_event.location
    
    event.add_popup_reminder(minutes_before_start=180)
    event.description = "Created by Meridian2GC"
    print(f"Generated event:\t{title}")
    calendar.add_event(event)
    logging.info("Event added")


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
    else:
        alternative = False

    if "-v" in sys.argv:
        logging.basicConfig(format="[%(levelname)s]\t%(message)s",
                            level=logging.DEBUG, stream=sys.stdout)
    elif "-q" in sys.argv:
        logging.basicConfig(format="[%(levelname)s]\t%(message)s",
                            level=logging.WARNING, stream=sys.stdout)
    else:
        logging.basicConfig(format="[%(levelname)s]\t%(message)s",
                            level=logging.INFO, stream=sys.stdout)
        
    for i in range(10):
        pagetext = get_pagetext(conf['url'], conf['login'], conf['password'])
        username = get_username(pagetext, alternative=alternative)
        if username != None:
            break
    else:
        logging.warning("Unable to load page text.")
        return

    legs = get_legs(pagetext, alternative=alternative)
    for leg in legs:
        process_leg(leg, calendar, username)
    
    reserves = get_reserves(pagetext, alternative=alternative)
    for reserve in reserves:
        process_reserve(reserve, calendar)


if __name__ == "__main__":
    main()

