#!/usr/bin/env python
##
# See the file COPYRIGHT for copyright information.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

from __future__ import print_function

from os import listdir, environ as environment
from os.path import dirname, join as joinpath
from itertools import chain
from setuptools import setup, find_packages as find_packages
from pip.req import parse_requirements



#
# Utilities
#

def version():
    """
    Compute the version number.
    """

    base_version = "0.2b"

    full_version = base_version

    return full_version



#
# Options
#

description = "Ranger Incident Management System"

long_description = file(joinpath(dirname(__file__), "README.rst")).read()

classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Twisted",
    "Intended Audience :: Information Technology",
    "Intended Audience :: Other Audience",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 2 :: Only",
    "Topic :: Office/Business",
]



#
# Dependencies
#

requirements_dir = joinpath(dirname(__file__), "requirements")


def read_requirements(reqs_filename):
    return [
        str(r.req) for r in
        parse_requirements(joinpath(requirements_dir, reqs_filename))
    ]


setup_requirements = []

install_requirements = read_requirements("base.txt")

extras_requirements = dict(
    (reqs_filename[4:-4], read_requirements(reqs_filename))
    for reqs_filename in listdir(requirements_dir)
    if reqs_filename.startswith("opt_") and reqs_filename.endswith(".txt")
)

# Requirements for development and testing
develop_requirements = read_requirements("develop.txt")

if environment.get("IMS_DEVELOP", "false") == "true":
    install_requirements.extend(develop_requirements)
    install_requirements.extend(chain(*extras_requirements.values()))



#
# Set up Extension modules that need to be built
#

extensions = []



#
# Run setup
#

def doSetup():
    # Write version file
    version_string = version()
    version_filename = joinpath(dirname(__file__), "ims", "version.py")
    version_file = file(version_filename, "w")
    try:
        version_file.write(
            'version = "{0}"\n\n'.format(version_string)
        )
        # version_file.write(
        #     "setup_requirements = {0!r}\n".format(setup_requirements)
        # )
        # version_file.write(
        #     "install_requirements = {0!r}\n".format(install_requirements)
        # )
    finally:
        version_file.close()

    setup(
        name="ranger-ims",
        version=version_string,
        description=description,
        long_description=long_description,
        url="https://github.com/burningmantech/ranger-ims",
        classifiers=classifiers,
        author="Wilfredo S\xe1nchez Vega",
        author_email="tool@burningman.com",
        license="Apache License, Version 2.0",
        platforms=["all"],
        packages=find_packages(),
        package_data={},
        scripts=["bin/imsd"],
        data_files=[],
        ext_modules=extensions,
        py_modules=[],
        setup_requires=setup_requirements,
        install_requires=install_requirements,
        extras_require=extras_requirements,
    )



#
# Main
#

if __name__ == "__main__":
    doSetup()
