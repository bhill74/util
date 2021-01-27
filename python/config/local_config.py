#!/usr/bin/python

# import select, json, getopt, sys
from ConfigParser import ConfigParser
import os.path


class LocalConfigParser(ConfigParser):
    def __init__(self, name):
        ConfigParser.__init__(self, allow_no_value=True)
        dir_name = os.getcwd()
        home_dir = os.path.expanduser("~")
        use_home = False
        while True:
            file_name = dir_name + '/' + name
            if (os.path.exists(file_name)):
                self.read(file_name)
                break

            if dir_name == home_dir:
                use_home = True

            if dir_name == '':
                break

            dir_name = os.path.dirname(dir_name)
            if dir_name == '/':
                dir_name = ''

        file_name = home_dir + '/' + name
        if not use_home and os.path.exists(file_name):
            self.read(file_name)

# Resolve the channel if a nickname was used.
# config = ConfigParser.ConfigParser()
# config.read(expanduser("~/slack.cfg"))
# section = 'Nicknames'
# if ('channel' in result and config.has_section(section)
# and config.has_option(section, result['channel'])):
# result['channel'] = config.get(section, result['channel'])
