#!/usr/bin/python

from local_config import LocalConfigParser
import os


class SlackConfig(LocalConfigParser):
    def __init__(self):
        LocalConfigParser.__init__(self, "slack.cfg")

    def get_base(self, option, var):
        if self.has_section('WebHook') and self.has_option('WebHook', option):
            return self.get('WebHook', option).strip()

        return os.getenv(var, '')

    def client(self):
        return self.get_base('client', 'SLACK_CLIENT')

    def hook(self):
        return self.get_base('hook', 'SLACK_HOOK')

    def token(self):
        return self.get_base('token', 'SLACK_HOOK_TOKEN')

    def nickname(self, name):
        if self.has_section('Nicknames') and self.has_option('Nicknames', name):
            return self.get('Nicknames', name).strip()

        return name
