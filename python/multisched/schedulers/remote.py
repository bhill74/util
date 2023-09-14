import sys
sys.dont_write_bytecode = True

import schedulers.localhost


class Scheduler(schedulers.localhost.Scheduler):
    def __init__(self, hosts=[], limit=1):
        schedulers.localhost.Scheduler.__init__(self, limit)
        self.hosts = {}
        l = 0
        for h in hosts:
            self.hosts[h] = limit
            l += limit

    def max_limit(self):
        limit = 0;
        for h in self.hosts:
            limit += self.hosts[h]

        return limit
            
    def _get_host(self):
        hosts = [h for h in self.hosts.keys() if self.hosts[h] > 0]
        if len(hosts) == 0:
            return None

        return hosts[0]

    def _remove_host(self, host):
        self.hosts[host] -= 1

    def _add_host(self, host):
        self.hosts[host] += 1

    def _submit_job(self, job):
        if 'cmd' not in job:
            self.debug_msg("Job has no 'cmd' entry")
            return None

        host = self._get_host()
        if not host:
            self.debug_msg("No available host")
            return None

        pre = ['echo']
        env = None
        if 'env' in job:
            env = job['env']
            pre += [self.chdir(env['PWD'], env=env)]

        new_cmd = ['ssh', host] + self.shell_wrap(job['cmd'], pre=pre, env=env)
        self.debug_msg("Cmd: {}".format(new_cmd))

        job = self._launch_local(new_cmd, job, info={'host': host})
        if job:
            job['host'] = host
            self._remove_host(host)
        else:
            self.debug_msg("not submitted")

        return job

    def _reclaim(self, job):
        if 'host' not in job:
            return

        self._add_host(job['host'])

    def absorb(self, settings):
        if not schedulers.localhost.Scheduler.absorb(self, settings):
            return False

        if 'hosts' in settings:
            for h in settings['hosts']:
                self.hosts[h] = self.limit

    def header(self, info=None):
        return "Running on host {}".format(info['host'] if info and 'host' in info else 'Unknown')

    def describe(self):
        return "Running maximum {} jobs accross {}".format(self.max_limit(), "/".join(self.hosts.keys()))
