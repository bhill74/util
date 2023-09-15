import os
import sys
import shlex
sys.dont_write_bytecode = True


class Base:
    def __init__(self):
        self._start = True
        self.manager = None
        self.out_dir = None
        self.err_dir = None
        self.debug = False

    def debug_msg(self, msg):
        if self.debug:
            print(msg)

    def sh_split(self, cmd):
        return shlex.split(cmd)

    def sh_join(self, cmd):
        if isinstance(cmd, str):
            return cmd

        # TODO: Quote arguments that need it.
        return " ".join(cmd)
        #return " ".join([shlex.quote(c) for c in cmd])

    def setenv(self, name, value, env=None):
        return 'export {}={}'.format(name, value)

    def unsetenv(self, name, env=None):
        return 'unset {}'.format(name)

    def chdir(self, path, env=None):
        return 'cd {}'.format(path)

    def join_cmds(self, cmds, env=None):
        if isinstance(cmds, str):
            return cmds

        return ';'.join(cmds)

    def shell_wrap(self, cmd, pre=None, post=None, env=None):
        if isinstance(cmd, list):
            if pre and post:
                cmd = "({})".format(self.join_cmds(pre + [self.sh_join(cmd)])) + " ".join(post)
            elif post:
                cmd = self.sh_join(cmd + post)
            elif pre:
                cmd = self.join_cmds(pre + [self.sh_join(cmd)])

        elif isinstance(cmd, str):
            if pre and post:
                cmd = " ".join(["({})".format(self.join_cmds(pre + [cmd]))] + post)
            elif post:
                cmd = " ".join(["({})".format(cmd)] + post)
            elif pre:
                cmd = self.join_cmds(pre + [cmd])

        else:
            sys.stderr.write("Bad input", cmd)

        return ['bash', '-c', cmd]

    def submit(self, job):
        if isinstance(job, list):
            job = {'cmd': cmd}

        if 'name' not in job:
            job['name'] = 'unknown'

        out_file = "out"
        err_file = "err"
        if 'name' in job:
            out_file = "{}.out".format(job['name'])
            err_file = "{}.err".format(job['name'])

        if 'out' not in job and self.out_dir:
            job['out'] = self.out_dir
        if 'err' not in job and self.err_dir:
            job['err'] = self.err_dir

        if 'out' in job:
            out_file = os.path.join(job['out'], out_file)
        if 'err' in job:
            err_file = os.path.join(job['err'], err_file)
        elif 'out'in job:
            err_file = os.path.join(job['out'], err_file)

        job['out'] = out_file
        job['err'] = err_file
        return self._submit_job(job)

    def query(self, job):
        return self._query_job(job)

    def _reclaim(self, job):
        return

    def absorb(self, settings):
        if not settings:
            return False

        if not isinstance(settings, dict):
            return False

        if 'out' in settings:
            self.out_dir = settings['out']
        if 'err' in settings:
            self.err_dir = settings['err']

        if 'debug' in settings:
            self.debug = settings['debug']

        return True

    def header(self, info=None):
        return "Nothing significant"

    def describe(self):
        return "A Basic Scheduler"
