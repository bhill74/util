#!/usr/bin/python3

import os
import json
import requests
import urllib.parse
import re
import time


def parseTrace(trace):
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


def download(response, output):
    if response.status_code != 200:
        info = json.loads(response.text)
        msg = info['message'] if 'message' in info else "{} Unknown".format(response.status_code) 
        print("Unable to download ({})".format(msg))
        return 

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


def isCompleteStatus(status):
    return True if status is None or status in ['success', 'failed'] \
            else False


history_props = ['status', 'name', 'web_url', 'variables']

# ********************************************************************************
# Name: Base
# Description:
#  The base GitLab class for communicating with the WebAPI. Whatever members
#  are not provided can be derived from the environment variables.
# Arguments:
#  domain -- The name of the gitlab domain.
#  preview -- Whether to be verbose about the data being communicated.
#  access_token -- The token key to use for read access.
# ********************************************************************************
class Base:
    def __init__(self, domain=None, preview=0, access_token=None):
        if not domain:
            domain = os.environ["GL_DOMAIN"] if 'GL_DOMAIN' in os.environ \
                else 'https://gitlab.com'

        self.domain = domain
        self.preview = preview
        self._access_token = access_token

    def get(self, url, headers={}, data={}, stream=False, token=None):
        if self.preview:
            print("URL: {}".format(url))

        if not token:
            token = self.access_token()

        if not token:
            raise ValueError("Missing access token")

        if "token" not in headers:
            headers['PRIVATE-TOKEN'] = token

        return requests.get(url, headers=headers, data=data, stream=stream)

    def getJSON(self, url, headers={}, data={}, stream=False, token=None, 
                default=None):
        r = self.get(url, headers=headers, data=data, stream=stream, token=token)
        if r.status_code != 200:
            return default
        return json.loads(r.text)

    def download(self, url, output, token=0):
        return download(self.get(url, stream=True, token=token), output)

    def access_token(self):
        if self._access_token:
            return self._access_token

        return os.environ["GL_TOKEN"] if 'GL_TOKEN' in os.environ \
            else 0

    def trigger_token(project):
        for k, v in os.environ.items():
            m = re.search(r'^GL_PROJECT_(\d*)$', k)
            if m and v == project:
                pid = m.group(1)
                tk = "GL_TRIGGER_" + pid
                if tk in os.environ:
                    return os.environ[tk]

        return 0

    def api(self):
        return "{}/api/v4/projects".format(self.domain)

    def project_api(self, project):
        return self.api() + "/{}".format(urllib.parse.quote_plus(str(project)))

    def pipeline_api(self, project):
        return Base.project_api(self, project) + "/pipeline"

    def pipelines_api(self, project):
        return Base.project_api(self, project) + "/pipelines"

    def jobs_api(self, project):
        return Base.project_api(self, project) + "/jobs"

    def trigger_api(self, project):
        return Base.project_api(self, project) + "/trigger/pipeline"

    def repository_api(self, project):
        return Base.project_api(self, project) + "/registry/repositories"

    def launch(self, project, ref, params={}, token=None):
        if not token:
            token = Base.trigger_token(project)

        if not token:
            raise ValueError("Missing trigger token")

        var = {"token": token, "ref": ref}
        for k in params:
            var["variables[{}]".format(k)] = params[k]

        url = Base.trigger_api(self, project)
        if (self.preview):
            print("URL: " + url)
            print("VARS: ", var)
            return {'id': -1}

        r = requests.post(url, data=var)
        return json.loads(r.text)

    def query(self, project, params={}, token=None):
        results = []
        fields = {'page': 1, 'per_page': 10}
        for k, v in params.items():
            if v != '@all' and not isinstance(v, list):
                fields[k] = v

        url = Base.pipelines_api(self, project)
        if (self.preview):
            print("URL: " + url)

        while(len(results) == 0 or
              ('per_page' in fields and
               len(results) < int(fields['per_page']))):
            if (self.preview):
                print("VARS: ", fields)
                break

            for res in self.getJSON(url, data=fields, token=token, default=[]):
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

        return results

    def project(self, project, token=None):
        url = "{}".format(Base.project_api(self, project))
        return self.getJSON(url, token=token, default={})

    def pipeline(self, project, pipeline_id, token=None):
        url = "{}/{}".format(Base.pipelines_api(self, project),
                             pipeline_id)
        return self.getJSON(url, token=token, default={})

    def job(self, project, job_id, token=None):
        url = "{}/{}".format(Base.jobs_api(self, project),
                             job_id)
        return self.getJSON(url, token=token, default={})

    def variables(self, project, pipeline_id, token=None):
        url = "{}/{}/variables".format(Base.pipelines_api(self, project),
                                       pipeline_id)
        results = {}
        for v in self.getJSON(url, token=token, default={}):
            results[v['key']] = v['value']

        return results

    def artifactsById(self, project, job_id, output, token=None):
        if not output:
            info = Base.job(self, project, job_id)
            name = info['name'] if 'name' in info else 'default'
            output = "{}.zip".format(name)

        url = "{}/{}/artifacts".format(
                Base.jobs_api(self, project),
                job_id)
        self.download(url, output, token=token)

    def artifactsByName(self, project, branch, job_name, output, token=None):
        if not branch:
            info = Base.project(self, project)
            branch = info['default_branch'] if 'default_branch' in info else 'master'

        if not output:
            output = "{}.zip".format(job_name)

        url = "{}/jobs/artifacts/{}/download?job={}".format(
                Base.project_api(self, project),
                branch,
                urllib.parse.quote_plus(str(job_name)))
        self.download(url, output, token=token)

    def jobs(self, project, pipeline_id, token=None):
        url = "{}/{}/jobs".format(Base.pipelines_api(self, project),
                                  pipeline_id)
        return self.getJSON(url, token=token, default=[])

    def trace(self, project, job_id, token=None):
        url = Base.project_api(self, project) + "/jobs/{}/trace".format(job_id)
        return self.get(url, token=token).text

    def repositories(self, project, params={}, token=None):
        url = Base.repository_api(self, project) + "/"
        return self.getJSON(url, data=params, token=token)


