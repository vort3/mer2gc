#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from google.oauth2 import service_account
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
from bs4 import BeautifulSoup
import keys
import datetime
import logging
import json
import sys
import os


def get_pagesource(url, login, password):
    opt = Options()
    opt.headless = True
    opt.add_argument("-private")
    s = Service('/usr/bin/geckodriver', log_path=os.devnull)

    with webdriver.Firefox(options=opt, service=s) as drv:
        drv.get(url)
        WebDriverWait(drv, 30).until(EC.visibility_of_element_located(
                                    (By.CLASS_NAME, "z-button")))
        drv.find_elements(By.CLASS_NAME, "z-textbox")[0].send_keys(login)
        drv.find_elements(By.CLASS_NAME, "z-textbox")[1].send_keys(password)
        drv.find_element(By.CLASS_NAME, "z-button").click()
        drv.get(url + "/web.meridian/workplan.zul")
        WebDriverWait(drv, 30).until(EC.visibility_of_element_located(
                                    (By.CLASS_NAME, "fio")))
        src = BeautifulSoup(drv.page_source, "html.parser")
        logging.debug(src)
        return src


def get_events(src):
    events = []

    rows = src.select(".z-listitem")
    for row in rows:
        event = {}
        for i, cell in enumerate(row.select(".z-listcell-content")):
            content = []
            for span in cell.select("span"):
                if "display:none" not in span.get("style", ""):
                    content.append(span.text)
            event[keys.cellkeys[i]] = content
        events.append(event)
    
    for i, event in enumerate(events):
        if len(event) == 3:
            event["date"] = event["departure"][0].split()
        else:
            event["date"] = events[i - 1]["date"]
    
    return list(filter(lambda i: len(i) != 4, events))


def process_event(event, calendar):
    if len(event["event"]) == 0:
        # ToDo: handle trainings better
        event["event"] = ["TRAINING: " + event["comment"][-1]]
    fnumber = event["event"][0]
    dep = event["departure"][-1]
    arr = event["arrival"][-1]
    
    if "Passenger on task" in event["info"]:
        title = f"{dep}-{arr} {fnumber} (PAX)"
    elif "TRAINING" in event["event"][0]:
        title = fnumber
    else:
        title = f"{dep}-{arr} {fnumber}"
    
    start = datetime.datetime.strptime(
            event["date"][0] + event["departure"][0], "%d.%m.%Y%H:%M")
    start = start.replace(tzinfo=datetime.timezone.utc)
    end   = datetime.datetime.strptime(
            event["date"][0] + event["arrival"][0], "%d.%m.%Y%H:%M")
    end   = end.replace(tzinfo=datetime.timezone.utc)

    if " (+1)" in event["arrival"]:
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
    event.location = keys.locations.get(arr, "Unknown location")
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

    if "-v" in sys.argv:
        logging.basicConfig(format="[%(levelname)s]\t%(message)s",
                            level=logging.DEBUG, stream=sys.stdout)
    elif "-q" in sys.argv:
        logging.basicConfig(format="[%(levelname)s]\t%(message)s",
                            level=logging.WARNING, stream=sys.stdout)
    else:
        logging.basicConfig(format="[%(levelname)s]\t%(message)s",
                            level=logging.INFO, stream=sys.stdout)

    src = get_pagesource(conf['url'], conf['login'], conf['password'])
    events = get_events(src)
    for event in events:
        process_event(event, calendar)


if __name__ == "__main__":
    main()

