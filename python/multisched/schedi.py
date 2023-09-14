import manager
import os
import time
import sys
sys.dont_write_bytecode = True

SERVE_PID = -1

def setup():
    address, default = manager.get_address()
    os.environ['SCHED_PORT'] = str(address[1])
    SERVE_PID = os.fork()
    if SERVE_PID == 0:
        manager.serve()
        exit()
    else:
        time.sleep(1)


def bins(value):
    manager.bins(value)

def distribute():
    manager.distribute()

def shutdown():
    manager.shutdown() 
    print("Shutdown")
    os.wait()

def submit(cmd, params={}):
    return manager.submit(cmd, params) 

def wait(ids=None):
    if isinstance(ids, str):
        ids = [ids]

    manager.wait(ids)
