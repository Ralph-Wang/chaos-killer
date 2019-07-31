#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import threading
import timeunit
import requests
import time
import math
import signal
import subprocess

from .killer import *


# hot fix for the issue of execute shell with pipeline in Python < 3.2
def default_sigpipe():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def execute_shell(cmd, cwd=None):
    logging.debug('Running command ' + ' '.join(cmd))
    result = {
            "code": -1,
            "stdout" : "",
            "stderr" : ""
            }

    try:
        p = subprocess.Popen(cmd,
                   stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   preexec_fn=default_sigpipe,
                   cwd=cwd)
        stdout, stderr = p.communicate()

        result['code'] = p.returncode
        result['stdout'] = stdout or ''
        result['stderr'] = stderr or ''
    except:
        result['code'] = -1
        result['stderr'] = 'Shell execution error'

    return result




PD_TREND_API = "http://{host}:{port}/pd/api/v1/trend"

# FIXME the intervals can be configurable
FETCH_INTERVAL = 100 # ms
KILL_INTERVAL = 500 # ms

def fetch_data(service):
    while True:
        logging.debug("fetching data from pd rest api")

        # FIXME address can be configurable
        resp = requests.get(PD_TREND_API.format(host="127.0.0.1", port="8010"))
        data = resp.json()

        # update service status
        active_tikvs = list(filter(lambda tikv: tikv["state_name"] == "Up", data["stores"]))
        service.active_tikvs = active_tikvs
        service.exist_any_history = len(data["history"]["entries"]) != 0

        # notify all observer
        service.notify(data)

        timeunit.milliseconds.sleep(FETCH_INTERVAL)

def kill_node(service, killer_type):
    while True:
        if random.randint(0, 10) == 10 and service.tikv_can_be_killed:
            logging.info("oops, somebody will be unlucky and to be killed")
            killer = KillerFactory.new_killer(killer_type, service)
            killer.random_kill()
        else:
            logging.info("today is a lukcy day, no body will be killed")

        timeunit.milliseconds.sleep(KILL_INTERVAL)



class TiDBKillerService(object):
    def __init__(self):
        self._monitors = []
        self._exist_any_history = True
        self._active_tikvs = []


        self._data_thread = threading.Thread(target=fetch_data, args=(self,))
        self._data_thread.setName("data-thread")

        # FIXME killer type can be configurable
        self._killer_thread = threading.Thread(target=kill_node, args=(self, KillerTypes.COMPOSE))
        self._killer_thread.setName("killer-thread")

    @property
    def tikv_can_be_killed(self):
        # for easy case, here let the kill be not conccurent
        return len(self._monitors) == 0 and not self.exist_any_history and len(self.active_tikvs) >= 4

    @property
    def exist_any_history(self):
        return self._exist_any_history

    @exist_any_history.setter
    def exist_any_history(self, value):
        self._exist_any_history = value

    @property
    def active_tikvs(self):
        return self._active_tikvs

    @active_tikvs.setter
    def active_tikvs(self, value):
        self._active_tikvs = value

    def notify(self, data):
        for monitor in self._monitors:
            monitor.update(data)

    def register(self, monitor):
        self._monitors.append(monitor)

    def unregister(self, monitor):
        self._monitors.remove(monitor)

    def start(self):
        self._data_thread.start()
        self._killer_thread.start()

    def join(self):
        self._data_thread.join()
        self._killer_thread.join()

    def serve(self):
        self.start()
        self.join()



