#!/usr/bin/python3

"""
GitLab objects
"""

import sys
import os
import json
import logging
import urllib.parse
import re
import time
from inspect import isfunction

# External modules
sys.path.append(os.path.join(os.getenv('HOME'), 'lib', 'ext'))
import requests

# Personal modules
sys.path.append(os.path.join(os.getenv('HOME'), "lib", "config"))
from local_config import LocalConfigParser


class Config(LocalConfigParser):
    """
    Used to retrieve information for interfacing with the GitLab API
    
    Arguments:
        [name = 'gitlab.cfg'] -- The name of the configuration file to look for.
    """

    def __init__(self, name='gitlab.cfg'):
        LocalConfigParser.__init__(self, name)

    def _retrieve(self, section, option):
        if self.has_section(section) and self.has_option(section, option):
            return self.get(section, option).strip()

        return None

    def _get_base(self, option, var):
        result = self._retrieve('general', option)
        return result if result else os.getenv(var, '')

    def domain(self):
        return self._get_base('domain', 'GL_DOMAIN')

    def token(self):
        return self._get_base('token', 'GL_TOKEN')

    def trigger_token(self, project):
        if isinstance(project, int):
            p = Project(project, domain=self.domain())
            project = p.attr('path_with_namespace')

        section = 'project:{}'.format(project)
        result = self._retrieve(section, 'trigger_token')
        if result:
            return result

        for k, v in os.environ.items():
            m = re.search(r'^GL_PROJECT_(\d*)$', k)
            if m and v == project:
                pid = m.group(1)
                tk = "GL_TRIGGER_" + pid
                if tk in os.environ:
                    return os.environ[tk]

        return None


def _parseTrace(trace):
    """
    Used to parse trace information
    """
    others = []
    for line in trace.split("\n"):
        line = re.sub('^ *pipeline ', '', line)
        line = re.sub("'", '"', line)
        line = re.sub(": ", ":", line)
        line = re.sub(', "', ',"', line)
        line = re.sub(":False", ":false", line)
        line = re.sub(":True", ":true", line)
        line = re.sub(":None", ":null", line)

        try:
            obj = json.loads(line)
        except ValueError:
            continue

        others.append(obj)

    return others


def _download(response, output='archive'):
    """
    Used to download a file based on HTTP resonse
    """
    if response.status_code != 200:
        info = json.loads(response.text)
        msg = info['message'] if 'message' in info else "{} Unknown".format(response.status_code) 
        print("Unable to download ({})".format(msg))
        return 

    output += '.zip'
    print("Downloading ({}):".format(output), end='', flush=True)
    count = 0
    with open(output, 'wb') as f:
        for chunk in response.iter_content(chunk_size=2048):
            count += 1
            if count % 80 == 0:
                print(".", end='', flush=True)
            if chunk:
                f.write(chunk)

        f.close()
        print(" done!")


def _isCompleteStatus(status):
    """
    Simple test for evaluating a status as complete.
    """
    return True if status is None or status in ['success', 'failed'] \
            else False


_history_props = ['status', 'name', 'web_url', 'variables']


def _is_match(a, b):
    if isinstance(a, str) and isinstance(b, str):
        if a in b:
            return True
        if b in a:
            return True

        return False

    if isinstance(a, list) and isinstance(b, str):
        if b in a:
            return True

        if len([s for s in a if b in a]) > 0:
            return True

        return False

    if isinstance(a, str) and isinstance(b, list):
        return _is_match(b, a)

    return False


