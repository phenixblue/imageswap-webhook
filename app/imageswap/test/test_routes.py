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

import json
import sys
import unittest
from unittest.mock import patch

sys.path.append("./app/imageswap")
import imageswap

class TestRoutes(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True

    def tearDown(self):

        pass

    def test_healthz(self):

        """Method to test webhook /healthz route"""

        result = self.app.get("/healthz")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data)["health"], "ok")
        self.assertEqual(json.loads(result.data)["pod_name"], "imageswap-abc1234")

    def test_root_deploy_noswap(self):

        """Method to test root route with request that should swap the image definition"""

        with open("./testing/deployments/test-deploy01.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post(
                "/",
                data=json.dumps(request_object_json),
                headers={"Content-Type": "application/json"},
            )

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertNotIn("patch", json.loads(result.data)["response"])
            self.assertNotIn("patchtype", json.loads(result.data)["response"])
            self.assertEqual(json.loads(result.data)["response"]["uid"], "96ab6176-dc7e-11e8-84d0-da6ee68491b2")
        
    def test_root_deploy_swap_container(self):

        """Method to test root route with request that should swap the image definition"""

        with open("./testing/deployments/test-deploy02.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post(
                "/",
                data=json.dumps(request_object_json),
                headers={"Content-Type": "application/json"},
            )

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(json.loads(result.data)["response"]["patch"], "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvY29udGFpbmVycy8wL2ltYWdlIiwgInZhbHVlIjogImptc2VhcmN5L2hlbGxvLWt1YmVybmV0ZXM6MS41In1d")
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "96ab6176-dc7e-11e8-84d0-da6ee68491b2")

    def test_root_deploy_swap_init(self):

        """Method to test root route with request that should swap the image definition"""

        with open("./testing/deployments/test-deploy03.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post(
                "/",
                data=json.dumps(request_object_json),
                headers={"Content-Type": "application/json"},
            )

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(json.loads(result.data)["response"]["patch"], "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvY29udGFpbmVycy8wL2ltYWdlIiwgInZhbHVlIjogImptc2VhcmN5L2hlbGxvLWt1YmVybmV0ZXM6MS41In1d")
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "96ab6176-dc7e-11e8-84d0-da6ee68491b2")

    def test_root_deploy_swap_both(self):

        """Method to test root route with request that should swap the image definition"""

        with open("./testing/deployments/test-deploy03.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post(
                "/",
                data=json.dumps(request_object_json),
                headers={"Content-Type": "application/json"},
            )

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(json.loads(result.data)["response"]["patch"], "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvY29udGFpbmVycy8wL2ltYWdlIiwgInZhbHVlIjogImptc2VhcmN5L2hlbGxvLWt1YmVybmV0ZXM6MS41In1d")
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "96ab6176-dc7e-11e8-84d0-da6ee68491b2")

    def test_root_pod_noswap(self):

        """Method to test root route with request that should swap the image definition"""

        with open("./testing/pods/test-pod01.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post(
                "/",
                data=json.dumps(request_object_json),
                headers={"Content-Type": "application/json"},
            )

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertNotIn("patch", json.loads(result.data)["response"])
            self.assertNotIn("patchtype", json.loads(result.data)["response"])
            self.assertEqual(json.loads(result.data)["response"]["uid"], "96ab6176-dc7e-11e8-84d0-da6ee68491b2")

if __name__ == "__main__":
    unittest.main()