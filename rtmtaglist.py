# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Nikola Škorić (nskoric [ at ] gmail.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Please see the GPL license at http://www.gnu.org/licenses/gpl.txt
#
# To contact the author, see http://github.com/dijxtra/rtmtaglister

"""A script fetching a Remember The Milk list and then printing it's tasks grouped by tags. Useful because RTM currently (April 2013) does not have this option."""

__all__ = ['main']

import ConfigParser
import urllib2
import os.path
from collections import OrderedDict
from icalendar import Calendar


def parse_conf(conf_file = "rtm.conf"):
    """Parses config file passed as parameter and returns it's sections as dictionaries."""
    if not os.path.isfile(conf_file):
        print "Config file " + conf_file + " not found. Exiting."
        exit()
      

    Config = ConfigParser.ConfigParser()
    Config.read(conf_file)
    login = dict(Config.items('login'))
    urls = dict(Config.items('urls'))

    return login, urls

def get_ical(username, password, top_level_url, url):
    """Connects to Rememberthemilk web site and retrieves a icalendar file"""
    # create a password manager
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

    # Add the username and password.
    # If we knew the realm, we could use it instead of None.
    password_mgr.add_password(None, top_level_url, username, password)

    handler = urllib2.HTTPBasicAuthHandler(password_mgr)

    # create "opener" (OpenerDirector instance)
    opener = urllib2.build_opener(handler)

    # use the opener to fetch a URL
    opener.open(url)

    # Install the opener.
    # Now all calls to urllib2.urlopen use our opener.
    urllib2.install_opener(opener)

    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    the_page = response.read()

    return the_page

def extract_tags(desc):
    """Extracts "Tags: " property of RTM task from icalendar "Description: " property."""
    for s in desc.split("\n"):
        if s.startswith("Tags: ") and s != "Tags: none":
            return s.split("Tags: ")[1]

    return ''

def filter(component):
    """Returns true if component is a type of task we wish to use."""
    if component.name == 'VTODO' \
    and component.get('status', None) is None:
        return True
    else:
        return False

def fillotagdic(gcal):
    """Takes a icalendar.Calendar() object and returns an OrderedDict of tasks grouped according to their tags."""
    tagdic = {}
    tagdic[''] = []

    for component in gcal.walk():
        if filter(component):
            tags = extract_tags(component['description'])
            if tags != '':
                if tagdic.get(tags, None) is None:
                    tagdic[tags] = []
                tagdic[tags].append(component['summary'])
                tags = ' [' + tags + ']'
            else:
                tagdic[''].append(component['summary'])

    return OrderedDict(sorted(tagdic.items()))

def main():
    """Configures user credentials and target list and then does the job."""

    login, urls = parse_conf()
    username = login['username']
    password = login['password']
    top_level_url = urls['base']
    url = top_level_url + urls['calendar']

    ical = get_ical(username, password, top_level_url, url)
#    ical = open("cal.ical").read()

    gcal = Calendar.from_ical(ical)

    otagdic = fillotagdic(gcal)

    for tag in otagdic:
        print "### " + tag.upper().encode('utf-8') + " ###"
        print

        for task in sorted(otagdic[tag]):
            print task.encode('utf-8')

        print

if __name__ == "__main__":
    main()
