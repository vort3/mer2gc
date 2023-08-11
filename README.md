# mer2gc

Script to add flights from Web Meridian to Google Calendar. 

## Configuration

Configuration is read from a json formatted file located in ~/.config/mer2gc/ . Default file name is "config.json". It's also possible to use "-c" flag to pass custom config file name to the script.
It has to contain Web Meridian server's URL, DIR URL, user's login and password, and Google Calendar URL.

There must be a serviceacct.json file with google service account keys in the same directory.
Service account needs write access to user's calendar to create new events.

## ToDo:

[ ] Add destination weather forecast
[ ] Add dirs for aircraft
[ ] Add JSON passee configuration