class Base:
    """
    The base GitLab class for interfacing with the GitLab WebAPI.

    Arguments:
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
        [access_token] -- The GitLab access token, will default to the local configuration.
    """

    def __init__(self, domain=None, preview=0, access_token=None):
        self.config = Config()
        if not domain:
            domain = self.config.domain()

        self.domain = domain
        self.preview = preview
        self.access_token = access_token

    def _debug_():
        try:
            import http.client as http_client
        except ImportError:
            import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1

        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger('requests.packages.urllib3')
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    def get(self, url, headers={}, data={}, stream=False, token=None):
        if self.preview:
            print("URL: {}".format(url))

        if not token:
            token = self._access_token()

        if not token:
            raise ValueError("Missing access token")

        if "token" not in headers:
            headers['PRIVATE-TOKEN'] = token

        return requests.get(url, headers=headers, data=data, stream=stream)

    def put(self, url, headers={}, data={}, stream=False, token=None):
        if self.preview:
            print("URL: {}".format(url))

        if not token:
            token = self._access_token()

        if not token:
            raise ValueError("Missing access token")

        if "token" not in headers:
            headers['PRIVATE-TOKEN'] = token

        return requests.put(url, headers=headers, data=data, stream=stream)

    def post(self, url, headers={}, data={}, token=None):
        if self.preview:
            print("URL: {}".format(url))

        if not token:
            token = self._access_token()

        if not token:
            raise ValueError("Missing access token")

        if "token" not in headers:
            headers['PRIVATE-TOKEN'] = token

        return requests.post(url, headers=headers, data=data)

    def delete(self, url, headers={}, token=None):
        if self.preview:
            print("URL: {}".format(url))

        if not token:
            token = self._access_token()

        if not token:
            raise ValueError("Missing access token")

        if "token" not in headers:
            headers['PRIVATE-TOKEN'] = token

        return requests.delete(url, headers=headers)

    def getJSON(self, url, headers={}, data={}, stream=False, token=None, 
                default=None):
        r = self.get(url, headers=headers, data=data, stream=stream, token=token)
        if r.status_code != 200:
            return default

        return json.loads(r.text)

    def download(self, url, output='archive', token=0):
        return _download(self.get(url, stream=True, token=token), output=output)

    def attr(self, name, info=None, token=None):
        """
        Returns the given attribute.
        """
        if not info:
            info = self.info(token=token)

        return info[name] if name in info else None

    def _user_attr(self, name, info=None, token=None):
        u = self.attr(name, info=info, token=None)
        if not u:
            return None

        return Users(domain=self.domain).toUser(u, token=token)

    def _users_attr(self, name, info=None, token=None):
        u = self.attr(name, info=info, token=None)
        if not u:
            return []

        users = Users(domain=self.domain)
        return [users.toUser(r, token=token) for r in u]

    def attrs(self, names, info=None, token=None):
        """
        Returns the given list of attributes.
        """
        if not info:
            info = self.info(token=token)

        result = {}
        for name in names:
            if name in info:
                result[name] = info[name]

        return result

    def _access_token(self):
        if self.access_token:
            return self.access_token

        return self.config.token()

    def _trigger_token(self, project):
        return self.config.trigger_token(project)

    def _api(self):
        return "{}/api/v4/projects".format(self.domain)

    def _project_api(self, project):
        return self._api() + "/{}".format(urllib.parse.quote_plus(str(project)))

    def _pipeline_api(self, project):
        return Base._project_api(self, project) + "/pipeline"

    def _pipelines_api(self, project):
        return Base._project_api(self, project) + "/pipelines"

    def _schedules_api(self, project):
        return Base._project_api(self, project) + "/pipeline_schedules"

    def _labels_api(self, project):
        return Base._project_api(self, project) + "/labels"

    def _issues_api(self, project):
        return Base._project_api(self, project) + "/issues"

    def _jobs_api(self, project):
        return Base._project_api(self, project) + "/jobs"

    def _bridges_api(self, project):
        return Base._project_api(self, project) + "/bridges"

    def _trigger_api(self, project):
        return Base._project_api(self, project) + "/trigger/pipeline"

    def _repository_api(self, project):
        return Base._project_api(self, project) + "/registry/repositories"

    def _merge_requests_api(self, project):
        return Base._project_api(self, project) + "/merge_requests"

    def _users_api(self):
        return "{}/api/v4/users".format(self.domain)

    def launch(self, project, ref, params={}, token=None):
        if not token:
            token = Base._trigger_token(self, project)

        if not token:
            raise ValueError("Missing trigger token")

        var = {"token": token, "ref": ref}
        for k in params:
            var["variables[{}]".format(k)] = params[k]

        url = Base._trigger_api(self, project)
        if (self.preview):
            print("URL: " + url)
            print("VARS: ", var)
            return {'id': -1}

        r = requests.post(url, data=var)
        return json.loads(r.text)

    def query(self, project, api_func=None, filter=None, info_func=None, params={}, token=None):
        results = []
        fields = {'page': 1, 'per_page': 10}
        select = set()
        user_base = {}
        users = Users(domain=self.domain, preview=self.preview, access_token=token)

        for k, v in params.items():
            if v == '@all' or (isinstance(v, list) and '@all' in v):
                continue

            if k == 'per_page':
                fields['per_page'] = v

            dtype = None
            if filter:
                if k not in filter:
                    select.add(k)
                    continue

                dtype = filter[k]
            else:
                select.add(k)

            if (not dtype or dtype == 'string'):
                if isinstance(v, str):
                    fields[k] = v
                elif isinstance(v, list) and len(v) == 1:
                    fields[k] = v[0]
            elif (not dtype or dtype == 'list'):
                if isinstance(v, str):
                    fields[k] = v
                elif isinstance(v, list):
                    fields[k] = ','.join(v)
            elif dtype == 'user':
                base = k
                if k.endswith('_id'):
                    base = k.replace('_id', '')
                    u = users.byId(v)
                else:
                    if k.endswith('name'):
                        base = k.replace('name', '')

                    u = users.bySearch(v)

                fields[k] = ','.join([str(uu.id()) for uu in u])
                select.add(k)
                user_base[k] = base
            elif isfunction(dtype):
                for kk, vv in dtype(params, k).items():
                    fields[kk] = vv

        url = api_func(self, project) if project else api_func(self)

        if (self.preview):
            print("URL: " + url)

        while(len(results) == 0 or
              ('per_page' in fields and
               len(results) < int(fields['per_page']))):
            if (self.preview):
                print("VARS: ", fields)
                break

            complete = True
            for res in self.getJSON(url, data=fields, token=token, default=[]):
                complete = False

                #print(json.dumps(res, indent=5))
                if res == 'error' or res == 'message':
                    return results

                keep = True
                for k in select:
                    if filter and k in filter:
                        t = filter[k]
                        if t == 'user':
                            if k in res:
                                continue

                            if not info_func:
                                continue

                            base = user_base[k]
                            info = info_func(self, project, res['id'], token=token)
                            if '@all' not in params[k]:
                                match = None
                                p = params[k]
                                for u in ['username', 'name', 'id']:
                                    if _is_match(info[base][u], p):
                                        match = u 

                                if not match:
                                    keep = False
                                    break

                            res[base] = info[base]['username']
                            res[base + '_name'] = info[base]['name']
                            res[base + '_id'] = info[base]['id']
                            continue

                    if isinstance(params[k], list) and '@all' not in params[k] and k in res:
                        v = res[k]
                        if isinstance(k, str):
                            if v not in params[k]:
                                keep = False
                                break

                        elif isinstance(k, list):
                            p = set(params[k])
                            if len(p - set(res[k])) != len(p): 
                                keep = False
                                break

                if not keep:
                    continue
            
                # If the VARIABLES are something to filter on.
                if 'variables' in params:
                    variables = Base.variables(self, project, res['id'],
                                               token=token)
                    if 'message' in variables:
                        print("Error. {}".format(variables['message']))
                        return

                    res['variable_names'] = []
                    res['variable_values'] = {}
                    count = 0

                    for name in variables:
                        res['variable_names'].append(name)
                        if name in params['variables']:
                            if params['variables'][name] is False:
                                count = 0
                                break

                            if params['variables'][name] is True or \
                               params['variables'][name] == variables[name]:
                                count += 1

                            res['variable_values'][name] = variables[name]

               
                    if count != len(params['variables']):
                        continue

                results.append(res)
                if 'per_page' in fields and \
                        len(results) >= int(fields['per_page']):
                    break

            fields['page'] += 1

            if complete:
                break

        return results

    def project(self, project, token=None):
        url = "{}".format(Base._project_api(self, project))
        return self.getJSON(url, token=token, default={})

    def pipeline(self, project, pipeline_id, token=None):
        url = "{}/{}".format(Base._pipelines_api(self, project),
                             pipeline_id)
        return self.getJSON(url, token=token, default={})

    def schedule(self, project, schedule_id, token=None):
        url = "{}/{}".format(Base._schedules_api(self, project),
                             schedule_id)
        return self.getJSON(url, token=token, default={})

    def issue(self, project, issue_id, token=None):
        url = "{}/{}".format(Base._issues_api(self, project),
                             issue_id)
        return self.getJSON(url, token=token, default={})

    def job(self, project, job_id, token=None):
        url = "{}/{}".format(Base._jobs_api(self, project),
                             job_id)
        return self.getJSON(url, token=token, default={})

    def bridge(self, project, bridge_id, token=None):
        url = "{}/{}".format(Base._bridges_api(self, project),
                             bridge_id)
        return self.getJSON(url, token=token, default={})

    def job_query(self, project, criteria={}, token=None):
        url = Base._jobs_api(self, project)

        id_min = None
        if 'id_min' in criteria:
            id_min = criteria['id_min']
            del criteria['id_min']

        id_max = None
        if 'id_max' in criteria:
            id_max = criteria['id_max']
            del criteria['id_max']

        jobs = []
        for j in self.getJSON(url, token=token, default=[]):
            id = j['id']
            if id_min and id_min > id:
                return jobs
            if id_max and id_max < id:
                continue

            valid = True
            for k, v in criteria.items():
                if k in j:
                    if j[k] == v:
                        continue

                valid = False
                break

            if not valid:
                continue

            jobs += [j]

        return jobs
    
    def variables(self, project, pipeline_id, token=None):
        url = "{}/{}/variables".format(Base._pipelines_api(self, project),
                                       pipeline_id)
        results = {}
        for v in self.getJSON(url, token=token, default={}):
            results[v['key']] = v['value']

        return results

    def merge_requests(self, project, params={}, token=None):
        url = "{}".format(Base._merge_requests_api(self, project))
        return self.getJSON(url, data=params, token=token, default={})

    def merge_request(self, project, merge_request_iid, token=None):
        url = "{}/{}".format(Base._merge_requests_api(self, project), merge_request_iid)
        return self.getJSON(url, token=token, default={})

    def user(self, user_id, token=None):
        url = "{}/{}".format(Base._users_api(self),
                             user_id)
        return self.getJSON(url, token=token, default={})

    def artifactByFileName(self, project, job_id, filename, output=None, token=None):
        url = "{}/{}/artifacts/{}".format(
            Base._jobs_api(self, project),
            job_id, filename)

        if not output:
            r = self.get(url, token=token)
            if r.status_code != 200:
                print("URL", url)
                return {} 

            return json.loads(r.text)
        else:
            self.download(url, output=output, token=token)
        
    def artifactsById(self, project, job_id, output=None, token=None):
        if not output:
            info = Base.job(self, project, job_id)
            name = info['name'] if 'name' in info else 'default'
            output = name

        url = "{}/{}/artifacts".format(
                Base._jobs_api(self, project),
                job_id)
        self.download(url, output=output, token=token)

    def artifactsByName(self, project, branch, job_name, output=None, token=None):
        if not branch:
            info = Base.project(self, project)
            branch = info['default_branch'] if 'default_branch' in info else 'master'

        if not output:
            output = job_name

        url = "{}/jobs/artifacts/{}/download?job={}".format(
                Base._project_api(self, project),
                branch,
                urllib.parse.quote_plus(str(job_name)))
        self.download(url, output=output, token=token)

    def jobs(self, project, pipeline_id, token=None):
        url = "{}/{}/jobs".format(Base._pipelines_api(self, project),
                                  pipeline_id)
        result = self.getJSON(url, token=token, default=[])
        result.sort(key=lambda x: x["id"])
        return result

    def bridges(self, project, pipeline_id, token=None):
        url = "{}/{}/bridges".format(Base._pipelines_api(self, project),
                                  pipeline_id)
        result = self.getJSON(url, token=token, default=[])
        result.sort(key=lambda x: x["id"])
        return result

    def trace(self, project, job_id, token=None):
        url = Base._project_api(self, project) + "/jobs/{}/trace".format(job_id)
        return self.get(url, token=token).text

    def repositories(self, project, params={}, token=None):
        url = Base._repository_api(self, project) + "/"
        return self.getJSON(url, data=params, token=token)

    def users(self, params={}, token=None):
        url = Base._users_api(self) + "/"
        return self.getJSON(url, data=params, token=token)


