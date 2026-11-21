# -*- coding: utf-8 -*-
# Part of Flectra. See LICENSE file for full copyright and licensing details.

RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: ALPHA,
                          BETA: BETA,
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# version_info format: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspired by Python's own sys.version_info, in order to be
# properly comparable using normal operators, for example:
#  (6,1,0,'beta',0) < (6,1,0,'candidate',1) < (6,1,0,'candidate',2)
#  (6,1,0,'candidate',2) < (6,1,0,'final',0) < (6,1,2,'final',0)
version_info = (3, 0, 0, FINAL, 0, '')
version = '.'.join(str(s) for s in version_info[:2]) + RELEASE_LEVELS_DISPLAY[version_info[3]] + str(version_info[4] or '') + version_info[5]
series = serie = major_version = '.'.join(str(s) for s in version_info[:2])

product_name = 'MoonWitness'
description = 'MoonWitness Server (powered by Flectra 3.0)'
long_desc = '''MoonWitness is an operational platform powered by the Flectra 3.0 Python ERP
and ORM engine. It combines first-party MoonWitness addons, host management,
and service orchestration with Flectra's modular web client, PostgreSQL ORM,
customizable reports, and XML-RPC interfaces.
'''
classifiers = """Development Status :: 5 - Production/Stable
License :: OSI Approved :: GNU Lesser General Public License v3

Programming Language :: Python
"""
url = 'https://github.com/A-L-L-A-H/flectra'
author = 'FlectraHQ, OpenERP S.A.'
author_email = 'info@flectrahq.com'
license = 'LGPL-3'

nt_service_name = "flectra-server-" + series.replace('~','-')
