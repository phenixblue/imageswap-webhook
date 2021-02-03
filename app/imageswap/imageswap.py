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

from flask import Flask, request, jsonify
from logging.handlers import MemoryHandler
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics
import base64
import config
import copy
import datetime
import json
import jsonpatch
import logging
import os
import re

app = Flask(__name__)

# Set Global variables
imageswap_namespace_name = os.getenv("IMAGESWAP_NAMESPACE_NAME", "imageswap-system")
imageswap_pod_name = os.getenv("IMAGESWAP_POD_NAME")
imageswap_disable_label = os.getenv("IMAGESWAP_DISABLE_LABEL", "k8s.twr.io/imageswap")

# Setup Prometheus Metrics for Flask app
metrics = PrometheusMetrics(app, defaults_prefix="imageswap")

# Static information as metric
metrics.info("app_info", "Application info", version="v1.2.0")

# Set logging config
log = logging.getLogger("werkzeug")
log.disabled = True
imageswap_log_level = os.getenv("IMAGESWAP_LOG_LEVEL", "INFO")
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

    app.logger.info("##################################################################")

    # Detect if "name" in object metadata
    # this was added because the request object for pods doesn't
    # include a "name" field in the object metadata. This is because generateName
    # occurs Server Side post-admission
    if "name" in workload_metadata:

        workload = modified_spec["request"]["object"]["metadata"]["name"]

    elif "generateName" in workload_metadata:

        workload = modified_spec["request"]["object"]["metadata"]["generateName"]

    else:

        workload = uid

    app.logger.debug(json.dumps(request.json))

    # Skip patching if disable label is found and set to "disable"
    if (
        "labels" in workload_metadata
        and imageswap_disable_label in workload_metadata["labels"]
        and workload_metadata["labels"][imageswap_disable_label] == "disabled"
    ):

        app.logger.info(f'Disable label "{imageswap_disable_label}=disabled" detected, skipping image swap.')
        needs_patch = False

    else:

        # Change workflow/json path based on K8s object type
        if workload_type == "Pod":

            for container_spec in modified_spec["request"]["object"]["spec"]["containers"]:

                app.logger.info(f"Processing container: {namespace}/{workload}")
                needs_patch = swap_image(container_spec)

            if "initContainers" in modified_spec["request"]["object"]["spec"]:

                for init_container_spec in modified_spec["request"]["object"]["spec"]["initContainers"]:

                    app.logger.info(f"Processing init-container: {namespace}/{workload}")
                    needs_patch = swap_image(init_container_spec)

        else:

            for container_spec in modified_spec["request"]["object"]["spec"]["template"]["spec"]["containers"]:

                app.logger.info(f"Processing container: {namespace}/{workload}")
                needs_patch = swap_image(container_spec)

            if "initContainers" in modified_spec["request"]["object"]["spec"]["template"]["spec"]:

                for init_container_spec in modified_spec["request"]["object"]["spec"]["template"]["spec"]["initContainers"]:

                    app.logger.info(f"Processing init-container: {namespace}/{workload}")
                    needs_patch = swap_image(init_container_spec)

    if needs_patch:

        app.logger.debug("Needs patch")
        app.logger.info("Diffing original request to modified request and generating JSONPatch")

        patch = jsonpatch.JsonPatch.from_diff(request_info["request"]["object"], modified_spec["request"]["object"])

        app.logger.info(f"JSON Patch: {patch}")

        admission_response = {
            "allowed": True,
            "uid": request_info["request"]["uid"],
            "patch": base64.b64encode(str(patch).encode()).decode(),
            "patchtype": "JSONPatch",
        }
        admissionReview = {
            "apiVersion": "admission.k8s.io/v1beta1",
            "kind": "AdmissionReview",
            "response": admission_response,
        }

    else:

        app.logger.debug("Doesn't need patch")
        admission_response = {
            "allowed": True,
            "uid": request_info["request"]["uid"],
        }

        admissionReview = {
            "apiVersion": "admission.k8s.io/v1beta1",
            "kind": "AdmissionReview",
            "response": admission_response,
        }

    app.logger.info("Sending Response to K8s API Server:")
    app.logger.info(json.dumps(admissionReview))

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

    app.logger.info(f"Swapping image definition for container spec: {name}")

    if image_prefix in image:

        app.logger.info("Internal image definition detected, nothing to do")

        return False

    else:

        if image_prefix[-1] == "-":
            new_image = image_prefix + image
        elif "/" not in image:
            new_image = image_prefix + re.sub(r"(^.*)", r"/\1", image)
        else:
            new_image = image_prefix + re.sub(r"(^.*/)+(.*)", r"/\2", image)

        app.logger.info(f"External image definition detected: {image}")
        app.logger.info(f"External image updated to Internal image: {new_image}")

        container_spec["image"] = new_image

        return True


################################################################################
################################################################################
################################################################################


def main():

    app.logger.info("ImageSwap v1.3.1-prerelease Startup")

    app.run(
        host="0.0.0.0", port=5000, debug=False, threaded=True, ssl_context=("./tls/cert.pem", "./tls/key.pem",),
    )


################################################################################
################################################################################
################################################################################

if __name__ == "__main__":

    main()