class Users(Base):
    """
    The class for interfacing with the GitLab Users.

    Arguments:
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
        [access_token] -- The GitLab access token, will default to the local configuration.    
    """

    def __init__(self, domain=None, preview=0, access_token=None):
        super().__init__(domain, preview, access_token)

    def __rep__(self):
        return "<Users {}>".format(self.domain)

    def __str__(self):
        return self.__rep__()

    def query(self, api_func=Base._users_api, params={}, token=None):
        """
        Function for querying users.
        """
        return Base.query(self, None, api_func=api_func, params=params, token=token)

    def toUser(self, u, token=None):
        """
        Used to convert a user record into a User class.
        """
        return User(u['id'], domain=self.domain, preview=self.preview, access_token=token)

    def byId(self, user_id, token=None):
        """
        Used to look up a user by ID.
        """
        users = self.query(params={'id': user_id})
        return self.toUser(users[0], token=token) if len(users) else None 

    def byUsername(self, username, token=None):
        """
        Used to look up a user by Username.
        """
        users = self.query(params={'username': username})
        return self.toUser(users[0], token=token) if len(users) else None 

    def bySearch(self, search, token=None):
        """
        Used to look up users by a search criteria.
        """
        users = self.query(params={'search': search})
        return [self.toUser(u, token=token) for u in users] 


