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

from typing import IO
from flask import Flask, request, jsonify
from logging.handlers import MemoryHandler
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
import fnmatch

app = Flask(__name__)

# Set Global variables
imageswap_namespace_name = os.getenv("IMAGESWAP_NAMESPACE_NAME", "imageswap-system")
imageswap_pod_name = os.getenv("IMAGESWAP_POD_NAME")
imageswap_disable_label = os.getenv("IMAGESWAP_DISABLE_LABEL", "k8s.twr.io/imageswap")
imageswap_mode = os.getenv("IMAGESWAP_MODE", "MAPS")
imageswap_maps_file = os.getenv("IMAGESWAP_MAPS_FILE", "/app/maps/imageswap-maps.conf")
imageswap_maps_default_key = "default"
imageswap_maps_wildcard_key = "noswap_wildcards"
imageswap_exact_keyword = "[EXACT]"
imageswap_replace_keyword = "[REPLACE]"

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

    """Function to run main logic to handle imageswap mutation"""

    request_info = request.json
    modified_spec = copy.deepcopy(request_info)
    uid = modified_spec["request"]["uid"]
    workload_metadata = modified_spec["request"]["object"]["metadata"]
    workload_type = modified_spec["request"]["kind"]["kind"]
    namespace = modified_spec["request"]["namespace"]
    # flag, whether there was at least one change, so that a patch has to be returned
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

        app.logger.info(f'Disable label "{imageswap_disable_label}=disabled" detected for "{workload}" {workload_type}", skipping image swap.')
        needs_patch = False

    else:

        # Change workflow/json path based on K8s object type
        if workload_type == "Pod":

            for container_spec in modified_spec["request"]["object"]["spec"]["containers"]:

                app.logger.info(f"Processing container: {namespace}/{workload}")
                needs_patch = swap_image(container_spec) or needs_patch

            if "initContainers" in modified_spec["request"]["object"]["spec"]:

                for init_container_spec in modified_spec["request"]["object"]["spec"]["initContainers"]:

                    app.logger.info(f"Processing init-container: {namespace}/{workload}")
                    needs_patch = swap_image(init_container_spec) or needs_patch

        else:

            for container_spec in modified_spec["request"]["object"]["spec"]["template"]["spec"]["containers"]:

                app.logger.info(f"Processing container: {namespace}/{workload}")
                needs_patch = swap_image(container_spec) or needs_patch

            if "initContainers" in modified_spec["request"]["object"]["spec"]["template"]["spec"]:

                for init_container_spec in modified_spec["request"]["object"]["spec"]["template"]["spec"]["initContainers"]:

                    app.logger.info(f"Processing init-container: {namespace}/{workload}")
                    needs_patch = swap_image(init_container_spec) or needs_patch

    if needs_patch:

        app.logger.debug("Needs patch")
        app.logger.info("Diffing original request to modified request and generating JSONPatch")

        patch = jsonpatch.JsonPatch.from_diff(request_info["request"]["object"], modified_spec["request"]["object"])

        app.logger.debug(f"JSON Patch: {patch}")

        admission_response = {
            "allowed": True,
            "uid": request_info["request"]["uid"],
            "patch": base64.b64encode(str(patch).encode()).decode(),
            "patchType": "JSONPatch",
        }
        admissionReview = {
            "apiVersion": "admission.k8s.io/v1",
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
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": admission_response,
        }

    app.logger.info("Sending Response to K8s API Server")
    app.logger.debug(f"Admission Review: {json.dumps(admissionReview)}")

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


def build_swap_map(map_file):

    """Function to build a map of imageswap customizations"""

    maps = {}
    exact_maps = {}
    replace_maps = {}

    # Read maps from file
    with open(map_file, "r") as f:
        # Read lines in the file to build a Dict of imageswap maps
        for line in f:
            # Skip commented lines
            if line[0] == "#":
                continue
            # Trim trailing comments
            if "#" in line:
                line = re.sub(r"(^.*[^#])(#.*$)", r"\1", line)
            # Trim whitespace
            line = re.sub(r" ", "", line.rstrip())
            # Skip empty lines
            if not line:
                continue
            # Check for new style separator ("::") and verify the map splits correctly
            if "::" in line and len(line.split("::")) == 2:
                (key, val) = line.split("::")
            # Check for old style separator (":") and verify the map splits correctly
            elif ":" in line and len(line.split(":")) == 2:
                app.logger.warning(
                    f'Map defined with ":" as separator. This syntax is now deprecated. Please use "::" to separate the key and value in the map file: {line}'
                )
                (key, val) = line.split(":")
            else:
                # Check if map key contains a ":port" and that the new style separator ("::") is not used
                if line.count(":") > 1 and "::" not in line:
                    app.logger.warning(
                        f'Invalid map is specified. A port in the map key or value requires using "::" as the separator. Skipping map for line: {line}'
                    )
                # Warn for any other invalid map syntax
                else:
                    app.logger.warning(f"Invalid map is specified. Incorrect syntax for map definition. Skipping map for line: {line}")
                continue
            # Store processed line key/value pair in map
            if key.startswith(imageswap_exact_keyword):
                key = key[len(imageswap_exact_keyword) :].lstrip()
                exact_maps[key] = val
            elif key.startswith(imageswap_replace_keyword):
                key = key[len(imageswap_replace_keyword) :].lstrip()
                replace_maps[key] = val
            else:
                maps[key] = val

    f.close()

    return (replace_maps, exact_maps, maps)


################################################################################
################################################################################
################################################################################


