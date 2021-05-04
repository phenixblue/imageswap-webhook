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

import base64
import json
import os
import sys
import unittest
from unittest.mock import patch

sys.path.append("./app/imageswap")
import imageswap

os.environ["IMAGESWAP_POD_NAME"] = "imageswap-abc1234"
os.environ["IMAGESWAP_CLUSTER_NAME"] = "test-cluster"
os.environ["IMAGESWAP_LOG_LEVEL"] = "DEBUG"
os.environ["IMAGE_PREFIX"] = "jmsearcy"


class RoutePatterns(unittest.TestCase):
    def setUp(self):

        self.app = imageswap.app.test_client()
        self.app.testing = True

    def tearDown(self):

        pass

    @patch("imageswap.imageswap_pod_name", "imageswap-abc1234")
    def test_healthz(self):

        """Method to test healthz route"""

        result = self.app.get("/healthz")

        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data)["health"], "ok")
        self.assertEqual(json.loads(result.data)["pod_name"], "imageswap-abc1234")

    def test_root_deploy_noswap(self):

        """Method to test root route with deployment request that should not swap the image definition"""

        with open("./testing/deployments/test-deploy01.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertNotIn("patch", json.loads(result.data)["response"])
            self.assertNotIn("patchtype", json.loads(result.data)["response"])
            self.assertEqual(json.loads(result.data)["response"]["uid"], "d6a539c0-8605-4923-8b57-ed54313e359a")

    def test_root_deploy_swap_disabled(self):

        """Method to test root route with deployment request where disable label is used"""

        with open("./testing/deployments/test-deploy05.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertNotIn("patch", json.loads(result.data)["response"])
            self.assertNotIn("patchtype", json.loads(result.data)["response"])
            self.assertEqual(json.loads(result.data)["response"]["uid"], "a1b56548-759b-4d44-afd1-d4aae8714d04")

    def test_root_deploy_swap_container(self):

        """Method to test root route with deployment request that should swap the primary container image definition"""

        with open("./testing/deployments/test-deploy02.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvY29udGFpbmVycy8wL2ltYWdlIiwgInZhbHVlIjogImptc2VhcmN5L2hlbGxvLWt1YmVybmV0ZXM6MS41In1d",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "29df64b9-da70-4044-ac07-4fcff7c3eb5c")

    def test_root_deploy_swap_init(self):

        """Method to test root route with deployment request that should swap the init-container image definition"""

        with open("./testing/deployments/test-deploy03.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvaW5pdENvbnRhaW5lcnMvMC9pbWFnZSIsICJ2YWx1ZSI6ICJqbXNlYXJjeS9oZWxsby1rdWJlcm5ldGVzOjEuNSJ9XQ==",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "2f95b6dc-0dd9-4729-9cd3-d5577d2b0621")

    def test_root_deploy_swap_both(self):

        """Method to test root route with deployment request that should swap both the primary container and init-container image definitions"""

        with open("./testing/deployments/test-deploy04.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            # Decode base64 encoded patch string into Python List of Dicts. This allows for comparison without the List order impacting assertion
            result_patch = base64.b64decode(json.loads(result.data)["response"]["patch"]).decode()
            expected_patch = "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvaW5pdENvbnRhaW5lcnMvMC9pbWFnZSIsICJ2YWx1ZSI6ICJqbXNlYXJjeS9oZWxsby1rdWJlcm5ldGVzOjEuNSJ9LCB7Im9wIjogInJlcGxhY2UiLCAicGF0aCI6ICIvc3BlYy90ZW1wbGF0ZS9zcGVjL2NvbnRhaW5lcnMvMC9pbWFnZSIsICJ2YWx1ZSI6ICJqbXNlYXJjeS9oZWxsby1rdWJlcm5ldGVzOjEuNSJ9XQ=="
            expected_patch_decoded = base64.b64decode(expected_patch).decode()

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertCountEqual(result_patch, expected_patch_decoded)
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "2d213641-c136-49d5-b162-a0d2593639f7")

    def test_root_pod_noswap(self):

        """Method to test root route with pod request that should not swap the image definition"""

        with open("./testing/pods/test-pod01.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertNotIn("patch", json.loads(result.data)["response"])
            self.assertNotIn("patchtype", json.loads(result.data)["response"])
            self.assertEqual(json.loads(result.data)["response"]["uid"], "60df4b0b-8856-4ce7-9fb3-bc8034856995")

    def test_root_pod_swap_container(self):

        """Method to test root route with pod request that should swap the primary container image definition"""

        with open("./testing/pods/test-pod02.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL2NvbnRhaW5lcnMvMC9pbWFnZSIsICJ2YWx1ZSI6ICJqbXNlYXJjeS9oZWxsby1rdWJlcm5ldGVzOjEuNSJ9XQ==",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "8350e416-408e-4d89-b219-4c6811a2e099")

    def test_root_pod_swap_init(self):

        """Method to test root route with pod request that should swap the init-container image definition"""

        with open("./testing/pods/test-pod03.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL2luaXRDb250YWluZXJzLzAvaW1hZ2UiLCAidmFsdWUiOiAiam1zZWFyY3kvaGVsbG8ta3ViZXJuZXRlczoxLjUifV0=",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "82a5b842-0cfb-4293-abea-0c2603d8a16a")

    def test_root_pod_swap_both(self):

        """Method to test root route with pod request that should swap both the primary container and init-container image definitions"""

        with open("./testing/pods/test-pod04.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            # Decode base64 encoded patch string into Python List of Dicts. This allows for comparison without the List order impacting assertion
            result_patch = base64.b64decode(json.loads(result.data)["response"]["patch"]).decode()
            expected_patch = "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL2luaXRDb250YWluZXJzLzAvaW1hZ2UiLCAidmFsdWUiOiAiam1zZWFyY3kvaGVsbG8ta3ViZXJuZXRlczoxLjUifSwgeyJvcCI6ICJyZXBsYWNlIiwgInBhdGgiOiAiL3NwZWMvY29udGFpbmVycy8wL2ltYWdlIiwgInZhbHVlIjogImptc2VhcmN5L2hlbGxvLWt1YmVybmV0ZXM6MS41In1d"
            expected_patch_decoded = base64.b64decode(expected_patch).decode()

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertCountEqual(result_patch, expected_patch_decoded)
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "ffeb2e4a-a440-4f70-90cb-9e960f7471c4")

    def test_root_pod_swap_noslash(self):

        """Method to test root route with pod request that should swap the primary container image definition that doesn't include a slash"""

        with open("./testing/pods/test-pod05.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL2NvbnRhaW5lcnMvMC9pbWFnZSIsICJ2YWx1ZSI6ICJqbXNlYXJjeS9uZ2lueDpsYXRlc3QifV0=",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "2ca21f3f-a77f-4145-b7ac-bf656a976f46")

    @patch.dict(os.environ, {"IMAGE_PREFIX": "jmsearcy-"})
    def test_root_pod_swap_dash(self):

        """Method to test root route with pod request that should swap the primary container image definition where the IMAGE_PREFIX ends with a '-'"""

        with open("./testing/deployments/test-deploy02.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL3RlbXBsYXRlL3NwZWMvY29udGFpbmVycy8wL2ltYWdlIiwgInZhbHVlIjogImptc2VhcmN5LXBhdWxib3V3ZXIvaGVsbG8ta3ViZXJuZXRlczoxLjUifV0=",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "29df64b9-da70-4044-ac07-4fcff7c3eb5c")

    def test_root_pod_swap_generatename(self):

        """Method to test root route with pod request using generateName field that should swap the primary container image definition"""

        with open("./testing/pods/test-pod06.json") as json_file:

            request_object_json = json.load(json_file)

            result = self.app.post("/", data=json.dumps(request_object_json), headers={"Content-Type": "application/json"},)

            self.assertEqual(result.status_code, 200)
            self.assertEqual(json.loads(result.data)["response"]["allowed"], True)
            self.assertEqual(
                json.loads(result.data)["response"]["patch"],
                "W3sib3AiOiAicmVwbGFjZSIsICJwYXRoIjogIi9zcGVjL2NvbnRhaW5lcnMvMC9pbWFnZSIsICJ2YWx1ZSI6ICJqbXNlYXJjeS9uZ2lueDpsYXRlc3QifV0=",
            )
            self.assertEqual(json.loads(result.data)["response"]["patchtype"], "JSONPatch")
            self.assertEqual(json.loads(result.data)["response"]["uid"], "1ee8aaf2-d96b-401e-9db6-76282587df24")


if __name__ == "__main__":
    unittest.main()
