#!/usr/bin/env bash

# Copyright 2020 The WebRoot, Inc.
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
#
# This is based on existing work from the MagTape project: 
# https://github.com/tmobile/magtape

source ./testing/export-env.sh

# Run tests and get coverage
coverage run -m unittest discover -v -s app/imageswap/test/

# Generate and output coverage report
coverage report --include app/imageswap/imageswap.py