class User(Base):
    """
    A class for interfacing with a single GitLab User. 
    
    Arguments:
        user_id -- The unique id of the User in GitLab.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
        [access_token] -- The GitLab access token, will default to the local configuration.
    """

    def __init__(self, user_id, domain=None, preview=0, access_token=None):
        self.user_id = user_id
        super().__init__(domain, preview, access_token)

    def __rep__(self):
        info = self.info()
        return "<User {} '{}' ({})>".format(self.user_id,
                                            self.name(info=info),
                                            self.username(info=info))

    def __str__(self):
        return self.__rep__()

    def id(self):
        """
        To retrieve the user id.
        """
        return self.user_id

    def info(self, token=None):
        """
        To retrieve the entire user record from GitLab.
        """
        return Base.user(self, self.user_id, token=None)

    def name(self, info=None, token=None):
        """
        Returns the name of the user.
        """
        return self.attr('name', info=info, token=token)

    def username(self, info=None, token=None):
        """
        Returns the username of the user.
        """
        return self.attr('username', info=info, token=token)

    def emails(self, token=None):
        """
        Returns the emails of the user.
        """
        url = "{}/{}/emails".format(Base._users_api(self), self.user_id)
        return self.getJSON(url, token=token)

    def email(self, info=None, token=None):
        """
        Returns the public email of the user.
        """
        return self.attr('public_email', info=info, token=token)

    def state(self, info=None, token=None):
        """
        Returns the state of the user.
        """
        return self.attr('state', info=info, token=token)


