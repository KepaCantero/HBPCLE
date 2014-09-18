'''setup.py'''

# pylint: disable=F0401,E0611,W0142

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import python_cle

from pip.req import parse_requirements
install_reqs = parse_requirements('requirements.txt')
from optparse import Option
options = Option("--workaround")
options.skip_requirements_regex = None
install_reqs = parse_requirements("./requirements.txt", options=options)
reqs = [str(ir.req) for ir in install_reqs]

config = {
    'description': 'Python Implementation of Closed Loop Engine',
    'author': 'mgevaert',
    'url': 'https://bbpteam.epfl.ch/project/spaces/display/HSP10/Neurorobotics+Platform+Home',
    'author_email': 'hinkel@fzi.de',
    'version': python_cle.__version__,
    'install_requires': reqs,
    'packages': ['python_cle'],
    'scripts': [],
    'name': 'python-cle',
    'include_package_data': True,
}

setup(**config)