class Project(Base):
    def __init__(self, project, domain=None, preview=0, access_token=None):
        self.project = project
        super().__init__(domain, preview, access_token)

    def project_api(self):
        return Base.project_api(self, self.project)

    def pipeline_api(self):
        return Base.pipeline_api(self, self.project)

    def pipelines_api(self):
        return Base.pipelines_api(self, self.project)

    def jobs_api(self):
        return Base.jobs_api(self, self.project)

    def trigger_api(self):
        return Base.trigger_api(self, self.project)

    def repository_api(self):
        return Base.repository_api(self, self.project)

    def info(self):
        return Base.project(self, self.project)

    def launch(self, ref, params={}, token=None):
        r = Base.launch(self, self.project, ref, params=params, token=token)
        return Pipeline(self.project, r['id'], self.domain, self.preview)

    def query(self, params={}, token=None):
        return Base.query(self, self.project, params=params, token=token)

    def pipeline(self, pipeline_id, token=None):
        return Pipeline(self.project, self.pipeline_id, self.domain,
                        self.preview)

    def job(self, job_id, token=None):
        return Job(self.project, self.pipeline_id, self.job_id, self.domain,
                   self.preview)

    def variables(self, pipeline_id, token=None):
        return Base.variables(self, self.project, pipeline_id, token=token)

    def artifactsById(self, job_id, output, token=None):
        return Base.artifactsById(self, self.project, job_id, output,
                                  token=token)

    def artifactsByName(self, branch, job_name, output, token=None):
        return Base.artifactsByName(self, self.project, branch, job_name, output,
                                    token=token)

    def jobs(self, pipeline_id, token=None):
        jobs = Base.jobs(self, self.project, pipeline_id, token=token)
        return [Job(self.project,
                pipeline_id, job['id'],
                self.domain, self.preview) for job in jobs]

    def trace(self, job_id, token=None):
        return Base.trace(self, self.project, job_id, token=token)

    def repositories(self, params={}, token=None):
        return Base.repositories(self.project, params=params, token=token)


class Pipelines(Project):
    def __init__(self, project, trigger_token=None, domain=None, preview=0):
        self._trigger_token = trigger_token
        super().__init__(project, domain, preview)

    def launch(self, ref, params={}, token=None):
        if not token:
            token = self._trigger_token

        return Project.launch(self, ref, params=params, token=token)

    def query(self, params={}, token=None):
        return Project.query(self, params, token=token)

    def jobs(self, pipeline_id, token=None):
        return Project.jobs(self, pipeline_id, token=token)


