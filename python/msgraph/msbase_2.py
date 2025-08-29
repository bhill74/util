import os
import sys
import time
import requests
import json
import urllib.parse

# External modules
sys.path.append(os.path.join(os.getenv("HOME"), 'lib', 'ext'))
from msal import PublicClientApplication

import webbrowser

_TENANT_ID = 'common'
_AUTHORITY_URL = f'https://login.microsoftonline.com/{_TENANT_ID}/'
_TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{_TENANT_ID}/oauth2/v2.0/token"

_BASE_URL = 'https://graph.microsoft.com/v1.0/'

class Base:
    def __init__(self, debug=False):
        self.debug = debug

    def debug(self, flag):
        self.debug = flag
        
    def debugMsg(self, header, msg=""):
        if not self.debug:
            return

        print("--- {}: {}".format(header, msg))

    def errorMsg(self, msg=""):
        sys.stderr.write(msg +"\n")
              

class MSGraphApplication(Base):
    def __init__(self, application, debug=False):
        Base.__init__(self, debug)
        self.name = application
        self.path = os.path.dirname(__file__)
        self.info = None
        if 'MS_GRAPH_APP' in os.environ:
            self.path = os.environ['MS_GRAPH_APP']
            if not os.path.exists(self.path):
                self.errorMsg("Application file {} can not be found".format(self.path))
                return
        elif 'MS_GRAPH_APP_DIR' in os.environ:
            self.path = os.envrion['MS_GRAPH_APP_DIR']
            f = os.path.join(self.path, application + '.json')
            if os.path.exists(f):
                self.path = f
            else:
                self.errorMsg("No '{}' application found at {}".format(application, self.path))
                return
        else:
            f = os.path.join(self.path, application + '.json')
            if not os.path.exists(f):
                self.errorMsg("No '{}' application found at {}".format(application, self.path))
                return
            self.path = f
            
        with open(self.path, "r") as file:
            try:
                self.info = json.loads(file.read())
            except Exception as e:
                self.errorMsg("Application file '{}' could not be read\n{}".format(self.path, str(e)))

    def getName(self):
        return self.name
    
    def getID(self):
        return self.info['id'] if 'id' in self.info else None

    def getScopes(self):
        return self.info['scopes'] if 'scopes' in self.info else None
    

class MSGraphCredentials(Base):
    def __init__(self, debug=False):
        Base.__init__(debug)
        return
    
class MSGraphBase(Base):
    def __init__(self, application,
                 credentials=None, debug=False):
        Base.__init__(self, debug)
        if isinstance(application, str):
            self.application = MSGraphApplication(application)
        elif isinstance(application, MSGraphApplication):
            self.application = application
        else:
            self.errorMsg("No application provided")
            return
    
        self.credentials = credentials
        if not self.credentials:
            file = 'msgraph.{}.token.json'.format(self.application.getName())
            if 'MS_GRAPH_CREDENTIALS' in os.environ:
                file = os.environ['MS_GRAPH_CREDENTIALS']
            
            if os.path.exists(file):
                with open(file, 'r') as f:
                    self.credentials = json.loads(f.read())
    
            else:
                app = PublicClientApplication(self.application.getID(), authority=_AUTHORITY_URL)
                flow = app.initiate_device_flow(scopes=self.application.getScopes())
                print(flow)
                print(flow['message'])
                webbrowser.open_new_tab(flow['verification_uri'])

                start_time = time.time()
                expires_in = flow['expires_in']
                interval = 3
                while time.time() - start_time < expires_in:
                    time.sleep(interval)

                    token_payload = {
                        'grant_type': 'device_code',
                        'client_id': self.application.getID(),
                        'device_code': flow['device_code']
                    }

                    try:
                        token_response = requests.post(_TOKEN_ENDPOINT, data=token_payload)
                        token_data = token_response.json()

                        if 'access_token' in token_data:
                            print("\nAuthentication successful!");
                            with open(file, 'w') as f:
                                f.write(json.dumps(token_data))

                            self.credentials = token_data
                            break

                        elif token_data.get('error') == 'authorization_pending':
                            print("Authorization pending ... Waiting.")
                        elif token_data.get('error') == 'slow_down':
                            interval += 5
                        elif token_data.get('error') == 'access_denied':
                            print("Authentication denied")
                            break
                        elif token_data.get('error') == 'expired_token':
                            print("Device code expired")
                            break
                        else:
                            print(f"Unknown error during polling: {token_data.get('error_discription', json.dumps(token_data))}")
                            break
                    except requests.exceptions.RequestException as e:
                        print(f"Network error during token polling: {e}")
                        break
                    except json.JSONDecodeError:
                        print("Invalid JSON response from token endpoint during polling.")
                        break

    def token(self):
        return self.credentials['access_token'] if self.credentials and 'access_token' in self.credentials else ''
    
    def enpoint(self):
        return ''

    def get(self, endpoint='', props=None):
        headers = {'Authorization': 'Bearer ' + self.token() }
        url = _BASE_URL + self.endpoint() + endpoint
        if props:
            url += '?'
            for k, v in props.items():
                url += f"{k}=" + urllib.parse.quote_plus(v) + '&'
        
        self.debugMsg('URL', url)

        result = requests.get(url, headers=headers)
        self.debugMsg('Response Code', result.status_code)

        return result.json()
        
