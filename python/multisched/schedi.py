import manager
import os
import time
import sys
sys.dont_write_bytecode = True

import atexit


SERVE_PID = -1

def startup():
    address, default = manager.get_address()
    os.environ['SCHED_PORT'] = str(address[1])
    SERVE_PID = os.fork()
    if SERVE_PID == 0:
        manager.serve()
        exit()
    else:
        time.sleep(1)
        atexit.register(shutdown)

def settings():
    return manager.settings()

def set_setting(key, value):
    s = manager.settings()
    s[key] = value
    os.environ[manager.settings_var()] = json.dumps(s)

def remove_setting(key):
    s = manager.settings()
    del s[key]
    os.environ[manager.settings_var()] = json.dumps(s)

def bins(value):
    manager.bins(value)

def distribute():
    manager.distribute()

def shutdown():
    if SERVE_PID == 0:
        return

    manager.shutdown() 
    os.wait()

def submit(cmd, params={}):
    return manager.submit(cmd, params) 

def wait(ids=None):
    if isinstance(ids, str):
        ids = [ids]

    manager.wait(ids)
