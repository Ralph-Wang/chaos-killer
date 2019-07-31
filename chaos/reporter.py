#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


class RepoterTypes(object):
    DUMMY = "dummy"
    LOCAL_FILE = "local"
    EMAIL = "email"

class ReporterFactory(object):
    types = {
            RepoterTypes.DUMMY: DummyReporter,
            RepoterTypes.LOCAL_FILE: LocalFileReporter,
            RepoterTypes.EMAIL: EmailReporter
            }

    @classmethod
    def new_reporter(cls, reporter_type):
        return cls.types[reporter_type]()

class Reporter(object):

    def __init__(self):
        pass

    def report(self, status):
        raise NotImplementedError("reporte is not implemented in base class")


class DummyReporter(Reporter):

    def report(self, status):
        logging.info("dummy reporter only record the origin status in the logs -- %s", status)


class LocalFileReporter(Reporter):

    def report(self, status):
        raise NotImplementedError("FIXME not implement it yet")



class EmailReporter(Reporter):

    def reporter(self, status):
        raise NotImplementedError("FIXME not implement it yet")
