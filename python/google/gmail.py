import gbase
import os
import re
from apiclient import discovery
import pkg_resources
import locale
import time
import json
import base64

MAIL_URL_BASE = "mail.google.com/mail/u/0/?tab=rm&ogbl#inbox/"
UNKNOWN_SUBJECT = 'Unknown'
UNREAD_LABEL = 'UNREAD'
DEFAULT_SCOPE = ".readonly"


def get_subject_from_payload(payload):
    for header in payload['headers']:
        if header['name'] == "Subject":
            return header['value']

    return None


def get_from_from_payload(payload):
    for header in payload['headers']:
        if header['name'] == "From":
            return header['value']

    return None


def get_to_from_payload(payload):
    for header in payload['headers']:
        if header['name'] == "Delivered-To":
            return header['value']

    return None


def decode_body(body):
    if 'size' in body and body['size'] > 0 and 'data' in body:
        return base64.urlsafe_b64decode(body['data'].encode("ASCII")).decode('utf-8')

    return ""


def get_body(data):
    message = ''

    if 'payload' in data:
        payload = data['payload']
        if 'parts' in payload:
            for p in payload['parts']:
                if "body" in p:
                    message += decode_body(p['body'])

        elif 'body' in payload:
            message += decode_body(payload['body'])

    else:
        message += data['snippet']

    return message


def is_unread_from_message(data):
    if 'labelIds' in data:
        if UNREAD_LABEL in data['labelIds']:
            return True

    return False


def resolveQ(param={}, q=None):
    if isinstance(param, str):
        param = {'q': param}
    elif isinstance(param, list):
        param = {'q': " ".join(param)}
    elif not isinstance(param, dict):
        print("NOT SUPPORTED", param)

    if q:
        if 'q' in param:
            param['q'] = "{} and {}".format(q, param['q'])
        else:
            param['q'] = q

    return param


def canonicalizeId(gid):
    match = re.match('^https?://{}([^/]+)'.format(MAIL_URL_BASE),
                     gid)
    if match:
        return match.groups()[0]

    return gid


class GMailBase(gbase.GoogleAPI):
    def __init__(self, scope, application="mail",
                 credentials=None, service=None):
        client_file = \
            pkg_resources.resource_filename(__name__, "mail_client_id.json")
        client_file = os.getenv("GOOGLE_MAIL_CLIENT_ID", client_file)

        scopes = [scope]
        gbase.GoogleAPI.__init__(
                self, "gmail",
                ["auth/gmail{}".format(s) for s in scopes],
                client_file, application,
                credentials=credentials,
                service=service)

    def get_service(self):
        if not self.service:
            self.service = discovery.build(self.api, 'v1',
                                           credentials=self.get_credentials())

        return self.service

    def get_users(self):
        return self.get_service().users()

    def get_labels(self):
        return self.get_users().labels()

    def get_threads(self, unrea=False):
        return self.get_users().threads()

    def get_messages(self):
        return self.get_users().messages()

    def get_resource(self, resource):
        if resource == "users":
            return self.get_service().users()
        elif resource == "labels":
            return self.get_service().users().labels()
        elif resource == "threads":
            return self.get_service().users().threads()
        elif resource == "messages":
            return self.get_service().users().messages()
        elif resource == "profile":
            return self.get_service().users().profile()
        else:
            print("Not supported: %s" % resource)
            exit(2)

        return None


