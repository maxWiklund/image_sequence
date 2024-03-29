# -*- coding: utf-8 -*-
# Copyright (C) 2021  Max Wiklund
#
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from setuptools import setup
import image_sequence
import sys


REQUIRES = ["scandir"] if sys.version_info < (3, 4) else []

setup(
    name="image_sequence",
    version=image_sequence.__version__,
    packages=["image_sequence"],
    url="",
    license="Apache License 2.0",
    author="Max Wiklund",
    author_email="info@maxwiklund.com",
    description="Library for representing file sequences.",
    py_modules=["image_sequence"],
    install_requires=REQUIRES,
)
