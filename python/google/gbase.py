import os
import sys

# External modules
sys.path.append(os.path.join(os.getenv('HOME'), 'lib', 'ext'))
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import webbrowser

API_DOMAIN = "www.googleapis.com"
API_URL = "https://{}".format(API_DOMAIN)


class GoogleAPI:
    def __init__(self, api, scopes, secret, application,
                 credentials=None, service=None,
                 credential_dir=None,
                 credential_path=None):
        self.api = api
        if not isinstance(scopes, list):
            scopes = (scopes)

        self.scopes = ["{}/{}".format(API_URL, s) for s in scopes]
        self.secret = secret
        self.application = application
        self.credentials = credentials
        self.credential_dir = credential_dir
        self.credential_path = credential_path
        if not self.credential_path:
            if 'GOOGLE_CREDS' in os.environ:
                self.credential_path = os.getenv('GOOGLE_CREDS', None)

        if self.credential_path:
            self.credential_dir = os.path.dirname(self.credential_path)
        elif not self.credential_dir:
            home_dir = os.path.expanduser('~')
            self.credential_dir = os.path.join(home_dir, '.credentials')

        self.service = service
        self.debug = os.getenv('GOOGLE_DEBUG', 'False') == 'True'

    def debugMsg(self, header, msg=""):
        if not self.debug:
            return

        print("--- {}: {}".format(header, msg))

    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        if self.credentials and not self.credentials.invalid:
            return self.credentials

        if not os.path.exists(self.credential_dir):
            os.makedirs(self.credential_dir)

        credential_path = self.credential_path
        if not credential_path:
            credential_file = \
                '{}.{}-python-{}.json'.format(
                    self.api, API_DOMAIN, self.application)
            self.debugMsg("Credential File", credential_file)

            credential_path = \
                os.path.join(self.credential_dir, credential_file)
        self.debugMsg("Credential Path", credential_path)

        store = Storage(credential_path)
        self.credentials = store.get()
        sys.argv = ['']
        if not self.credentials or self.credentials.invalid:
            self.debugMsg("Scopes", self.scopes)
            flow = client.flow_from_clientsecrets(
                self.secret, self.scopes)
            flow.user_agent = self.application
            self.credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)

        return self.credentials

    def open(self, url):
        webbrowser.open(url)
