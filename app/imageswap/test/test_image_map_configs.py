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
# Test map config scenarios ###############################################
###########################################################################


@patch("imageswap.imageswap_mode", "MAPS")
@patch("imageswap.imageswap_maps_file", "./testing/map_files/map_file_no_default.conf")
class BadConfig(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True
        imageswap.app.logger.setLevel("DEBUG")

    def tearDown(self):

        pass

    def test_map_config_no_default(self):

        """Method to test Map File config (no default swap map)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "default.io/paulbower/hello-kubernetes:1.5"

        expected_image = "default.io/paulbower/hello-kubernetes:1.5"
        result = imageswap.swap_image(container_spec)

        self.assertFalse(result)
        self.assertEqual(container_spec["image"], expected_image)


@patch("imageswap.imageswap_mode", "MAPS")
@patch("imageswap.imageswap_maps_file", "./testing/map_files/map_file.conf")
class GoodConfig(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True
        imageswap.app.logger.setLevel("DEBUG")

    def tearDown(self):

        pass

    def test_map_config_default(self):

        """Method to test Map File config (default swap map)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "default.io/paulbower/hello-kubernetes:1.5"

        expected_image = "default.example.com/paulbower/hello-kubernetes:1.5"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_default_empty(self):

        """Method to test Map File config (default swap map has no value)"""

        imageswap.imageswap_maps_file = "./testing/map_files/map_file_empty_default.conf"

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "john.io/paulbower/hello-kubernetes:1.5"

        expected_image = "john.io/paulbower/hello-kubernetes:1.5"
        result = imageswap.swap_image(container_spec)

        self.assertFalse(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_with_trailing_dash(self):

        """Method to test Map File config (map value with trailing "-")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "docker.io/tmobile/magtape:latest"

        expected_image = "my.example.com/mirror-docker.io/tmobile/magtape:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_with_path_suffix(self):

        """Method to test Map File config (map value with path suffix)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "gitlab.com/tmobile/pie/proxyman:latest"

        expected_image = "registry.example.com/gitlab/tmobile/pie/proxyman:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_with_no_value(self):

        """Method to test Map File config (map with no value)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "cool.io:443/istio/istiod:latest"

        expected_image = "cool.io:443/istio/istiod:latest"
        result = imageswap.swap_image(container_spec)

        self.assertFalse(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_noswap_wildcard(self):

        """Method to test Map File config (match of pattern in noswap_wildcard)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "registry.external.twr.io:443/istio/istiod:latest"

        expected_image = "registry.external.twr.io:443/istio/istiod:latest"
        result = imageswap.swap_image(container_spec)

        self.assertFalse(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_noswap_wildcard_override(self):

        """Method to test Map File config (map that overrides matched pattern in noswap_wildcard)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "registry.internal.twr.io:443/istio/istiod:latest"

        expected_image = "registry.example.com:443/istio/istiod:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_noswap_with_extra_space(self):

        """Method to test Map File config (noswap_wildcard pattern with extra space after comma)"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "walrus.io/test/test:latest"

        expected_image = "walrus.io/test/test:latest"
        result = imageswap.swap_image(container_spec)

        self.assertFalse(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_map_config_with_library_image(self):
    
        """Method to test Map File config (map with library registry)"""
    
        imageswap.imageswap_maps_file = "./testing/map_files/map_file_library_image.conf"
    
        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "nginx:latest"
    
        expected_image = "harbor.example.com/library/nginx:latest"
        result = imageswap.swap_image(container_spec)
    
        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


if __name__ == "__main__":
    unittest.main()
