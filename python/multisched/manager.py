import importlib
import os
import sys
import time
import shlex
import json
import uuid
import socket
from multiprocessing.connection import Listener, Client
from multiprocessing import Process, Manager
sys.dont_write_bytecode = True
import base


# External modules
sys.path.append(os.path.join(os.getenv('HOME'), 'lib', 'multisched'))

_host = 'localhost'
_password = b'Secret Password'
_var = "SCHED_PORT"
_undef = "undefined port"


def echo(val, env=None, both=False):
    return 'echo {}'.format(val)
    return 'echo {}'.format(val) + ('| tee >(cat >&2)' if both else '')


def title(val, env=None, both=False):
    return echo('----- {} -----'.format(val), env=env, both=both)



class SharedJobs:
    def __init__(self, manager):
        #self.jobs = manager.Value(list, []) 
        self.jobs = manager.list()
        self.done = manager.list()
        self.queue = manager.list()
        self.bins = manager.list()
        self.live = manager.Value(bool, True)
        self.lock = manager.Lock()

    # Active Jobs
    def add_job(self, job):
        with self.lock:
            if 'exit_code' in job:
                self.done.append(job)
            else:
                self.jobs.append(job)

    def complete_job(self, i, job):
        with self.lock:
            self.jobs.pop(i)
            self.done.append(job)

    def num_jobs(self):
        with self.lock:
            return len(self.jobs)

    def get_job(self, i):
        with self.lock:
            return self.jobs[i] if len(self.jobs) > i else None

    # Queued Jobs
    def prepend_to_queue(self, job):
        with self.lock:
            q = self.queue
            q.insert(0, job)
            self.queue = q

    def add_to_queue(self, job):
        with self.lock:
            #print("  to bin", len(self.bins), job.keys(), job['job_id'])
            if len(self.bins):
                #print("bins ", [len(b) for b in self.bins])
                b0 = self.bins[0]
                if len(b0) == len(self.bins[-1]):
                    b0.append(job)
                    self.bins[0] = b0
                else:
                    p = b0 
                    for i in range(1,len(self.bins)):
                        n = self.bins[i]
                        if len(n) < len(p):
                            self.bins[i] = n + [job]
                            break
                        p = n
                
                #print("bins ", [len(b) for b in self.bins])
                return

            job['state'] = 'queued'
            self.queue.append(job)

    def num_queued(self):
        n = 0
        with self.lock:
            n = len(self.queue)

        return n

    def get_queue(self, i):
        with self.lock:
            return self.queue[i] if len(self.queue) > i else None

    def pop_queue(self, i):
        with self.lock:
            return self.queue.pop(i) if len(self.queue) else None

    # Bins
    def num_bins(self):
        with self.lock:
            return len(self.bins)

    def has_bins(self):
        with self.lock:
            if len(self.bins) == 0:
                return False

            for b in self.bins:
                if len(b) > 0:
                    return True

        return False

    def set_bins(self, s):
        with self.lock:
            for i in range(s):
                self.bins.append([])

    def get_bin(self, i):
        with self.lock:
            return self.bins[i] if len(self.bins) > i else []

    def add_to_bin(self, i, job):
        with self.lock:
            self.bins[i].append(job)

    def distribute_bins(self, sched):
        with self.lock:
            while len(self.bins):
                bin_jobs = self.bins.pop(0);
                if len(bin_jobs) == 0:
                    continue

                all_cmd = {}
                e = dict(os.environ)
                if isinstance(bin_jobs[0], dict):
                    all_cmd = bin_jobs[0].copy()
                    del(all_cmd['cmd'])
                    if 'env' in all_cmd:
                        e = all_cmd['env']
                    else:
                        all_cmd['env'] = e
                else:
                    all_cmd['env'] = e

                cmd = []
                for b in bin_jobs:
                    c = b
                    env_cmd = []
                    if isinstance(b, dict):
                        c = b['cmd']
                        if 'env' in b:
                            ee = b['env']
                            de = {k:v for k,v in ee.items() if k not in e or v != e[k]}
                            for k,v in de.items():
                                if k == 'PWD':
                                    env_cmd += [sched.chdir(v, env=ee)]
                                elif k != 'OLDPWD':
                                    env_cmd += [sched.setenv(k, v, env=ee)]
                            for k in [k for k in e.keys() if k not in ee]:
                                env_cmd += [sched.unsetenv(k, env=ee)]
                            e = ee

                    cmd_str = sched.sh_join(c)
                    cmd += [echo('', env=e, both=True),
                            title(cmd_str, env=e, both=True)]
                    cmd += env_cmd + [cmd_str]

                all_cmd['cmd'] = sched.join_cmds(cmd) 

                self.queue.append(all_cmd);
    # Live
    def is_live(self):
        with self.lock:
            return self.live.value

    def set_live(self, live):
        with self.lock:
            self.live.value = live

    def has_work(self):
        with self.lock:
            return len(self.jobs) or len(self.queue) or len(self.bins) or self.live.value

    def wait_for(self, values, attrib='job_id'):
        while True:
            with self.lock:
                j = [j for j in self.jobs if attrib in j and j[attrib] in values]
                q = [q for q in self.queue if attrib in q and q[attrib] in values]
                if len(j) == 0 and len(q) == 0:
                    return True
                
            time.sleep(3)

        return False

    def status(self, job_id, sched):
        with self.lock:
            for j in [j for j in self.jobs if j['job_id'] == job_id]:
                return sched.query(j).name

            for j in [q for q in self.queue if q['job_id'] == job_id]:
                return j['state'].name

            for j in [q for q in self.done if q['job_id'] == job_id]:
                return j['state'].name

        return base.State.NAME.name 


