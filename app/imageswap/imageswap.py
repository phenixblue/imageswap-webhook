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

from config import BaseConfig
from flask import Flask, request, jsonify
from logging.handlers import MemoryHandler
from pprint import pprint
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics
import base64
import copy
import datetime
import json
import jsonpatch
import logging
import os
import re

app = Flask(__name__)

# Set Global variables
imageswap_namespace_name = os.environ["IMAGESWAP_NAMESPACE_NAME"]
imageswap_pod_name = os.environ["IMAGESWAP_POD_NAME"]

# Setup Prometheus Metrics for Flask app
metrics = PrometheusMetrics(app, defaults_prefix="imageswap")

# Static information as metric
metrics.info("app_info", "Application info", version="v1.2.0")

# Set logging config
log = logging.getLogger("werkzeug")
log.disabled = True
imageswap_log_level = os.environ["IMAGESWAP_LOG_LEVEL"]
app.logger.setLevel(imageswap_log_level)

################################################################################
################################################################################
################################################################################


@app.route("/", methods=["POST"])
def mutate():

    request_info = request.json
    modified_spec = copy.deepcopy(request_info)
    uid = modified_spec["request"]["uid"]
    workload_metadata = modified_spec["request"]["object"]["metadata"]
    workload_type = modified_spec["request"]["kind"]["kind"]
    namespace = modified_spec["request"]["namespace"]
    needs_patch = False

    print("")
    print("##################################################################")
    print("")

    # Detect if "name" in object metadata
    # this was added because the request object for pods don't
    # include a "name" field in the object metadata. This is because generateName
    # occurs Server Side post-admission
    if "name" in workload_metadata:

        workload = modified_spec["request"]["object"]["metadata"]["name"]

    elif "generateName" in workload_metadata:

        workload = modified_spec["request"]["object"]["metadata"]["generateName"]

    else:

        workload = uid

    pprint(request_info)

    # Change workflow/json path based on K8s object type
    if workload_type == "Pod":

        for container_spec in modified_spec["request"]["object"]["spec"]["containers"]:

            print("[INFO] - Processing container: {}/{}".format(namespace, workload))
            needs_patch = swap_image(container_spec)

        if "initContainer" in modified_spec["request"]["object"]["spec"]:

            for init_container_spec in modified_spec["request"]["object"]["spec"]["initContainer"]:

                print("[INFO] - Processing init-container: {}/{}".format(namespace, workload))
                needs_patch = swap_image(init_container_spec)

    else:

        for container_spec in modified_spec["request"]["object"]["spec"]["template"]["spec"]["containers"]:

            print("[INFO] - Processing container: {}/{}".format(namespace, workload))
            needs_patch = swap_image(container_spec)

        if "initContainer" in modified_spec["request"]["object"]["spec"]["template"]["spec"]:

            for init_container_spec in modified_spec["request"]["object"]["spec"]["template"]["spec"]["initContainer"]:

                print("[INFO] - Processing init-container: {}/{}".format(namespace, workload))
                needs_patch = swap_image(init_container_spec)

    if needs_patch:

        print("[DEBUG] -Doesn't need patch")

        print("[INFO] - Diffing original request to modified request and generating JSONPatch")

        patch = jsonpatch.JsonPatch.from_diff(request_info["request"]["object"], modified_spec["request"]["object"])

        print("[INFO] - JSON Patch: {}".format(patch))

        admission_response = {
            "allowed": True,
            "uid": request_info["request"]["uid"],
            "patch": base64.b64encode(str(patch).encode()).decode(),
            "patchtype": "JSONPatch",
        }
        admissionReview = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": admission_response,
        }

    else:

        print("[DEBUG] -Doesn't need patch")
        admission_response = {
            "allowed": True,
            "uid": request_info["request"]["uid"],
        }

        admissionReview = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": admission_response,
        }

    print("[INFO] - Sending Response to K8s API Server:")
    pprint(admissionReview)
    return jsonify(admissionReview)


################################################################################
################################################################################
################################################################################


@app.route("/healthz", methods=["GET"])
def healthz():

    """Function to return health info for app"""

    health_response = {
        "pod_name": imageswap_pod_name,
        "date_time": str(datetime.datetime.now()),
        "health": "ok",
    }

    # Return JSON formatted response object
    return jsonify(health_response)


################################################################################
################################################################################
################################################################################


def swap_image(container_spec):

    image_prefix = os.environ["IMAGE_PREFIX"]
    name = container_spec["name"]
    image = container_spec["image"]

    print("[INFO] - Swapping image definition for container spec: {}".format(name))

    if image_prefix in image:

        print("[INFO] - Internal image definition detected, nothing to do")

        return False

    else:

        if "/" not in image:
            new_image = image_prefix + re.sub(r"(^.*)", r"/\1", image)
        else:
            new_image = image_prefix + re.sub(r"(^.*/)+(.*)", r"/\2", image)

        print("[INFO] - External image definition detected: {}".format(image))
        print("[INFO] - External image updated to Internal image: {}".format(new_image))

        container_spec["image"] = new_image

        return True


################################################################################
################################################################################
################################################################################


def main():

    app.logger.info("ImageSwap Startup")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        ssl_context=(f"{BaseConfig.imageswap_tls_path}/cert.pem", f"{BaseConfig.imageswap_tls_path}/key.pem",),
    )


################################################################################
################################################################################
################################################################################

if __name__ == "__main__":

    main()
