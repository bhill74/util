import os
import sys
import re
import pkg_resources
import locale
import time
import json

# Local modules
import gbase
import gdrive

# External modules
sys.path.append(os.path.join(os.getenv('HOME'), 'lib', 'ext'))
from googleapiclient.discovery import build

FORM_URL_BASE = "docs.google.com/forms/d/"


def canonicalizeId(gid):
    match = re.match('^https?://{}([^/]+)'.format(FORM_URL_BASE),
                     gid)
    if match:
        return match.groups()[0]

    return gid


class GFormBase(gbase.GoogleAPI):
    def __init__(self, scope, application="forms",
                 credentials=None, service=None,
                 client_file=None,
                 credential_dir=None):
        if not client_file:
            client_file = \
                pkg_resources.resource_filename(__name__,
                                                "forms_client_id.json")
            client_file = os.getenv("GOOGLE_FORMS_CLIENT_ID", client_file)

        scopes = ['.body']
        gbase.GoogleAPI.__init__(
                self, "forms",
                ["auth/forms{}".format(s) for s in scopes],
                client_file, application,
                credentials=credentials,
                service=service,
                credential_dir=credential_dir)

    def get_service(self):
        if not self.service:
            self.service = build(self.api, 'v1', credentials=self.credentials())

        return self.service

    def get_forms(self):
        return self.get_service().forms()


class GItem(GFormBase):
    def __init__(self, gid,
                 application=None, credentials=None, service=None,
                 client_file=None,
                 credential_dir=None):
        self.gid = gid
        GFormBase.__init__(self, "",
                           application=application,
                           credentials=credentials,
                           service=service,
                           client_file=client_file,
                           credential_dir=credential_dir)


class IncompatibleFormat(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


class GForm(GItem):
    def __init__(self,
                 gid=None, name='',
                 application=None, credentials=None, service=None,
                 client_file=None,
                 credential_dir=None):
        self.name = name
        if gid is not None:
            gid = canonicalizeId(gid)

        GItem.__init__(self, gid=gid,
                       application=application,
                       credentials=credentials,
                       service=service,
                       client_file=client_file,
                       credential_dir=credential_dir)

    def init(self, name):
        if self.gid is not None:
            return self.gid

        form = {'info': {'title': name}}

        try:
            result = self.get_forms().create(
                body=form).execute()
            self.gid = result['formId']
        except Exception as e:
            print(e)

        return None

    def _batchUpdate(self, requests):
        try:
            self.get_forms().batchUpdate(
                    formId=self.gid, body={'requests': requests}).execute()
        except Exception as e:
            print(e)

        return None

    def toQuiz(self):
        command = [
                {'updateSettings': {
                     'settings': {'quizSettings': {'isQuiz': True}},
                     'updateMask': 'quickSettings.isQuiz'}}]
        return self._batchUpdate(command)

    def add_file(self, filename):
        gd = gdrive.GDrive(self.application)
        direc = gd.resolve("{}_images".format(self.name), create=True)[0]
        file = direc.createFile(filename, {'file': filename, 'mimeType': 'image/gif'})
        return file

    def add(self, question):
        op = {'createItem': {'item': {}}}

        if isinstance(question, str):
            op['createItem']['item'] = {'title': question}
        elif isinstance(question, dict):
            if 'text' in question:
                op['createItem']['item'] = {'title': question['text']}
                op['createItem']['item']['questionItem'] = \
                    {'question': {'required': True}}
                if 'choices' in question:
                    op['createItem']['item']['questionItem']['question']['choiceQuestion'] = \
                        {'type': 'RADIO',
                         'options': [{'value': str(c)} for c in question['choices']]}

            elif 'image' in question:
                url = question['image']
                if (os.path.exists(url)):
                    file = self.add_file(url)
                    url = file.getViewUrl()

                op['createItem']['item'] = {'imageItem': {'image': {'sourceUri': url}}}
        else:
            return None

        op['createItem']['location'] = {'index': 0}

        print("OP", json.dumps(op, indent=5))

        return self._batchUpdate([op])

    def get(self):
        return self.get_forms().get(formId=self.gid).execute()

    def open(self):
        gbase.GoogleAPI.open(
                'https://{}/%s/edit#gid=0'.format(FORM_URL_BASE) %
                self.gid)

    def toFile(self):
        return gdrive.GFile(self.gid, self.name,
                            application=self.application)
