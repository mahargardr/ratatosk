# setup.py

from setuptools import setup, find_packages

setup(
    name='ratatosk',
    version='0.1.1',
    description="This package can manipulate RAN files (e.g. Audit CM, and Get CM for certain MO)",
    author="Dewa Mahardika",
    author_email="dewamahardika499@gmail.com",
    packages=find_packages(),
    package_data={'':['config.json']},
    entry_points='''
        [console_scripts]
        ratatosk=ratatosk.cli:main
    ''',
)