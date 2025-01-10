#!/usr/bin/python3

from teams_config import TeamsConfig
import os
import subprocess
import json
import requests
import sys


class TeamsIdentity:
    def __init__(self, name=None):
        self.cfg = TeamsConfig()
        self.domain = self.cfg.domain()
        self.client = self.cfg.client()
        self.name = name

    def url(self):
        address = self.cfg.nickname(self.name)
        if not address or address == self.name:
            sys.stderr.write("No channel by the nickname {}\n".format(self.name))
            return None

        return "https://{}/{}/IncomingWebhook/{}".format(
                self.domain, self.client, address)

    def __rep__(self):
        return "<Teams {}>".format(self.url())

    def __str__(self):
        return self.__rep__()


class ToTeams:
    def __init__(self, preview=False):
        self.cfg = TeamsConfig()
        self.preview = preview

    def url(self, identity=None, name=None):
        if not identity:
            identity = TeamsIdentity(name=name)

        return identity.url()

    def markdown(self, content):
        if isinstance(content, list):
            content = "\n".join(content)

        ps = subprocess.Popen(('kramdown', '-o', 'teams'),
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        res = ps.communicate(input=content.encode('utf-8'))[0].decode('utf-8')
        return json.loads(res)

    def block(self, text, markdown=True):
        if markdown:
            return { 'type': 'TextBlock',
                     'text': text,
                     'wrap': True }

        return { 'type': 'RichTextBlock',
                 'inlines': [{'type': 'TextRun', 'text': t} for t in text.split()]}

    def section(self, content, markdown=True):
        return {"type": "TextBlock", "text": content, "wrap": True }

    def table(self, content, markdown=True):
        index = 0
        found = True

        columns = []
        while found:
            column = {'type': 'Column', 'items': []}
            first = False
            for row in content:
                text = ''
                if len(row) > index:
                    text = row[index]
                    found = True

                column['items'].append({'type': 'TextBlock', 'text': text, 'wrap': True})

                if first:
                    column['weight'] = 'Bolder'

            if found:
                columns.append(column)

            if column == 0:
                colomn['width'] = 'stretch' if columns == 0 else 'auto'

            index += 1

        result = {'type': 'ColumSet',
                  'columns': columns }

        return result

    def payload(self, content, text=None):
        body = []
        result = { 'type': 'message',
                   'attachments': [
                    {"contentType": "application/vnd.microsoft.card.adaptive",
                     "contentUrl": None,
                     "content": {
                         "type": "AdaptiveCard",
                         "$schema": "https://adaptivecards.io/schema/adaptive-card.json",
                         "version": "1.3",
                         "body": body}}]}

        if text:
            result['summary'] = text

        if isinstance(content, str) and not text:
            body.append({'type': 'TextBlock', 'text': content, 'wrap': True})
        elif isinstance(content, dict):
            body.append(content)
        elif isinstance(content, list):
            if len(content) > 0 and not isinstance(content[0], str):
                
                body += content
            else:
                print("E")
                for line in content:
                    if 'text' not in result:
                        result['text'] = ''

                    result['text'] += str(line) + "\n"
        else:
            body += content

        return result

    def to(self, content, markdown=True,
           name=None, text=None,
           identity=None,
           preview=False):
        if markdown:
            content = self.markdown(content)

        url = self.url(identity=identity, name=name)
        payload = self.payload(content, text)
        data = json.dumps(payload)
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