class Project(Base):
    """
    A class for interfacing with a single GitLab project.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
        [access_token] -- The GitLab access token, will default to the local configuration.
    """

    def __init__(self, project, domain=None, preview=0, access_token=None):
        self.project = project
        super().__init__(domain, preview, access_token)

    def __rep__(self):
        return "<Project {} '{}'>".format(self.id(),
                                          self.name())

    def __str__(self):
        return self.__rep__()

    def _project_api(self):
        """
        Returns the project API url specific to this project
        """
        return Base._project_api(self, self.project)

    def _pipeline_api(self):
        """
        Returns the pipeline API url specific to this project
        """
        return Base._pipeline_api(self, self.project)

    def _pipelines_api(self):
        """
        Returns the pipelines API url specific to this project
        """
        return Base._pipelines_api(self, self.project)

    def _labels_api(self):
        """
        Returns the labels API url specific to this project
        """
        return Base._labels_api(self, self.project)

    def _issues_api(self):
        """
        Returns the issues API url specific to this project
        """
        return Base._issues_api(self, self.project)

    def _schedules_api(self):
        """
        Returns the schedules API url specific to this project
        """
        return Base._schedules_api(self, self.project)

    def _jobs_api(self):
        """
        Returns the jobs API url specific to this project
        """
        return Base._jobs_api(self, self.project)

    def _trigger_api(self):
        """
        Returns the trigger API url specific to this project
        """
        return Base._trigger_api(self, self.project)

    def _repository_api(self):
        """
        Returns the repository API url specific to this project
        """
        return Base._repository_api(self, self.project)

    def _merge_request_api(self):
        """
        Returns the merge request API url specific to this project
        """
        return Base._merge_request_api(self, self.project)

    def _merge_requests_api(self):
        """
        Returns the merge requests API url specific to this project
        """
        return Base._merge_requests_api(self, self.project)

    def info(self, token=None):
        """
        Used to retrieve the GitLab record for a project. 
        """
        return Base.project(self, self.project, token=token)

    def id(self, info=None, token=None):
        """
        Used to retrieve the id.
        """
        return self.attr('id', info=info, token=token)

    def name(self, info=None, token=None):
        """
        Used to retrieve the name.
        """
        return self.attr('path_with_namespace', info=info, token=token)

    def launch(self, ref, params={}, token=None):
        """
        Used to launch a pipeline. 
        """
        r = Base.launch(self, self.project, ref, params=params, token=token)
        return Pipeline(self.project, r['id'], self.domain, self.preview)

    def query(self, api_func=Base._pipelines_api, params={}, token=None):
        """
        Used to query pipelines. 
        """
        filter = {'status': 'string',
                  'user_id': 'user',
                  'user': 'user' }
        self.preview = False;#True
        return Base.query(self, self.project,
                          api_func=api_func, filter=filter, info_func=Base.pipeline,
                          params=params, token=token)

    def pipeline(self, pipeline_id, token=None):
        """
        Used to retrieve a pipeline by ID. 
        """
        return Pipeline(self.project, pipeline_id, self.domain, self.preview)

    def labels(self, token=None):
        """
        Used to retrieve all the labels
        """
        url = self._labels_api()
        return self.getJSON(url, token=token, default={})

    def issues(self, token=None):
        """
        Used to retrieve all issues
        """
        url = self._issues_api()
        return self.getJSON(url, token=token, default={})

    def issue(self, issue_id, token=None):
        """
        Used to retrieve a schedule by ID.
        """
        return Issue(self.project, issue_id, self.domain, self.preview)

    def schedules(self, token=None):
        """
        Used to retrieve all schedules. 
        """
        url = self._schedules_api()
        return self.getJSON(url, token=token, default={})

    def schedule(self, schedule_id, token=None):
        """
        Used to retrieve a schedule by ID. 
        """
        return Schedule(self.project, schedule_id, self.domain, self.preview)

    def job(self, job_id, token=None):
        """
        Used to retrieve a job by ID. 
        """
        return Job(self.project, self.pipeline_id, job_id, self.domain, self.preview)

    def variables(self, pipeline_id, token=None):
        """
        Used to retrieve all the variables for a given pipeline.
        """
        return Base.variables(self, self.project, pipeline_id, token=token)

    def artifactByFileName(self, job_id, filename, output=None, token=None):
        """
        Used to retrieve specific artifact
        """
        return Base.artifactByFileName(self, self.project, job_id,
                                       filename,
                                       output=output,
                                       token=token)
    
    def artifactsById(self, job_id, output=None, token=None):
        """
        Used to retrieve artifacts by ID.
        """
        return Base.artifactsById(self, self.project, job_id,
                                  output=output,
                                  token=token)

    def artifactsByName(self, branch, job_name, output=None, token=None):
        """
        Used to retrieve artifacts by name.
        """
        return Base.artifactsByName(self, self.project, branch, job_name,
                                    output=output,
                                    token=token)

    def jobs(self, pipeline_id, token=None):
        """
        Used to list all the jobs for a given pipeline.
        """
        jobs = Base.jobs(self, self.project, pipeline_id, token=token)
        return [Job(self.project,
                pipeline_id, job['id'],
                self.domain, self.preview) for job in jobs]
 
    def job_query(self, criteria={}, token=None):
        """ 
        Used to query jobs
        """
        jobs = Base.job_query(self, self.project, criteria=criteria, token=token)
        return [Job(self.project,
                job['pipeline']['id'], job['id'],
                self.domain, self.preview) for job in jobs]

    def bridges(self, pipeline_id, token=None):
        """
        Used to list all the bridges for a given pipeline.
        """
        bridges = Base.bridges(self, self.project, pipeline_id, token=token)
        return [Bridge(self.project,
                pipeline_id, bridge['id'],
                self.domain, self.preview, info=bridge) for bridge in bridges]
 
    def trace(self, job_id, token=None):
        """
        Used to trace a job and find all nested pipelines/jobs. 
        """
        return Base.trace(self, self.project, job_id, token=token)

    def repositories(self, params={}, token=None):
        """
        Used to search a project for all related repositories.
        """
        return Base.repositories(self, self.project, params=params, token=token)

    def _toMergeRequest(self, record):
        return MergeRequest(self.project, record['iid'], domain=self.domain, preview=self.preview)

    def _toMergeRequests(self, records):
        records.sort(key=lambda m: m['iid'])
        return [self._toMergeRequest(r) for r in records]

    def mergeRequests(self, params={}, token=None):
        """
        Used to search a project for all related merge requests.
        """
        r = Base.merge_requests(self, self.project, params=params, token=token)
        return self._toMergeRequests(r)


class Pipelines(Project):
    """
    A class for interfacing with GitLab Pipelines.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        [trigger_token] -- The GitLab trigger token, will default to the local configuration.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
        [access_token] -- The GitLab access token, will default to the local configuration.
    """

    def __init__(self, project, trigger_token=None, domain=None, preview=0):
        self._trigger_token = trigger_token
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<Pipelines on {}>".format(Project(self.project, domain=self.domain).name())

    def __str__(self):
        return self.__rep__()

    def launch(self, ref, params={}, token=None):
        """
        Launches a new pipeline based on given parameters and reference.
        """
        if not token:
            token = self._trigger_token

        return Project.launch(self, ref, params=params, token=token)

    def query(self, params={}, token=None):
        """
        Performs a search of all existing Pipelines based on given parameters.
        """
        return Project.query(self, params=params, token=token)

    def jobs(self, pipeline_id, token=None):
        """
        Returns all jobs from a specific Pipeline.
        """
        return Project.jobs(self, pipeline_id, token=token)

    def bridges(self, pipeline_id, token=None):
        """
        Returns all bridges from a specific Pipeline.
        """
        return Project.bridges(self, pipeline_id, token=token)