class GItem(GMailBase):
    def __init__(self, scope=DEFAULT_SCOPE,
                 application="mail", credentials=None, service=None):
        GMailBase.__init__(self, scope,
                           application=application,
                           credentials=credentials,
                           service=service)

    def toLabel(self, item):
        label = GLabel(item['id'], item['name'],
                       application=self.application,
                       credentials=self.credentials,
                       service=self.service)
        label.debug = self.debug
        return label

    def toLabels(self, items):
        return [self.toLabel(i) for i in items]

    def toThread(self, item):
        thread = GThread(item['id'],
                         application=self.application,
                         credentials=self.credentials,
                         service=self.service)
        thread.debug = self.debug
        return thread

    def toThreads(self, items):
        return [self.toThread(i) for i in items]

    def toMessage(self, item):
        message = GMessage(item['id'],
                           application=self.application,
                           credentials=self.credentials,
                           service=self.service)
        message.debug = self.debug
        return message

    def toMessages(self, items):
        return [self.toMessage(i) for i in items]

    def getProfile(self):
        return self.get_users().getProfile(userId='me').execute()

    def getEmail(self):
        profile = self.getProfile()
        return profile['emailAddress'] if 'emailAddress' in profile else "<unknown>"


class GLabel(GItem):
    def __init__(self, gid, name,
                 scope=DEFAULT_SCOPE,
                 application=None, credentials=None, service=None):
        self.gid = gid
        self.name = name
        GItem.__init__(self,
                       scope=scope,
                       application=application,
                       credentials=credentials,
                       service=service)

    def getMessages(self):
        messages = GMail.search_messages(self, 'label:{}'.format(self.name))
        return self.toMessages(messages)

    def getThreads(self, unread=False):
        param = ['label:{}'.format(self.name)]
        if unread:
            param.append('is:unread')

        threads = GMail.search_threads(self, param)
        return self.toThreads(threads)

    def __str__(self):
        return "GLabel: {} ({})".format(self.name, self.gid)


class GThread(GItem):
    def __init__(self, gid,
                 scope=DEFAULT_SCOPE,
                 application=None, credentials=None, service=None):
        self.gid = gid
        GItem.__init__(self,
                       scope=scope,
                       application=application,
                       credentials=credentials,
                       service=service)

    def getData(self):
        return self.get_threads().get(userId='me', id=self.gid).execute()

    def getMessages(self, data=None):
        if not data:
            data = self.getData()

        return self.toMessages([m for m in data['messages']])

    def getFrom(self, data=None):
        if not data:
            data = self.getData()

        for m in data['messages']:
            value = get_from_from_payload(m['payload'])
            if value:
                return value

        return ""

    def getTo(self, data=None):
        if not data:
            data = self.getData()

        for m in data['messages']:
            value = get_to_from_payload(m['payload'])
            if value:
                return value

        return ""

    def getSubject(self, data=None):
        if not data:
            data = self.getData()

        for m in data['messages']:
            value = get_subject_from_payload(m['payload'])
            if value:
                return value

        return UNKNOWN_SUBJECT

    def isUnread(self, data=None):
        if not data:
            data = self.getData()

        if 'messages' in data:
            for m in data['messages']:
                if is_unread_from_message(m):
                    return True

        return False

    def getNum(self, data=None):
        if not data:
            data = self.getData()

        count = 0
        for m in data['messages']:
            msg = m['payload']
            count += len(msg['parts'])
        return count

    def markRead(self):
        GMail.get_threads(self).modify(userId='me', id=self.gid, body={'addLabelIds':[], 'removeLabelIds':[UNREAD_LABEL]}).execute()

    def markUnread(self):
        GMail.get_threads(self).modify(userId='me', id=self.gid, body={'addLabelIds':[UNREAD_LABEL], 'removeLabelIds':[]}).execute()
    
    def process(self, parserFunc):
        for m in self.getMessages():
            parserFunc(m)

    def __str__(self):
        data = self.getData()
        return "GThread: {} [{}] ({})".format(self.getSubject(data=data),
                                              self.getNum(data=data),
                                              self.gid)


