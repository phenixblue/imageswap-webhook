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
# Test image definition/syntax scenarios ##################################
###########################################################################


@patch("imageswap.imageswap_mode", "MAPS")
@patch("imageswap.imageswap_maps_file", "./testing/map_files/map_file.conf")
class ImageFormats(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True
        imageswap.app.logger.setLevel("DEBUG")

    def tearDown(self):

        pass

    def test_image_format_image_only(self):

        """Method to test MAP based swap (image only: \"alpine\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "alpine"

        expected_image = "my.example.com/mirror-docker.io/alpine"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_image_tag(self):

        """Method to test MAP based swap (image+tag: \"nginx:latest\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "nginx:latest"

        expected_image = "my.example.com/mirror-docker.io/nginx:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_project_image(self):

        """Method to test MAP based swap (project+image: \"ubuntu/ubuntu\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "ubuntu/ubuntu"

        expected_image = "my.example.com/mirror-docker.io/ubuntu/ubuntu"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_project_image_tag(self):

        """Method to test MAP based swap (project+image+tag: \"ubuntu/ubuntu:latest\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "ubuntu/ubuntu:latest"

        expected_image = "my.example.com/mirror-docker.io/ubuntu/ubuntu:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    # Test registry+project+image

    def test_image_format_registry_project_image(self):

        """Method to test MAP based swap (registry+project+image: \"quay.io/solo/gloo\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "quay.io/solo/gloo"

        expected_image = "quay.example3.com/solo/gloo"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_registry_project_image_tag(self):

        """Method to test MAP based swap (registry+project+image+tag: \"quay.io/solo/gloo:v1.0\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "quay.io/solo/gloo:v1.0"

        expected_image = "quay.example3.com/solo/gloo:v1.0"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_registry_port_project_image_tag(self):

        """Method to test MAP based swap (registry+port+project+image+tag: \"gcr.io:443/istio/istiod:latest\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "gcr.io:443/istio/istiod:latest"

        expected_image = "default.example.com/istio/istiod:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_nested_project_image(self):

        """Method to test MAP based swap (nested project+image: \"some/random/test/without/registry-or-tag\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "some/random/test/without/registry-or-tag"

        expected_image = "my.example.com/mirror-docker.io/some/random/test/without/registry-or-tag"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_nested_project_image_tag(self):

        """Method to test MAP based swap (nested project+image+tag: \"some/random/test/without/registry-or-tag:latest\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "some/random/test/without/registry-or-tag:latest"

        expected_image = "my.example.com/mirror-docker.io/some/random/test/without/registry-or-tag:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_registry_nested_project_image_tag(self):

        """Method to test MAP based swap (registry+nested project+image+tag: \"myregistry.com/some/random/test/with/registry:latest\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "myregistry.com/some/random/test/with/registry:latest"

        expected_image = "default.example.com/some/random/test/with/registry:latest"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_registry_with_many_domain_levels(self):

        """Method to test MAP based swap (registry with more than 3 domain levels+project+image+tag: \"harbor.geo.k8s.twr.io/stuff/magtape:latest\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "harbor.geo.k8s.twr.io/stuff/magtape:latest"

        expected_image = "harbor.geo.k8s.twr.io/stuff/magtape:latest"
        result = imageswap.swap_image(container_spec)

        self.assertFalse(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_project_image_digest(self):

        """Method to test MAP based swap (project+image@digest: \"kindest/node@sha256:15d3b5c4f521a84896ed1ead1b14e4774d02202d5c65ab68f30eeaf310a3b1a7\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "kindest/node@sha256:15d3b5c4f521a84896ed1ead1b14e4774d02202d5c65ab68f30eeaf310a3b1a7"

        expected_image = "my.example.com/mirror-docker.io/kindest/node@sha256:15d3b5c4f521a84896ed1ead1b14e4774d02202d5c65ab68f30eeaf310a3b1a7"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)

    def test_image_format_library_image_with_dotted_tag(self):

        """Method to test MAP based swap (library image with tag that contains a ".": \"rabbitmq:3.8.18-management\")"""

        container_spec = {}
        container_spec["name"] = "test-container"
        container_spec["image"] = "rabbitmq:3.8.18-management"

        expected_image = "my.example.com/mirror-docker.io/rabbitmq:3.8.18-management"
        result = imageswap.swap_image(container_spec)

        self.assertTrue(result)
        self.assertEqual(container_spec["image"], expected_image)


if __name__ == "__main__":
    unittest.main()
