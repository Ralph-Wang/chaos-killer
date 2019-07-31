#!/usr/bin/env python
# -*- coding: utf-8 -*-

import chaos.service as service
import logging


logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(threadName)s] [%(levelname)s] [%(pathname)s:%(lineno)d] %(message)s')


service.TiDBKillerService().serve()