class Pipeline(Project):
    """
    A class for interfacing with a single GitLab Pipeline.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        pipeline_id -- The unique ID of a GitLab pipeline.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """

    def __init__(self, project, pipeline_id, domain=None, preview=0):
        self.pipeline_id = pipeline_id
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<Pipeline {} on {}>".format(self.pipeline_id,
                                            Project(self.project, domain=self.domain).name())

    def __str__(self):
        return self.__rep__()

    def id(self):
        """
        Returns the unique ID of the Pipeline.
        """
        return self.pipeline_id

    def jobs(self, token=None):
        """
        Returns the jobs related to the Pipline.
        """
        return Project.jobs(self, self.pipeline_id, token=token)

    def bridges(self, token=None):
        """
        Returns the bridges related to the Pipline.
        """
        return Project.bridges(self, self.pipeline_id, token=token)

    def jobIds(self, token=None):
        """
        Returns the unique IDs of the jobs related to the Pipeline.
        """
        return [job.job_id for job in self.jobs(token)]

    def trace(self, job_id, token=None):
        """
        Returns the tracing history of the Pipeline.
        """
        return Project.trace(self, job_id, token=token)

    def variables(self, token=None):
        """
        Returns the variables used in the Pipeline.
        """
        return Project.variables(self, self.pipeline_id, token=token)

    def info(self, token=None):
        """
        Returns the GitLab record of the Pipeline.
        """
        return Base.pipeline(self, self.project, self.pipeline_id)

    def user(self, info=None, token=None):
        """
        Returns the user that launched the Pipeline.
        """
        return self._user_attr('user', info=info, token=token)

    def attr(self, name, info=None, token=None):
        """
        Returns the given attribute from the Pipeline.
        """
        if name in 'variables':
            return self.variables(token=token)

        return Base.attr(self, name, info=info, token=token)

    def attrs(self, names, token=None):
        """
        Returns the given list of attributes from the Pipeline.
        """
        result = {}
        if 'variables' in names:
            result['variables'] = self.variables(token=token)
            if len(names) == 1:
                return result

        result.update(Base.attrs(self, names, token=token))

        return result

    def status(self, info=None, token=None):
        """
        Returns the status of the Pipeline.
        """
        return self.attr('status', info=info, token=token)

    def pipelines(self, token=None):
        """
        Returns all the Pipelines that result from this one.
        """
        result = []
        for job in self.jobs(token=token):
            result += job.pipelines()

        return result

    def overallStatus(self, token=None):
        """
        Returns the overall status of this Pipeline and any sub-Pipelines.
        """
        status = self.status(token=token)
        if status != "success":
            return status

        for j in self.jobs():
            status = j.overallStatus(token=token)
            if status != "success":
                return status

        return status

    def hierarchy(self, props=None, token=None):
        """
        Report the hierachy of the Pipeline.
        """
        info = {'id': self.pipeline_id, 'jobs': []}

        if props:
            info.update(self.attrs(props, token=token))

        for job in self.jobs(token=token):
            info['jobs'].append(job.hierarchy(props=props, token=token))

        for bridge in self.bridges(token=token):
            i = bridge.info()
            #print("BRIDGE", self, json.dumps(i, indent=4))
            if 'downstream_pipeline' not in i:
                continue

            if not isinstance(i['downstream_pipeline'], dict):
                continue

            if 'id' not in i['downstream_pipeline']:
                continue

            dpid = i['downstream_pipeline']['id']
            dpipeline = Pipeline(self.project, dpid,
                         self.domain, self.preview)
            for job in dpipeline.jobs(token=token):
                h = job.hierarchy(props=props, token=token)
                if 'pipelines' in h:
                    h['pipelines'].append(dpid)
                info['jobs'].append(h)

        return info

    def history(self, token=None):
        """
        Report the history of the Pipeline.
        """
        return self.hierarchy(_history_props, token=token)

    def artifactByFileName(self, job_id, filename, output=None, token=None):
        """
        Get a specific artifact by name
        """
        return Project.artifactByFileName(self, job_id, filename, output=output, token=token)
    
    def artifactsById(self, job_id, output=None, token=None):
        """
        Download all artifacts of a specific Job in the Pipeline.
        """
        Project.artifactsById(self, job_id, output=output, token=token)

    def artifacts(self, output='archive.{}', token=None):
        """
        Download all artifacts created by Jobs in the Pipeline.
        """
        for j in self.jobs():
            self.artifactsById(j.job_id, output=output.format(j.job_id), token=token)

    def wait(self, token=None):
        """
        Pause until the overall status is complete.
        """
        while True:
            if _isCompleteStatus(self.status()):
                break

            time.sleep(3)

        for pipeline in self.pipelines():
            pipeline.wait()


class Job(Pipeline):
    """
    A class for interfacing with a single GitLab Job.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        pipeline_id -- The unique ID of a GitLab pipeline.
        job_id -- The unique ID of a GibLab job.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """

    def __init__(self, project, pipeline_id, job_id, domain=None, preview=0):
        self.job_id = job_id
        super().__init__(project, pipeline_id, domain, preview)

    def __rep__(self):
        return "<Job {}/'{}' on {}>".format(self.job_id,
                                            self.name(),
                                            Project(self.project, domain=self.domain).name())

    def __str__(self):
        return self.__rep__()

    def id(self):
        """
        Returns the unique ID of the Job.
        """
        return self.job_id

    def info(self, token=None):
        """
        Returns the GitLab record of the Job.
        """
        return Base.job(self, self.project, self.job_id, token=token)

    def name(self, info=None, token=None):
        """
        Returns the name of the Job.
        """
        return self.attr('name', info=info, token=token)

    def status(self, info=None, token=None):
        """
        Returns the status of the Job.
        """
        return self.attr('status', info=info, token=token)

    def overallStatus(self, token=None):
        """
        Returns the overall status of this Job and all sub-Jobs.
        """
        status = self.status(token=token)
        if status != "success":
            return status

        for p in self.pipelines(token=token):
            status = p.overallStatus(token=token)
            if status != "success":
                return status

        return "success"

    def trace(self, token=None):
        """
        Returns the tracing history of the Job.
        """
        return Pipeline.trace(self, self.job_id, token=token)
    
    def artifactByFileName(self, filename, token=None):
        """
        Download specific artifact created by this Job.
        """
        return Pipeline.artifactByFileName(self, self.job_id, filename, token=token)

    def artifacts(self, output='archive', token=None):
        """
        Download all artifacts created by this Job.
        """
        return Pipeline.artifactsById(self, self.job_id, output=output, token=token)

    def pipelines(self, token=None):
        """
        Returns all the Pipelines that result from this Job.
        """
        result = []
        for item in _parseTrace(self.trace(token=token)):
            if 'id' not in item or 'project_id' not in item:
                continue

            pipeline_id = item['id']
            project_id = item['project_id']
            p = Pipeline(project_id, pipeline_id,
                         self.domain, self.preview)
            result.append(p)

        return result

    def hierarchy(self, props=None, token=None):
        """
        Report the hierarchy of the Job.
        """
        info = {'id': self.job_id, 'name': self.name(), 'pipelines': []}
        if props:
            info.update(self.attrs(props, token=token))

        for pipeline in self.pipelines(token=token):
            h = pipeline.hierarchy(props=props, token=token)
            info['pipelines'].append(h)

        return info

    def history(self, token=None):
        """
        Report the history of the Job.
        """
        return self.hierarchy(_history_props, token=token)

    def wait(self):
        """
        Pause until the status of the job is complete.
        """
        while True:
            if _isCompleteStatus(self.status()):
                break

            time.sleep(3)


