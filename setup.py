#!/usr/bin/env python
import glob
from setuptools import setup

setup(name='emfmcp',
      version='0.1',
      description='emfcamp master control program for tilda badges',
      long_description=open('README.md').read(),
      author='EMF Badge Monkeys',
      author_email='hello@emfcamp.org',
      url='http://www.emfcamp.org',
      packages=['emfmcp', 'emfgateway'],
      scripts=glob.glob('bin/*.py'),
      install_requires=[
          "tornado >= 4.0.1",
          "pyserial >= 2.7",
          "structlog >= 0.4.2",
          "PyDispatcher >= 2.0.3",
      ],
      )