def update_jobs(flavor, shared, settings):
    h = Hub(flavor, shared)
    h.wait()


class Hub:
    def __init__(self, flavor, shared, delay=4):
        self.flavor = flavor
        self.flavor.hub = self
        self.unique_id = 0
        self.delay = delay 
        self.shared = shared 

    def _submit(self, job):
        self.flavor.debug_msg("  submitting: {}".format(job['job_id']))
        job = self.flavor.submit(job)
        if job:
            self.shared.add_job(job)
            return True
        #else:
        #    self.shared.prepend_to_queue(job)

        return False

    def limit(self):
        return self.flavor.max_limit()

    def _prep(self, job, params):
        if isinstance(job, str):
            job = shlex.split(job)

        if 'name' not in job:
            job['name'] = str(self.unique_id)

        self.unique_id += 1
        job['job_id'] = str(uuid.uuid4())
        job.update(params)
        return job

    def queue(self, job, params={}):
        job = self._prep(job, params) 

        self.shared.add_to_queue(job)
        return job

    def submit(self, job, params={}):
        job = self._prep(job, params)
        limit = self.limit()
        n_jobs = self.shared.num_jobs()
        if limit == -1 or n_jobs < limit:
            if self._submit(job):
                return job

        self.shared.add_to_queue(job)
        return job

    def update(self):
        jobs = []
        n_jobs = self.shared.num_jobs()
        i = 0
        while i < n_jobs:
            job = self.shared.get_job(i)
            r = self.flavor.query(job)
            if r == base.State.PASS or r == base.State.FAIL or r == base.State.CORRUPT:
                job['state'] = r
                self.flavor._reclaim(job)
                self.shared.complete_job(i, job)
                n_jobs -= 1
            else:
                i += 1

        limit = self.limit()
        n_queued = self.shared.num_queued()
        while (limit == -1 or n_jobs < limit) and n_queued:
            q = self.shared.pop_queue(0)
            n_queued -= 1
            n_jobs += 1
            if q:
                self._submit(q)


    def wait(self):
        while self.shared.has_work():
            self.update()
            time.sleep(self.delay)

    def wait_for(self, job):
        while True:
            r = self.flavor.query(job)
            if r == base.State.PASS or r == base.State.FAIL:
                job['state'] = r
                self.flavor._reclaim(job)
                break
            elif r == base.State.CORRUPT:
                job['state'] = r
                self.flavor._reclaim(job)
                break

            time.sleep(self.delay)