class Bridge(Pipeline):
    """
    A class for interfacing with a single GitLab Bridge.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        pipeline_id -- The unique ID of a GitLab pipeline.
        bridge_id -- The unique ID of a GibLab bridge.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """

    def __init__(self, project, pipeline_id, bridge_id, domain=None, preview=0, info=None):
        self.bridge_id = bridge_id
        super().__init__(project, pipeline_id, domain, preview)
        self._info = info

    def __rep__(self):
        return "<Bridge {}/'{}' on {}>".format(self.bridge_id,
                                            self.name(),
                                            Project(self.project, domain=self.domain).name())

    def __str__(self):
        return self.__rep__()

    def id(self):
        """
        Returns the unique ID of the Bridge.
        """
        return self.bridge_id

    def info(self, token=None):
        """
        Returns the GitLab record of the Bridge.
        """
        return self._info #Base.bridge(self, self.project, self.bridge_id, token=token)

    def name(self, info=None, token=None):
        """
        Returns the name of the Bridge.
        """
        return self.attr('name', info=info, token=token)


class Schedule(Project):
    """
    A class for interfacing with a single GitLab Schedule.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        schedule_id -- The unique ID of a GitLab schedule.
        job_id -- The unique ID of a GibLab job.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """
    
    def __init__(self, project, schedule_id, domain=None, preview=0):
        self.schedule_id = schedule_id
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<Schedule {} on {}>".format(self.schedule_id,
                                            Project.name(self))

    def jobs(self, token=None):
        return Project.jobs(self, self.schedule_id, token=token)

    def info(self, token=None):
        """
        Retrieve the GitLab record.
        """
        return Base.schedule(self, self.project, self.schedule_id)

    def description(self, info=None, token=None):
        """
        Retrieve the schedule description.
        """
        return self.attr('description', info=info, token=token)

    def reference(self, info=None, token=None):
        """
        Retrieve the schedule reference.
        """
        return self.attr('ref', info=info, token=token)

    def owner(self, info=None, token=None):
        """
        Retrieve the owner.
        """
        return self._user_attr('owner', info=info, token=token)

    def pipeline(self, info=None, token=None):
        """
        Retrieves the last Pipeline that resulted from this Schedule.
        """
        p = self.attr('last_pipeline', info=info, token=token)
        if p:
            return Pipeline(self.project, p['id'], self.domain, self.preview)

        return None

    def variables(self, info=None, token=None):
        """
        Retrieves the variables for the Schedule.
        """
        result = {}
        r = info if info else self.info()
        if 'variables' in r:
            for v in r['variables']:
                result[v['key']] = v['value']

        return result

    def add(self, key, value, token=None, quiet=False):
        url = "{}/{}/variables".format(Base._schedules_api(self, self.project), self.schedule_id)
        response = self.post(url, data={'key': key, 'value': value}, token=token)
        if response.status_code != 201 and not quiet:
            info = json.loads(response.text)
            msg = info['message'] if 'message' in info else "{} Unknown".format(response.status_code) 
            print("Unable to add variable {} ({})".format(key, msg))
            return 

    def delete(self, key, token=None, quiet=False):
        url = "{}/{}/variables/{}".format(Base._schedules_api(self, self.project), self.schedule_id, key)
        response = Base.delete(self, url, token=token)
        if response.status_code != 202 and not quiet:
            info = json.loads(response.text)
            msg = info['message'] if 'message' in info else "{} Unknown".format(response.status_code) 
            print("Unable to remove variable {} ({})".format(key, msg))
            return 


class Issues(Project):
    """
    A class for interfacing with GitLab Issues

    Arguments:
        project -- The unique name or ID of a project in GitLab
        [domain] -- The GitLab domain, will default to the local configuration
        [preview = 0] -- Whether to display the access operations and not actually perform any communication
        [access_token] -- The GitLab access token, will default to the local configuration.
    """

    def __init__(self, project, domain=None, preview=0):
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<Issues on {}>".format(Project.name(self))

    def __str__(self):
        return self.__rep__()

    def query(self, params={}, token=None):
        """
        Performs a search of all existing Issues based on given parameters.
        """
        def process(params, k):
            return {'search': params[k],
                    'in': k}

        filter = {'assignee': 'user_id',
                  'assignee_name': 'user_name',
                  'author': 'user_id',
                  'author_name': 'user_name',
                  'confidential': 'boolean',
                  'created_after': 'date',
                  'due_date': 'date',
                  'state': 'string',
                  'labels': 'list',
                  'title': process 
                  }
        return Base.query(self, self.project,
                          api_func=Base._issues_api, 
                          filter=filter, info_func=Base.issue,
                          params=params, token=token)


