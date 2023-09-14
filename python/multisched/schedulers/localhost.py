import subprocess
import os
import sys
import base
import signal
import socket
sys.dont_write_bytecode = True


def timeout_handler(signum, frame):
    raise Exception("Timed out")


signal.signal(signal.SIGALRM, timeout_handler)


class Scheduler(base.Base):
    def __init__(self, limit=1):
        base.Base.__init__(self)
        self.limit = limit

    def max_limit(self):
        return self.limit

    def _launch_local(self, cmd, job, info=None):
        env = job['env'] if 'env' in job else None
        pwd = job['pwd'] if 'pwd' in job else os.getcwd() 

        out_f = subprocess.STDOUT
        if 'out' in job:
            out_fn = job['out']
            if not out_fn.startswith('/') and pwd:
                out_fn = os.path.join(pwd, out_fn)
            out_f = open(out_fn, "w")
            out_f.write(self.header(info) + "\n")

        if 'err' in job:
            err_fn = job['err']
            if not err_fn.startswith('/') and pwd:
                err_fn = os.path.join(pwd, err_fn)
            err_f = open(err_fn, "w")

        if isinstance(cmd, str):
            cmd = self.shell_wrap(cmd, env=env)

        out_f.write("Command: {}\n".format(cmd))

        try:
            p = subprocess.Popen(cmd,
                                 stdout=out_f,
                                 stderr=err_f,
                                 stdin=subprocess.DEVNULL,
                                 env=env, cwd=pwd)
            job['pid'] = p.pid
            return job
        except Exception as e:
            err_f.write(str(e))
            err_f.close()
            out_f.close()

        return None

    def _submit_job(self, job):
        if 'cmd' not in job:
            return None

        return self._launch_local(job['cmd'], job)

    def _query_job(self, job):
        if 'pid' not in job:
            return "CORRUPT"

        pid = job['pid']
        pid_str = str(pid)
        try:
            t = os.kill(pid, 0)
        except OSError:
            return "DONE"

        signal.alarm(2)
        try:
            os.waitpid(pid, 0)
            signal.alarm(0)
            return "DONE"
        except Exception as e:
            self.debug_msg(str(e))

        signal.alarm(0)

        return "RUN"

    def absorb(self, settings):
        if not base.Base.absorb(self, settings):
            return False

        if 'limit' in settings:
            self.limit = settings['limit'] 

        return True

    def header(self, info=None):
        return "Running on localhost:{}".format(socket.gethostname())

    def describe(self):
        return "Running maximum {} jobs on localhost:{}".format(self.limit, socket.gethostname())
