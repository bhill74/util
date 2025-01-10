# import select, json, getopt, sys
import os
import sys

# External modules
#sys.path.insert(0, os.path.join(os.getenv('HOME'), 'lib', 'ext'))
from configparser import ConfigParser


class LocalConfigParser(ConfigParser):
    def __init__(self, name, path=None):
        ConfigParser.__init__(self, allow_no_value=True)
        dir_name = os.getcwd()
        home_dir = os.path.expanduser("~")
        use_home = False
        self._file = None
        self._name = name

        if path:
            file_name = path + '/' + name
            if (os.path.exists(file_name)):
                self.read(file_name)

        while True:
            file_name = dir_name + '/' + name
            if (os.path.exists(file_name)):
                self.read(file_name)
                self._file = file_name
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
            self._file = file_name

    def write(self):
        if not self._file:
            self._file = "./{}".format(self._name)
            print("Creating new config file {}".format(self._file))
        else:
            print("Updating config file {}".format(self._file))

        with open(self._file, 'w') as f:
            ConfigParser.write(self, f)

# Resolve the channel if a nickname was used.
# config = ConfigParser.ConfigParser()
# config.read(expanduser("~/slack.cfg"))
# section = 'Nicknames'
# if ('channel' in result and config.has_section(section)
# and config.has_option(section, result['channel'])):
# result['channel'] = config.get(section, result['channel'])
