# mer2gc

Script to add flights from Web Meridian to Google Calendar. 

## Configuration

Configuration is read from a .json file located in ~/.config/mer2gc/config.json .
It has to contain Web Meridian server's URL, user's login and password, and Google Calendar URL.

There must be a serviceacct.json file with google service account keys in the same directory.
Service account needs write access to user's calendar to create new events.
