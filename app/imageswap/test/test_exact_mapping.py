#!/usr/bin/env python

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
import sys
import unittest
from unittest.mock import patch

sys.path.append("./app/imageswap")
import imageswap

###########################################################################
# Test image tag mapping scenarios ########################################
###########################################################################


@patch("imageswap.imageswap_mode", "EXACT")
@patch("imageswap.imageswap_maps_file", "./testing/map_files/map_file.conf")
class ExactMapping(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True
        imageswap.app.logger.setLevel("DEBUG")

    def tearDown(self):

        pass

    def test_map_exact_helloworld(self):

        """Method to test Map File config (default swap map has no value)"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_exact.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "hello-world"

        expected_image = "myownrepo.example.com/base/public-image-cache:hello-world"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


    def test_map_exact_ubuntu(self):

        """Method to test Map File config (default swap map has no value)"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_exact.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "ubutun:18.04"

        expected_image = "myownrepo.example.com/base/public-image-cache:ubuntu_18.04"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


    def test_map_mysqlserver(self):

        """Method to test Map File config (default swap map has no value)"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_exact.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "mysql/mysql-server"

        expected_image = "myownrepo.example.com/base/public-image-cache:mysql_mysql-server"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


    def test_map_mysqlserver56(self):

        """Method to test Map File config (default swap map has no value)"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_exact.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "mysql/mysql-server:5.6"

        expected_image = "myownrepo.example.com/base/public-image-cache:mysql_mysql-server_5.6"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


    def test_map_exact_nvcr(self):

        """Method to test Map File config (default swap map has no value)"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_exact.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "nvcr.io/nvidia:k8s-device-plugin_v0.9.0"

        expected_image = "myownrepo.example.com/base/private-image-cache:nvcr.io_nvidia_k8s-device-plugin_v0.9.0"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)



if __name__ == "__main__":
    unittest.main()
