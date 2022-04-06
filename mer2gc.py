#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
import datetime
import logging
import json
import sys
import os
import re


locations = {
    "AER": "Sochi International Airport (Adler), Ulitsa Mira, 50, Adler, Krasnodarskiy kray, Russia, 354355",
    "AKX": "Aktobe International Airport, 66X6+G83, Aktobe, Kazakhstan",
    "ALA": "Almaty International Airport, Mailin St 2, Almaty 050039, Kazakhstan",
    "AYT": "Antalya Airport, Antalya Havaalanı Dış Hatlar Terminali 1, 07230 Muratpaşa/Antalya, Turkey",
    "BQS": "Ignatievo Airport, Ignatyevskaya Rd, Blagoveshchensk, Amurskaya oblast', Russia, 675019",
    "BUD": "Budapest Airport, Budapest, 1185 Hungary",
    "CIT": "Airport, 9F8V+F6G, Shymkent, Kazakhstan",
    "DMB": "Taraz Airport, ул. Аэропорт б/н, Taraz 080000, Kazakhstan",
    "DWC": "Al Maktoum International Airport, Emirates Rd - Dubai - United Arab Emirates",
    "GUW": "Atyrau International Airport, Abulkhair Khan Ave 22, Atyrau 060000, Kazakhstan",
    "GYD": "Heydar Aliyev International Airport, AZ1109, settlement, Baku, Azerbaijan",
    "HAK": "Haikou Meilan International Airport, Meilan, Haikou, Hainan, China, 571126",
    "HKT": "Phuket International Airport, Mai Khao, Thalang District, Phuket 83110, Thailand",
    "HRG": "Hurghada International Airport, Hurghada Airport Toll Gate, Airport rd، قسم الغردقة، البحر الأحمر 84511, Egypt",
    "IST": "Istanbul Airport, Tayakadın, Terminal Caddesi No:1, 34283 Arnavutköy/İstanbul, Turkey",
    "JED": "Jeddah Airport, King Abdulaziz International Airport, Jeddah 23631, Saudi Arabia",
    "KGF": "Sary-Arka Airport, Karagandy 100000, Kazakhstan",
    "KOV": "Kokshetau Airport, а/я 432, г.Кокшетау 020004, Kazakhstan",
    "KRR": "Krasnodar International Airport, Ulitsa Yevdokii Bershanskoy, 355, Krasnodar, Krasnodarskiy kray, Russia, 350912",
    "KSN": "Airport Kostanay, Oral Street 39, Kostanay 110000, Kazakhstan",
    "MCT": "Muscat International Airport, Muscat, Oman",
    "MED": "Prince Mohammed Bin Abdulaziz International Airport, Medina Saudi Arabia",
    "MRV": "Aeroport Mineral'nyye Vody, Mineralnye Vody, Stavropol Krai, Russia, 357205",
    "NQZ": "International airport \"Astana\", Nur-Sultan 020000, Kazakhstan",
    "NRT": "Narita International Airport, 1-1 Furugome, Narita, Chiba 282-0004, Japan",
    "OSS": "Osh International Airport, Osh, Kyrgyzstan",
    "PPK": "Aeroport Petropavlovsk, 150000, Kazakhstan",
    "PWQ": "«Pavlodar» äwejayı, 140000, Kazakhstan",
    "SAW": "Sabiha Gokcen International Airport, Sanayi, 34906 Pendik/İstanbul, Turkey",
    "SCO": "Aktau Airport",
    "SSH": "Sharm El Sheikh International Airport, 2 El-Salam, Qesm Sharm Ash Sheikh, South Sinai Governorate, Egypt",
    "SYX": "Sanya Phoenix International Airport, Fenghuangzhen, Tianya, Sanya, Hainan, China, 572000",
    "TSE": "Nursultan Nazarbayev International Airport, Astana 020000, Kazakhstan",
    "UKK": "Aeroport Ust'-Kamenogorska, Ust'-Kamenogorsk 070000, Kazakhstan",
    "URA": "Ақжол халықаралық әуежайы, Тұқпай, Kazakhstan",
    "VKO": "Vnukovo International Airport, Vnukovo, Moscow Oblast, Russia",
    "VNO": "Vilnius International Airport, Rodūnios kl. 10A, Vilnius 02189, Lithuania",
    "XIY": "Xi'an Xianyang International Airport, Weicheng, Xianyang, Shaanxi, China",
    "DAC": "Hazrat Shahjalal International Airport",
}


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
    event.location = locations.get(dest, "Unknown location")
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

