from setuptools import setup, find_packages
from datetime import datetime
from pathlib import Path


version = 0.1
with Path('README.md').open() as readme:
    readme = readme.read()


setup(
    name='subproc_mgr',
    version=version if isinstance(version, str) else str(version),
    keywords="subprocess,lifetime", # keywords of your project that separated by comma ","
    description='A service to spawn and manage long-running child processes, following the lifecycle management of "child processes are attached to parent processes".', # a concise introduction of your project
    long_description=readme,
    long_description_content_type="text/markdown",
    license='mit',
    python_requires='>=3.9',
    url='https://github.com/thautwarm/subproc_mgr',
    author='thautwarm',
    author_email='twshere@outlook.com',
    packages=find_packages(),
    entry_points={"console_scripts": []},
    install_requires=[
        'psutil',
        'aiohttp',
        'wisepy2'
    ], # dependencies
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    zip_safe=False,
)


