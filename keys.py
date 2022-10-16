#!/usr/bin/env python3

locations = {
    "AER": "Sochi International Airport (Adler), Ulitsa Mira, 50, Adler, Krasnodarskiy kray, Russia, 354355",
    "AKX": "Aktobe International Airport, 66X6+G83, Aktobe, Kazakhstan",
    "ALA": "Almaty International Airport, Mailin St 2, Almaty 050039, Kazakhstan",
    "AYT": "Antalya Airport, Antalya Havaalanı Dış Hatlar Terminali 1, 07230 Muratpaşa/Antalya, Turkey",
    "BQS": "Ignatievo Airport, Ignatyevskaya Rd, Blagoveshchensk, Amurskaya oblast', Russia, 675019",
    "BUD": "Budapest Airport, Budapest, 1185 Hungary",
    "CIT": "Airport, 9F8V+F6G, Shymkent, Kazakhstan",
    "DAC": "Hazrat Shahjalal International Airport",
    "DMB": "Taraz Airport, ул. Аэропорт б/н, Taraz 080000, Kazakhstan",
    "DWC": "Al Maktoum International Airport, Emirates Rd - Dubai - United Arab Emirates",
    "EVN": "Zvartnots International Airport (EVN), Yerevan, Armenia",
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
    "LED": "Pulkovo Airport (LED), Pulkovskoye Shosse, Saint Petersburg, Russia",
    "MCT": "Muscat International Airport, Muscat, Oman",
    "MED": "Prince Mohammed Bin Abdulaziz International Airport, Medina Saudi Arabia",
    "MRV": "Aeroport Mineral'nyye Vody, Mineralnye Vody, Stavropol Krai, Russia, 357205",
    "NCU": "Nukus International Airport, FJM8+727, A. Dosnazarov ko'shesi, Nukus, Uzbekistan",
    "NQZ": "International airport \"Astana\", Nur-Sultan 020000, Kazakhstan",
    "NRT": "Narita International Airport, 1-1 Furugome, Narita, Chiba 282-0004, Japan",
    "OSS": "Osh International Airport, Osh, Kyrgyzstan",
    "PPK": "Aeroport Petropavlovsk, 150000, Kazakhstan",
    "PWQ": "«Pavlodar» äwejayı, 140000, Kazakhstan",
    "SAW": "Sabiha Gokcen International Airport, Sanayi, 34906 Pendik/İstanbul, Turkey",
    "SCO": "Aktau Airport",
    "SSH": "Sharm El Sheikh International Airport, 2 El-Salam, Qesm Sharm Ash Sheikh, South Sinai Governorate, Egypt",
    "SYX": "Sanya Phoenix International Airport, Fenghuangzhen, Tianya, Sanya, Hainan, China, 572000",
    "TBS": "Tbilisi International Airport",
    "TSE": "Nursultan Nazarbayev International Airport, Astana 020000, Kazakhstan",
    "UGC": "Urgench International Airport",
    "UKK": "Aeroport Ust'-Kamenogorska, Ust'-Kamenogorsk 070000, Kazakhstan",
    "URA": "Ақжол халықаралық әуежайы, Тұқпай, Kazakhstan",
    "VKO": "Vnukovo International Airport, Vnukovo, Moscow Oblast, Russia",
    "VNO": "Vilnius International Airport, Rodūnios kl. 10A, Vilnius 02189, Lithuania",
    "XIY": "Xi'an Xianyang International Airport, Weicheng, Xianyang, Shaanxi, China",
}


cellkeys = {
    0: "icon",
    1: "departure",
    2: "event",
    3: "arrival",
    4: "crew",
    5: "info",
    6: "comment",
    7: "confirm",
    8: "reports",
}


