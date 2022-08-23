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

import os

# Set Global variables
imageswap_tls_path = "/tls"
imageswap_tls_key_name = os.getenv("IMAGESWAP_TLS_KEY_NAME", "tls.cert")
imageswap_tls_cert_name = os.getenv("IMAGESWAP_TLS_CERT_NAME", "tls.key")

# Gunicorn config
bind = ":5000"
workers = 2
threads = 2
certfile = f"{imageswap_tls_path}/{imageswap_tls_cert_name}"
keyfile = f"{imageswap_tls_path}/{imageswap_tls_key_name}"
