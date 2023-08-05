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

import sys
import unittest
from unittest.mock import patch

sys.path.append("./app/imageswap")
import imageswap

###########################################################################
# Test image tag mapping scenarios ########################################
###########################################################################


@patch("imageswap.imageswap_mode", "MAPS")
@patch("imageswap.imageswap_maps_file", "./testing/map_files/map_file.conf")
class ReplaceMapping(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True
        imageswap.app.logger.setLevel("DEBUG")

    def tearDown(self):

        pass

    def test_map_default(self):

        """Method to test that default mapping is working for config files with [REPLACE] entries"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "any-image"

        expected_image = "default.example.com/any-image"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_host(self):

        """Method to test that host based mapping is working for config files with [REPLACE] entries"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "nvcr.io/any-image"

        expected_image = "harbor.example.com/any-image"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_exact_redis(self):

        """Method to test exact mapping is working for config files with [REPLACE] entries"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "redis"

        expected_image = "myownrepo.example.com/base/public-image-cache:redis"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_replace_prefix(self):

        """Method to test replace mapping where we match using a prefix"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "hello-world"

        expected_image = "myownrepo.example.com/base/public-image-cache/hello-world"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_replace_prefix_suffix(self):

        """Method to test replace mapping where we match using a prefix and a suffix"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "ubutun:18.04"

        expected_image = "myownrepo.example.com/base/ubutun:18.04"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_replace_suffix(self):

        """Method to test replace mapping where we match using a suffix"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "mysql/mysql-server:5.6"

        expected_image = "myownrepo.example.com/base/public-image-cache/mysql-server:5.6"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_replace_substring(self):

        """Method to test replace mapping where we match using a substring"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "nvcr.io/nvidia:k8s-device-plugin_v0.9.0"

        expected_image = "myownrepo.example.com/base/nvidia:k8s-device-plugin_v0.9.0"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_replace_single_char(self):

        """Method to test replace mapping where we use '?' to match any single character"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "hello:v1.1"

        expected_image = "myownrepo.example.com/base/public-image-cache/hello:v1.1"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_replace_unchanged(self):

        """Method to test replace when the result has not changed from the original"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_replace.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "auto"

        expected_image = "auto"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


if __name__ == "__main__":
    unittest.main()
