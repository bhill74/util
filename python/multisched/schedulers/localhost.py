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

        if isinstance(cmd, str):
            cmd = self.shell_wrap(cmd, env=env)

        if 'out' in job:
            out_f = self.open_file(job['out'], "w", force=True, pwd=pwd)
            out_f.write(self.header(info) + "\n")
            out_f.write("Command: {}\n".format(cmd))
            out_f.close()
            env['MULTISCHED_LOG'] = job['out']

        if 'err' in job:
            err_f = self.open_file(job['err'], "w", force=True, pwd=pwd)
            env['MULTISCHED_ERR'] = job['err']

        job['exit_file'] = os.path.join(pwd, job['job_id']+'.code')
        env['MULTISCHED_CODE'] = job['exit_file'] 

        self.debug_msg("CMD {}".format(str(cmd)))

        try:
            p = subprocess.Popen(['runner'] + cmd,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 env=env, cwd=pwd)
            job['pid'] = p.pid
            job['state'] = 'active'
            return job
        except FileNotFoundError as e:
            job['exit_code'] = 127
            job['state'] = 'fail'
            err_f.write(str(e))
            err_f.close()
            out_f.close()
            return job

        except Exception as e:
            err_f.write(str(e))
            err_f.close()
            out_f.close()

        return job 

    def _submit_job(self, job):
        if 'cmd' not in job:
            return None

        return self._launch_local(job['cmd'], job)

    def _query_job(self, job):
        if 'pid' not in job:
            return base.State.CORRUPT

        pid = job['pid']
        pid_str = str(pid)
        try:
            os.kill(pid, 0)
        except OSError as e:
            return base.State.PASS

        signal.alarm(2)
        try:
            r = os.waitpid(pid, 0)
            exit_file = self.open_file(job['exit_file'], 'r')
            job['exit_code'] = int(exit_file.read())
            exit_file.close()
            os.remove(job['exit_file'])
            del job['exit_file']
            signal.alarm(0)
            return base.State.PASS if job['exit_code'] == 0 else base.State.FAIL
        except Exception as e:
            self.debug_msg(str(e))

        signal.alarm(0)

        return base.State.RUN 

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
