#!/usr/bin/python

from slack_config import SlackConfig
import os
import subprocess
import json
import requests


class SlackIdentity:
    def __init__(self):
        cfg = SlackConfig()
        self.client = cfg.client()
        self.hook = cfg.hook()
        self.token = cfg.token()

    def url(self):
        return "https://hooks.slack.com/services/{}/{}/{}".format(
                self.client, self.hook, self.token)

    def __rep__(self):
        return "<Slack {}>".format(self.url())

    def __str__(self):
        return self.__rep__()


class ToSlack:
    def __init__(self, preview=False):
        self.cfg = SlackConfig()
        self.preview = preview

    def url(self, identity=None):
        if not identity:
            identity = SlackIdentity()

        return identity.url()

    def markdown(self, content):
        if isinstance(content, list):
            content = "\n".join(content)

        ps = subprocess.Popen(('kramdown', '-o', 'slack'),
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        res = ps.communicate(input=content.encode('utf-8'))[0].decode('utf-8')
        return json.loads(res)

    def block(self, text, markdown=True):
        return {"type": "mrkdwn" if markdown else "text", "text": text}

    def section(self, content, markdown=True):
        return {"type": "section", "text": self.block(content, markdown=markdown)}

    def table(self, content, markdown=True, delim=None):
        b = 0
        d = 5   # Break the content into 5-line chunks.
        sep = " "
        if delim:
            sep = " " + delim + " "

        result = []
        while (b < len(content)):
            fields = {"type": "section", "fields": []}
            for i in range(b, min(len(content), b+d)):
                c = content[i]
                fields["fields"].append(self.block(c[0], markdown=markdown))
                fields["fields"].append(self.block(sep.join(c[1:]), markdown=markdown))
    
            result.append(fields)
            b += d;

        return result

    def payload(self, content, channel=None, username=None,
                text=None, emoji=None, icon=None):
        result = {}

        if channel:
            result['channel'] = self.cfg.nickname(channel)

        if username:
            result['username'] = username

        if text:
            result['text'] = text

        if emoji:
            result['icon_emoji'] = ":{}:".format(emoji)

        if icon:
            result['icon_url'] = icon

        if isinstance(content, str) and not text:
            result['text'] = content
        elif isinstance(content, dict):
            result['blocks'] = [content]
        elif isinstance(content, list):
            if len(content) > 0 and not isinstance(content[0], str):
                result['blocks'] = content
            else:
                print("E")
                for line in content:
                    if 'text' not in result:
                        result['text'] = ''

                    result['text'] += str(line) + "\n"
        else:
            result['blocks'] = content

        return result

    def to(self, content, markdown=True,
           channel=None, username=None, text=None, emoji=None, icon=None,
           identity=None,
           preview=False):
        if markdown:
            content = self.markdown(content)

        url = self.url(identity=identity)
        payload = self.payload(content, channel, username, text, emoji, icon)
        data = {'payload': json.dumps(payload)}
        preview = preview if preview else self.preview
        if preview:
            print("URL", url)
            print("PAYLOAD:{}".format(json.dumps(payload, indent=4)))
            return True

        res = requests.post(url, data=data)
        if res.status_code != 200:
            print("URL:{}".format(url))
            print("PAYLOAD:{}".format(json.dumps(payload, indent=4)))
            print("ERROR: --- {} ---".format(res.text))
            return False

        return True