class Pipeline(Project):
    def __init__(self, project, pipeline_id, domain=None, preview=0):
        self.pipeline_id = pipeline_id
        super().__init__(project, domain, preview)

    def __rep__(self):
        return "Pipeline {} on {}".format(self.pipeline_id, self.project)

    def jobs(self, token=None):
        return Project.jobs(self, self.pipeline_id, token=token)

    def jobIds(self, token=None):
        return [job.job_id for job in self.jobs(token)]

    def trace(self, job_id, token=None):
        return Project.trace(self, job_id, token=token)

    def variables(self, token=None):
        return Project.variables(self, self.pipeline_id, token=token)

    def info(self, token=None):
        return Base.pipeline(self, self.project, self.pipeline_id)

    def attr(self, name, token=None):
        if name in 'variables':
            return self.variables(token=token)

        r = self.info()
        if name in r:
            return r[name]

        return None

    def attrs(self, names, token=None):
        result = {}
        if 'variables' in names:
            result['variables'] = self.variables(token=token)
            if len(names):
                return result

        r = self.info()
        for name in names:
            if name in r:
                result[name] = r[name]

        return result

    def status(self, token=None):
        return self.attr('status')

    def pipelines(self, token=None):
        result = []
        for job in self.jobs(token=token):
            result += job.pipelines()

        return result

    def overallStatus(self, token=None):
        status = self.status(token=token)
        if status != "success":
            return status

        for j in self.jobs():
            status = j.overallStatus(token=token)
            if status != "success":
                return status

        return status

    def hierarchy(self, props=None, token=None):
        info = {'id': self.pipeline_id, 'jobs': []}

        if props:
            info.update(self.attrs(props, token=token))

        for job in self.jobs(token=token):
            info['jobs'].append(job.hierarchy(props=props, token=token))

        return info

    def history(self, token=None):
        return self.hierarchy(history_props, token=token)

    def artifacts(self, job_id, output, token=None):
        Project.artifactsById(self, job_id, output, token=token)

    def wait(self, token=None):
        while True:
            if isCompleteStatus(self.status()):
                break

            time.sleep(3)

        for pipeline in self.pipelines():
            pipeline.wait()


class Job(Pipeline):
    def __init__(self, project, pipeline_id, job_id, domain=None, preview=0):
        self.job_id = job_id
        super().__init__(project, pipeline_id, domain, preview)

    def id(self):
        return self.job_id

    def info(self, token=None):
        return Base.job(self, self.project, self.job_id, token=token)

    def attr(self, name, token=None):
        r = self.info(token=token)
        if name in r:
            return r[name]

        return None

    def attrs(self, names, token=None):
        r = self.info()
        result = {}
        for name in names:
            if name in r:
                result[name] = r[name]

        return result

    def status(self, token=None):
        return self.attr('status', token=token)

    def overallStatus(self, token=None):
        status = self.status(token=token)
        if status != "success":
            return status

        for p in self.pipelines(token=token):
            status = p.overallStatus(token=token)
            if status != "success":
                return status

        return "success"

    def trace(self, token=None):
        return Pipeline.trace(self, self.job_id, token=token)

    def artifacts(self, output, token=None):
        return Pipeline.artifactsById(self, self.job_id, output, token=token)

    def pipelines(self, token=None):
        result = []
        for item in parseTrace(self.trace(token=token)):
            if 'id' not in item or 'project_id' not in item:
                continue

            pipeline_id = item['id']
            project_id = item['project_id']
            p = Pipeline(project_id, pipeline_id,
                         self.domain, self.preview)
            result.append(p)

        return result

    def hierarchy(self, props=None, token=None):
        info = {'id': self.job_id, 'pipelines': []}
        if props:
            info.update(self.attrs(props, token=token))

        for pipeline in self.pipelines(token=token):
            h = pipeline.hierarchy(props=props, token=token)
            info['pipelines'].append(h)

        return info

    def history(self, token=None):
        return self.hierarchy(history_props, token=token)

    def wait(self):
        while True:
            if isCompleteStatus(self.status()):
                break

            time.sleep(3)


# ********************************************************************************
# Name: Repositories
# Description:
#  The class for communicating with the WebAPI in relation to Repositories.
# Arguments:
#  domain -- The name of the gitlab domain.
#  preview -- Whether to be verbose about the data being communicated.
#  access_token -- The token key to use for read access.
# ********************************************************************************
class Repositories(Project):
    def __init__(self, project, domain=None, preview=0):
        self.project = project
        super().__init__(domain, preview)

    def repositories(self, params={}, token=None):
        return Project.repositories(self, self.project, params, token=token)

    def names(self, token=None):
        names = []
        info = self.repositories({"tags": True}, token)
        for i in info:
            if "tags" in i:
                for t in i["tags"]:
                    if "name" in t and t["name"] not in names:
                        names.append(t["name"])

        names.sort()
        return names