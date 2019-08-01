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

from .reporter import *


class KillerTypes(object):
    COMPOSE = "docker-compose"
    ANSIBLE= "ansible"
    K8S = "k8s"
    DUMMY = "dummy"


class Killer(object):

    def __init__(self, service):
        self._service = service

    def random_kill(self):
        logging.info("pick a poor node from %s", [tikv["address"] for tikv in self._service.active_tikvs])
        poor_man = random.choice(self._service.active_tikvs)

        logging.info("try to kill the node %s", poor_man["address"])
        self.kill(poor_man)
        monitor = Monitor(self._service, poor_man, ReporterFactory.new_reporter(RepoterTypes.LOCAL_FILE)) # FIXME make reporter configurable
        self._service.register(monitor)

    def kill(self, node):
        raise NotImplementedError("not implement in the base Killer class")


class DockerComposeKiller(Killer):

    def kill(self, node):
        logging.info("kill for docker-compose mode")
        host, port = node["address"].split(":", 1)
        container_id = subprocess.check_output("docker ps|grep %s|awk '{print $1b}'" % host, shell=True)

        logging.info("trying to stop the container - %s", container_id)
        killed_container_id = subprocess.check_output("docker stop %s" % container_id, shell=True)

        logging.info("container have been killed - %s" % killed_container_id)

class DummyKiller(Killer):

    def kill(self, node):
        logging.info("dummy killer will do nothing")


class AnsibleKiller(Killer):

    def kill(self, node):
        raise NotImplementedError("not implement the ansible killer")

class K8sKiller(Killer):

    def kill(self, node):
        raise NotImplementedError("not implement the k8s killer")


class KillerFactory(object):

    types = {
            KillerTypes.COMPOSE: DockerComposeKiller,
            KillerTypes.ANSIBLE: AnsibleKiller,
            KillerTypes.K8S: K8sKiller,
            KillerTypes.DUMMY: DummyKiller
            }

    @classmethod
    def new_killer(cls, killer_type, service):
        return cls.types[killer_type](service)

class Monitor(object):

    def __init__(self, service, killed_node, reporter):
        self._service = service
        self._reporter = reporter

        self._monitor_status = {
                "migrate_elapsed_secs": 0
                }
        self._start_in_secs = time.time()
        self._killed_node = killed_node
        self._origin_region_count = killed_node["region_count"]
        self._killed_node_id = killed_node["id"]

    def update(self, data):
        logging.info("update data in monitor %s, %s", self, data)

        migrated_region_count = 0
        for entry in data["history"]["entries"]:
            if entry["from"] == self._killed_node_id and entry["kind"] == "region":
                migrated_region_count += entry["count"]

        logging.info("already migrated regions count - %s", migrated_region_count)
        if self._origin_region_count == migrated_region_count:
            # the elapsed metric may not be so accurate as the INTERVAL exists.
            self._monitor_status["migrate_elapsed_secs"] = time.time() - self._start_in_secs
            self._monitor_status["total_migrated_regions"] = migrated_region_count
            self._monitor_status["final_status"] = data
            self.done()

    def done(self):
        self._service.unregister(self)
        self._reporter.report(self._monitor_status)