def get_address():
    default = False
    if _var in os.environ:
        address = (_host, int(os.environ[_var]))
    else:
        sock = socket.socket()
        sock.bind((_host, 0))
        address = sock.getsockname()
        sock.close()
        default = True

    return address, default


def serve():
    address, default = get_address()

    sched, settings = init_scheduler()
    manager = Manager()
    shared = SharedJobs(manager)

    p = Process(target=update_jobs, args=(sched, shared, settings))
    p.start()

    print(sched.describe())
    h = Hub(sched, shared)
    if default:
        print("PORT", address[1])

    listener = Listener(address, authkey=_password)
    keep = True
    conn = None
    while keep:
        conn = listener.accept()
        while True:
            msg = conn.recv()
            if isinstance(msg, str) and msg == 'close':
                conn.close()
                break
               
            elif isinstance(msg, str) and msg == 'shutdown':
                keep = False
                conn.close()
                break

            elif isinstance(msg, list) and msg[0] == 'bins':
                shared.set_bins(msg[1])
                conn.close()
                break

            elif isinstance(msg, str) and msg == 'distribute':
                shared.distribute_bins(sched)
                conn.close()
                break

            elif isinstance(msg, list) and msg[0] == 'wait':
                try:
                    attrib, values, host, pid = msg[1:] 
                except Exception as e:
                    attrib, values, host, pid = [[], 'job_id', '', 0] 
               
                if shared.wait_for(values, attrib=attrib):
                    conn.send("done")

                conn.close() 
                break

            elif isinstance(msg, list) and msg[0] == 'status':
                try:
                    ids, host, pid = msg[1:]
                except Exception as e:
                    ids, host, pid = [[], '', 0]

                status = [shared.status(i,sched) for i in ids]
                conn.send(status)

                conn.close()
                break

            elif isinstance(msg, dict):
                msg['accept'] = listener.last_accepted
                msg = h.queue(msg)
                conn.send(msg['job_id'])

            else:
                print("Unrecognized Result", msg)
                break

    listener.close()
    shared.set_live(False)
    p.join()


def submit(job, params={}):
    if isinstance(job, list):
        job = {'cmd': job}

    if 'env' not in job:
        job['env'] = dict(os.environ)

    if 'pwd' not in job:
        job['env']['PWD'] = job['pwd'] = os.getcwd()

    job.update(params)
    address, default = get_address() 
    conn = Client(address, authkey=_password)
    conn.send(job)
    conn.send('close')
    job_id = conn.recv()
    conn.close()
    return job_id

def shutdown():
    address, default = get_address() 
    try:
        conn = Client(address, authkey=_password)
        conn.send('shutdown')
        conn.close()
    except Exception as e:
        print(str(e))

def bins(num):
    address, default = get_address() 
    conn = Client(address, authkey=_password)
    conn.send(['bins', num])
    conn.close()

def distribute():
    address, default = get_address() 
    conn = Client(address, authkey=_password)
    conn.send('distribute')
    conn.close()


def wait(values, attrib='job_id'):
    address, default = get_address() 
    conn = Client(address, authkey=_password)
    conn.send(['wait', attrib, values, socket.gethostname(), str(os.getpid())])
    while conn.recv() != "done":
        print("test") # To fix

    conn.close()

def status(ids):
    address, default = get_address() 
    conn = Client(address, authkey=_password)
    if isinstance(ids, str):
        ids = [ids]

    conn.send(['status', ids, socket.gethostname(), str(os.getpid())])
    status = conn.recv()
    conn.close()

    return status



SETTINGS_VAR = "PP";

def settings_var():
    return SETTINGS_VAR;

def settings():
    if SETTINGS_VAR in os.environ:
        return json.loads(os.environ[SETTINGS_VAR])

    return {}

def init_scheduler():
    name = 'localhost'
    settings = {}
    if SETTINGS_VAR in os.environ:
        info = os.environ[SETTINGS_VAR]
        try:
            settings = json.loads(info)
            if 'sched' in settings:
                name = settings['sched']

        except Exception as e:
           print("E", e)
           sys.stderr.write(str(e))

    m = importlib.import_module("schedulers.{}".format(name))
    sched = m.Scheduler()
    sched.absorb(settings)
    return sched, settings