class Issue(Project):
    """
    A class for interfacing with a single GitLab Issue.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        issue_id -- The unique ID of a GitLab issue.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication
    """

    def __init__(self, project, issue_id, domain=None, preview=0):
        self.issue_id = issue_id
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<Issue {} on {}>".format(self.issue_id, Project.name(self))

    def api(self):
        return "{}/{}".format(Base._issues_api(self, self.project), self.issue_id)

    def notes_api(self):
        return "{}/notes".format(self.api())

    def info(self, token=None):
        """
        Retrieve the GitLab record
        """
        return Base.issue(self, self.project, self.issue_id)

    def description(self, info=None, token=None):
        """
        Retrieve the issue description
        """
        return self.attr('description', info=info, token=token)

    def owner(self, info=None, token=None):
        """
        Retrieve the owner.
        """
        return self._user_attr('owner', info=info, token=token)

    def state(self, info=None, token=None):
        """
        Retrieve the state
        """
        return self.attr('state', info=info, token=token)

    def labels(self, info=None, token=None):
        """
        Retrieve the labels
        """
        return self.attr('labels', info=info, token=token)

    def notes(self, token=None):
        return self.postJSON(self.notes_api())

    def add_note(self, note, token=None, quiet=False):
        url = self.notes_api() 
        if isinstance(note, str):
            note = {'body': note}

        response = self.post(url, data=note, token=token)
        if response.status_code != 201 and not quiet:
            info = json.loads(response.text)
            msg = info['message'] if 'message' in info else '{} Unknown'.format(response.status_code)
            print("Unable to add note to issue {} ({})".format(self.issue_id, msg))
            return False

        return True

    def edit(self, operations, token=None, quiet=False):
        url = self.api() 
        response = self.put(url, data=operations, token=token)
        if response.status_code != 200 and not quiet:
            info = json.loads(response.text)
            msg = info['message'] if 'message' in info else '{} Unknown'.format(response.status_code)
            print("Unable to edit issue {} ({})".format(self.issue_id, msg))
            return False

        return True

    def add_label(self, label, token=None):
        """
        Add a new label
        """
        return self.edit({'add_labels', label}, token=token)

    def remove_label(self, label, token=None):
        """
        Remove a label
        """
        return self.edit({'remove_labels', label}, token=token)

    def reassign(self, user, ops={}, token=None):
        users = Users(domain=self.domain,
                      preview=self.preview,
                      access_token=token) 
        u = users.bySearch(user) 
        if len(u) != 1:
            print("Could not resolve {} to a single user".format(user))
            return
    
        ops['assignee_id'] = u[0].id();
        note = "Assigned to {}".format(u[0].name())
        return self.edit(ops, token=token) and self.add_note(note, token=token)


class Repositories(Project):
    """
    A class for interfacing with the GitLab Repositories.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """

    def __init__(self, project, domain=None, preview=0):
        self.project = project
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<Repositories on {}>".format(self.name())

    def __str__(self):
        return self.__rep__()

    def repositories(self, params={}, token=None):
        """
        Retrieves the repositories that match the given search parameters.
        """
        return Project.repositories(self, params, token=token)

    def names(self, token=None):
        """
        Retrieve the names of all images stored in the repository.
        """
        names = []
        info = self.repositories({"tags": True}, token)
        for i in info:
            if "tags" in i:
                for t in i["tags"]:
                    if "name" in t and t["name"] not in names:
                        names.append(t["name"])

        names.sort()
        return names


class MergeRequests(Project):
    """
    A class for interfacing with the GitLab Merge Requests.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        [trigger_token] -- The GitLab trigger token, will default to the local configuration.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """

    def __init__(self, project, trigger_token=None, domain=None, preview=0):
        self._trigger_token = trigger_token 
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<MergeRequests on {}>".format(self.name())

    def __str__(self):
        return self.__rep__()

    def query(self, params={}, token=None):
        """
        Perform a query of all Merge Requests.
        """
        r = Project.query(self, api_func=Base._merge_requests_api, params=params, token=token)
        return self._toMergeRequests(r)
  
    def requests(self, token=None):
        """
        Retrieve the current merge request.
        """
        r = Base.merge_requests(self, self.project, token=token)
        return self._toMergeRequests(r)


class MergeRequest(Project):
    """
    A class for interfacing with a single GitLab Merge Request.

    Arguments:
        project -- The unique name or ID of a project in GitLab.
        merge_request_iid -- The unique ID of the merge request.
        [domain] -- The GitLab domain, will default to the local configuration.
        [preview = 0] -- Whether to display the access operations and not actually perform any communication.
    """

    def __init__(self, project, merge_request_iid, domain=None, preview=0):
        self.merge_request_iid = merge_request_iid
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "<MergeRequest {} on {}>".format(self.merge_request_iid,
                                                self.name())

    def __str__(self):
        return self.__rep__()

    def id(self):
        """
        Returns the uniqe ID of the Merge Request.
        """
        return self.merge_request_iid

    def info(self, token=None):
        """
        Returns the GitLab record of the Merge Request.
        """
        return Project.merge_request(self, self.project, self.merge_request_iid)

    def author(self, info=None, token=None):
        """
        Returns the author of the Merge Request.
        """
        return self._user_attr('author', info=info, token=token)

    def assignee(self, info=None, token=None):
        """
        Returns the assignee of the Merge Request.
        """
        return self._user_attr('assignee', info=info, token=token)

    def assignees(self, info=None, token=None):
        """
        Returns the assignees of the Merge Request.
        """
        return self._users_attr('assignees', info=info, token=token)

    def reviewers(self, info=None, token=None):
        """
        Returns the reviewers of the Merge Request.
        """
        return self._users_attr('reviewers', info=info, token=token)
