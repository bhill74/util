#!/usr/bin/python

import os
import sys
sys.path.insert(0, os.path.join(os.getenv('HOME'),'lib','config'))
from local_config import LocalConfigParser


class TeamsConfig(LocalConfigParser):
    def __init__(self):
        LocalConfigParser.__init__(self, "teams.cfg", os.path.dirname(__file__))

    def get_base(self, option, var):
        if self.has_section('WebHook') and self.has_option('WebHook', option):
            return self.get('WebHook', option).strip()

        return os.getenv(var, '')

    def domain(self):
        return self.get_base('domain', 'TEAMS_DOMAIN')

    def client(self):
        return self.get_base('client', 'TEAMS_CLIENT')

    def hook(self):
        return self.get_base('hook', 'TEAMS_HOOK')

    def token(self):
        return self.get_base('token', 'TEAMS_HOOK_TOKEN')

    def nickname(self, name):
        if self.has_section('Nicknames') and self.has_option('Nicknames', name):
            return self.get('Nicknames', name).strip()

        return name