class GMessage(GItem):
    def __init__(self, gid,
                 scope=DEFAULT_SCOPE,
                 application=None, 
                 credentials=None, 
                 service=None):
        self.gid = gid
        GItem.__init__(self,
                       scope=scope,
                       application=application,
                       credentials=credentials,
                       service=service)

    def getData(self):
        return self.get_users().messages().get(userId='me',
                                               id=self.gid).execute()

    def getSubject(self, data=None):
        if not data:
            data = self.getData()

        value = get_subject_from_payload(data['payload'])
        if value:
            return value

        return UNKNOWN_SUBJECT

    def getBody(self, data=None):
        if not data:
            data = self.getData()

        return get_body(data)

    def isUnread(self, data=None):
        if not data:
            data = self.getData()

        return is_unread_from_message(data)

    def getThread(self):
        return GMail.search_messages(self, ['label:{}'.format(self.name)])

    def getLabels(self):
        return GMail.search_messages(self, ['label:{}'.format(self.name)])

    def markRead(self):
        GMail.get_messages().modify(userId='me', id=self.gid, body={'addLabelIds':[], 'removeLabelIds':[UNREAD_LABEL]}).execute()

    def markUnread(self):
        GMail.get_messages().modify(userId='me', id=self.gid, body={'addLabelIds':[UNREAD_LABEL], 'removeLabelIds':[]}).execute()

    def __str__(self):
        return "GMail: {} ({})".format(self.getSubject(), self.gid)


class GMail(GItem):
    def __init__(self,
                 scope=DEFAULT_SCOPE,
                 application=None,
                 credentials=None,
                 service=None):
        GItem.__init__(self,
                       scope=scope,
                       application=application,
                       credentials=credentials,
                       service=service)

    def labels(self):
        return self.toLabels(self.get_labels().list(userId='me').execute()['labels'])

    def findLabel(self, name):
        labels = GMail.search_labels(self)
        labels = [l for l in labels if l['name'] == name]
        return self.toLabels(labels)

    def search_basic(self, resource, param={}):
        param = resolveQ(param)

        param['userId'] = 'me'

        results = []
        page_token = None
        while True:
            self.debugMsg("search_basic:Resource:", resource)
            self.debugMsg("search_basic:Parameters:", param)
            response = self.get_resource(resource).list(**param).execute()
            page_token = response.get('nextPageToken', None)
            results.extend(response.get(resource, []))
            if page_token is None:
                break

            param['pageToken'] = page_token

        return results

    def search_messages(self, param={}):
        return GMail.search_basic(self, 'messages', param)

    def search_threads(self, param={}):
        return GMail.search_basic(self, 'threads', param)

    def search_labels(self, param={}):
        return GMail.search_basic(self, 'labels', param)

    def search_profile(self, param={}):
        return GMail.search_basic(self, 'profile', param)

    def init(self, name):
        if self.gid is not None:
            return self.gid

        sheet = dict(
            properties={
                'autoRecalc': 'ON_CHANGE',
                'title': name,
                'locale': locale.getlocale()[0],
                'timeZone': time.tzname[0]
            },
            sheets=[
                {
                    'properties': {
                        'gridProperties': {'columnCount': 26, 'rowCount': 200},
                        'index': 0,
                        'sheetId': 0,
                        'sheetType': 'GRID',
                        'title': self.application
                    }
                }])

        try:
            result = self.get_spreadsheets().create(
                body=sheet).execute()
            self.gid = result['spreadsheetId']
        except Exception as e:
            print(e)

        return None

    def update(self, values, rangeName="A1"):
        try:
            self.get_spreadsheets().values().update(
                spreadsheetId=self.gid,
                range=rangeName,
                valueInputOption='RAW',
                body={'values': values}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def append(self, values, rangeName="A1"):
        try:
            self.get_spreadsheets().values().append(
                spreadsheetId=self.gid,
                range=rangeName,
                valueInputOption='RAW',
                body={'values': values}).execute()
            return True
        except Exception as e:
            print(e)

        return False

    def retrieve(self, rangeName):
        try:
            result = self.get_spreadsheets().values().get(
                spreadsheetId=self.gid, range=rangeName).execute()
        except Exception as e:
            print(e)
            return None

        return result['values'] if 'values' in result else []

    def open(self):
        gbase.GoogleAPI.open(
                'https://{}/%s'.format(MAIL_URL_BASE) %
                self.gid)
