import base
import os
import subprocess
import json
import sys
sys.dont_write_bytecode = True

import schedulers.localhost

base_path = '/tools/metrics.ca/mux-farm/0.2.0-2'
os.environ['PACKARD_HOME'] = base_path
paths = [os.path.join(base_path, 'bin'),
         os.path.join(base_path, "add-ons", 'mux-farm', 'bin'),
         os.getenv('PATH')]
os.environ['PATH'] = ':'.join(paths)

def alter_env(env):
    env['PACKARD_HOME'] = base_path
    env['PATH'] = ':'.join([os.path.join(base_path, 'bin'),
                            os.path.join(base_path, 'add-ons', 'mux-farm', 'bin'),
                            env['PATH']])

class Scheduler(schedulers.localhost.Scheduler):
    def __init__(self):
        schedulers.localhost.Scheduler.__init__(self, 0)

    def max_limit(self):
        return self.limit if self.limit else -1 

    def _submit_job(self, job):
        post = []
        pwd = self.pwd(job)

        if 'out' in job:
            post += ['1>>', job['out']]
            fh = self.open_file(job['out'], "w", True, pwd=pwd)
            fh.write(self.header() + "\n");
            fh.write("Command: {}\n".format(job['cmd']))
            fh.close()

        if 'err' in job:
            post += ['2>', job['err']]
        env = job['env'] if 'env' in job else None
        if env:
            alter_env(env)

        pwd = job['pwd'] if 'pwd' in job else None

        cmd = self.shell_wrap(job['cmd'], post=post, env=env)
        new_cmd = ['mux-farm']
        if 'MUX_FARM_IMAGE' in os.environ:
            new_cmd += ['--image', os.environ['MUX_FARM_IMAGE']]
        if 'timeout' in job:
            new_cmd += ['--timeout', job['timeout']]
        if 'tag' in job:
            new_cmd += ['--tag', job['tag']]
        if 'mem' in job:
            new_cmd += ['--mem', job['mem']]

        new_cmd += cmd

        self.debug_msg("CMD {}".format(str(new_cmd)))

        p = subprocess.Popen(new_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=env, cwd=pwd)
        sout, serr = p.communicate()
        if serr:
            if 'err' in job:
                f = self.open_file(job['err'], 'w', True, pwd=pwd)
                f.write(serr)
                f.close()

            return None

        if sout:
            job['mux_id'] = sout.decode('utf-8').strip()

        return job

    def _query_job(self, job):
        cmd = ['mux-status', '--format', 'json', job['mux_id']]
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sout, serr = p.communicate()
        if sout:
            j = json.loads(sout)
            info = j[0]
            s = j[0]['state'].upper()
            if 'status' in j[0]:
                info = info['status']
                if 'done' in j[0]['status']:
                    info = info['done']
                    if 'user_return_code' in info:
                        job['exit_code'] = info['user_return_code']
                        s = info['final_status'].upper()

            if s == 'PULL' or s == 'ALLOC':
               return base.State.RUN                   

            try:
                return base.State[s]
            except Exception as e:
                self.debug_msg(str(e))
                return base.State.UNKNOWN

        return base.State.GONE 

    def header(self, info=None):
        return "Running on mux-farm"

    def describe(self):
        return "Running {}on the mux-farm".format("maximum {} ".format(self.limit) if self.limit else "")