def swap_image(container_spec):

    """Function to perform imageswap for a container spec"""

    name = container_spec["name"]
    image = container_spec["image"]
    new_image = image
    image_split = image.partition("/")
    wildcard_maps = {}
    no_registry = False
    library_image = False

    # Check if first section is a Registry URL
    if "." in image_split[0] and image_split[1] != "" and image_split[2] != "":
        image_registry = image_split[0]
    else:
        # Set docker.io if no registry is detected
        image_registry = "docker.io"
        no_registry = True

    # Set the image registry key to work with
    image_registry_key = image_registry

    # Check the imageswap mode
    if imageswap_mode.lower() == "maps":

        app.logger.info('ImageSwap Webhook running in "MAPS" mode')

        (replace_maps, exact_maps, swap_maps) = build_swap_map(imageswap_maps_file)

        app.logger.debug(f"Swap Maps:\n{swap_maps}")
        app.logger.debug(f"Exact Maps:\n{exact_maps}")
        app.logger.debug(f"Replace Maps:\n{replace_maps}")

        found = False
        if image in exact_maps:
            app.logger.debug("found exact mapping")
            new_image = exact_maps[image]
            found = True
        else:
            # Check to see if a replacement pattern matches
            for pattern in replace_maps.keys():
                if fnmatch.fnmatch(image, pattern):
                    new_image = os.path.join(replace_maps[pattern], image.split("/")[-1])
                    found = True
                    break

        # Fallback to standard checks if the image has not been found
        if not found:
            # Check if Registry portion includes a ":<port_number>"
            if ":" in image_registry:
                image_registry_noport = image_registry.partition(":")[0]
            else:
                image_registry_noport = image_registry

            if image_registry not in swap_maps and image_registry_noport in swap_maps:
                image_registry_key = image_registry_noport

            # Verify the default map exists or skip swap
            if imageswap_maps_default_key not in swap_maps:
                app.logger.warning(f'You don\'t have a "{imageswap_maps_default_key}" entry in your ImageSwap Map config, skipping swap')
                return False

            # Check for noswap wildcards in map file
            if imageswap_maps_wildcard_key in swap_maps and swap_maps[imageswap_maps_wildcard_key] != "":
                wildcard_maps = str(swap_maps[imageswap_maps_wildcard_key]).split(",")

            # Check if registry or registry+library has a map specified
            if image_registry_key in swap_maps or image_registry_key + "/library" in swap_maps:

                # Check for Library image (ie. empty strings for index 1 an 2 in image_split)
                if image_split[1] == "" and image_split[2] == "":
                    library_image = True
                    app.logger.debug("Image is a Library image")
                else:
                    app.logger.debug("Image is not a Library image")

                if library_image and image_registry_key + "/library" in swap_maps:

                    image_registry_key = image_registry_key + "/library"
                    app.logger.info(f"Library Image detected and matching Map found: {image_registry_key}")
                    app.logger.debug("More info on Library Image: https://docs.docker.com/registry/introduction/#understanding-image-naming")

                # If the swap map has no value, swapping should be skipped
                if swap_maps[image_registry_key] == "":
                    app.logger.debug(f'Swap map for "{image_registry_key}" has no value assigned, skipping swap')
                    return False
                # If the image prefix ends with "-" just append existing image (minus any ":<port_number>")
                elif swap_maps[image_registry_key][-1] == "-":
                    if no_registry:
                        new_image = swap_maps[image_registry_key] + image_registry_noport + "/" + re.sub(r":.*/", "/", image)
                    else:
                        new_image = swap_maps[image_registry_key] + re.sub(r":.*/", "/", image)
                # If the image registry pattern is found in the original image
                elif image_registry_key in image:
                    new_image = re.sub(image_registry_key, swap_maps[image_registry_key], image)
                # For everything else
                else:
                    new_image = swap_maps[image_registry_key] + "/" + image

                app.logger.debug(f'Swap Map = "{image_registry_key}" : "{swap_maps[image_registry_key]}"')

            # Check if any of the noswap wildcard patterns from the swap map exist within the original image
            elif len(wildcard_maps) > 0 and any(noswap in image for noswap in wildcard_maps):
                app.logger.debug(f"Image matches a configured noswap_wildcard pattern, skipping swap")
                app.logger.debug(f'Swap Map = "noswap_wilcard" : "{wildcard_maps}"')
                return False
            # Using Default image swap map
            else:

                app.logger.debug(f'No Swap map for "{image_registry_key}" detected, using default map')
                app.logger.debug(f'Swap Map = "default" : "{swap_maps[imageswap_maps_default_key]}"')

                if swap_maps[imageswap_maps_default_key] == "":
                    app.logger.debug(f"Default map has no value assigned, skipping swap")
                    return False
                elif swap_maps[imageswap_maps_default_key][-1] == "-":
                    new_image = swap_maps[imageswap_maps_default_key] + image_registry_noport + "/" + image
                elif image_registry_key in image:
                    new_image = re.sub(image_registry, swap_maps[imageswap_maps_default_key], image)
                else:
                    new_image = swap_maps[imageswap_maps_default_key] + "/" + image

    # TO-DO (phenixblue): Remove this else block sometime in the future...
    # This "else" block maintains the legacy imageswap logic, which is now
    # deprecated.
    else:

        app.logger.warning('ImageSwap Webhook running in "LEGACY" mode. This mode is now deprecated. Please read the docs to setup the new MAPS configuration')

        if "IMAGE_PREFIX" in os.environ and os.environ["IMAGE_PREFIX"] != "":
            image_prefix = os.environ["IMAGE_PREFIX"]
        else:
            app.logger.warning('The "IMAGESWAP_PREFIX" is empty, skipping swap.')
            return False

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

    app.logger.info("ImageSwap v1.5.3 Startup")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
        ssl_context=(
            "./tls/cert.pem",
            "./tls/key.pem",
        ),
    )


################################################################################
################################################################################
################################################################################

if __name__ == "__main__":

    main()
