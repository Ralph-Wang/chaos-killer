#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time


class RepoterTypes(object):
    DUMMY = "dummy"
    LOCAL_FILE = "local"
    EMAIL = "email"

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
        report_file = "chaos.report.{0}.txt".format(time.strftime("%Y%m%d.%H%M%S"))
        logging.info("trying to report to a file - %s", report_file)
        with open(report_file, "w") as report_file_obj:
            left_active_tikvs = len(filter(lambda tikv: tikv["state_name"] == "Up", status["final_status"]["stores"]))

            report_file_obj.write("""
                    migrate_elasped: {0} seconds
                    total_migrated_regions: {1}
                    left_active_tikvs: {2}
                    """.format(status["migrate_elapsed_secs"],
                        status["total_migrated_regions"],
                        left_active_tikvs
                        ))
            report_file_obj.flush()
            pass



class EmailReporter(Reporter):

    def reporter(self, status):
        raise NotImplementedError("FIXME not implement it yet")

class ReporterFactory(object):
    types = {
            RepoterTypes.DUMMY: DummyReporter,
            RepoterTypes.LOCAL_FILE: LocalFileReporter,
            RepoterTypes.EMAIL: EmailReporter
            }

    @classmethod
    def new_reporter(cls, reporter_type):
        return cls.types[reporter_type]()
