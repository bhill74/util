#!/usr/bin/python3 

import os
import json
import requests
import urllib.parse
import re


class Pipeline:
    def __init__(self, domain=0, preview=0, access_token=0):
        if domain == 0:
            domain = os.environ["GL_DOMAIN"] if 'GL_DOMAIN' in os.environ \
                else 'https://gitlab.com'

        self.domain = domain
        self.preview = preview
        self._access_token = access_token

    def access_token(self):
        if self._access_token:
            return self._access_token

        return os.environ["GL_TOKEN"] if 'GL_TOKEN' in os.environ \
            else 'UNKNOWN'

    def trigger_token(project):
        for k, v in os.environ.items():
            m = re.search(r'^GL_PROJECT_(\d*)$', k)
            if m and v == project:
                pid = m.group(1)
                tk = "GL_TRIGGER_" + pid
                if tk in os.environ:
                    return os.environ[tk]

        return 'UNKNOWN'

    def api(self):
        return "{}/api/v4/projects".format(self.domain)

    def project_api(self, project):
        return self.api() + "/{}".format(urllib.parse.quote_plus(project))

    def pipeline_api(self, project):
        return self.project_api(project) + "/pipeline"

    def pipelines_api(self, project):
        return self.project_api(project) + "/pipelines"

    def trigger_api(self, project):
        return self.project_api(project) + "/trigger/pipeline"

    def launch(self, project, ref, params={}, token=0):
        if token == 0:
            token = Pipeline.trigger_token(project)

        var = {"token": token, "ref": ref}
        for k in params:
            var["variables[{}]".format(k)] = params[k]

        url = self.trigger_api(project)
        if (self.preview):
            print("URL: " + url)
            print("VARS: ", var)
            return {'id': -1}

        r = requests.post(url, data=var)
        return json.loads(r.text)

    def query(self, project, params={}, token=0):
        if token == 0:
            token = self.access_token()

        results = []
        fields = {'page': 1, 'per_page': 10}
        for k, v in params.items():
            if v != '@all' and not isinstance(v, list):
                fields[k] = v

        url = self.pipelines_api(project)
        if (self.preview):
            print("URL: " + url)

        while(len(results) == 0 or
              ('per_page' in fields and
               len(results) < int(fields['per_page']))):
            if (self.preview):
                print("VARS: ", fields)
                break

            r = requests.get(url, data=fields,
                             headers={'PRIVATE-TOKEN': token})
            for res in json.loads(r.text):
                if res == 'error' or res == 'message':
                    return results

                # If STATUS is something to fiter on.
                if 'status' in params:
                    if '@all' not in params['status'] and \
                       res['status'] not in params['status']:
                        continue

                # If USER is something to filter on.
                if 'user' in params:
                    info = self.pipeline(project, res['id'], token=token)
                    if '@all' not in params['user'] and \
                       info['user']['username'] not in params['user']:
                        continue

                    res['user'] = info['user']['username']
                    res['username'] = info['user']['name']

                # If the VARIABLES are something to filter on.
                if 'variables' in params:
                    variables = self.variables(project, res['id'], token=token)
                    if 'message' in variables:
                        print("Error. {}".format(variables['message']))
                        return

                    res['variable_names'] = []
                    res['variable_values'] = {}
                    count = 0

                    for variable in variables:
                        k = variable['key']
                        res['variable_names'].append(k)
                        if k in params['variables']:
                            if params['variables'][k] is False:
                                count = 0
                                break

                            if params['variables'][k] is True or \
                               params['variables'][k] == variable['value']:
                                count += 1

                            res['variable_values'][k] = variable['value']

                    if count != len(params['variables']):
                        continue

                results.append(res)
                if 'per_page' in fields and \
                        len(results) >= int(fields['per_page']):
                    break

            fields['page'] += 1

        return results

    def pipeline(self, project, pipeline_id, token='UNKNOWN'):
        url = self.pipelines_api(project) + "/{}".format(pipeline_id)
        r = requests.get(url, headers={'PRIVATE-TOKEN': token})
        return json.loads(r.text)

    def variables(self, project, pipeline_id, token='UNKNOWN'):
        url = self.pipelines_api(project) + "/{}/variables".format(pipeline_id)
        r = requests.get(url, headers={'PRIVATE-TOKEN': token})
        return json.loads(r.text)


class ProjectPipeline(Pipeline):
    def __init__(self, project, trigger_token=0, domain=0, preview=0):
        self.project = project
        self._trigger_token = trigger_token
        super().__init__(domain, preview)

    def launch(self, ref, params={}, token=0):
        if token == 0:
            token = self._trigger_token

        return super().launch(self.project, ref, params=params, token=token)

    def query(self, params={}, token=0):
        return super().query(self.project, params, token=token)
