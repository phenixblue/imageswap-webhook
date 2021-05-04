#!/usr/bin/env bash

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
#
# This is based on existing work from the MagTape project: 
# https://github.com/tmobile/magtape

################################################################################
#### Variables, Arrays, and Hashes #############################################
################################################################################

MODE="${1}"
MANIFEST_DIR="./deploy/manifests"
POLICY_DIR="./policies"
TMP_DIR="./tmp"
INSTALL_MANIFEST="./deploy/install.yaml"
TMP_INSTALL_MANIFEST="${TMP_DIR}/install.yaml"
TARGET_MANIFEST=""
NAMESPACE="imageswap-system"

################################################################################
#### Functions #################################################################
################################################################################

# **********************************************
# Check the argument being passed to script
# **********************************************
help_message() {

  echo "You need to specify the proper argument:"
  echo "    Mode: (\"build\" or \"compare\")"

}

# **********************************************
# Check the argument being passed to script
# **********************************************
check_arguments() {

  if [ "${MODE}" == "" ] && [ "${MODE}" != "build" ] && [ "${MODE}" != "compare" ]; then

    help_message
    exit 1

  fi

}

# **********************************************
# Build a single manifest from individuals
# **********************************************
function build_manifest() {

    # Start with blank file
    > "${TARGET_MANIFEST}"

    # Aggregate ImageSwap Application specific manifests
    cat "${MANIFEST_DIR}/imageswap-ns.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-cluster-rbac.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-ns-rbac.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-sa.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-env-cm.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    kubectl create cm imageswap-mwc-template -n "${NAMESPACE}" --from-file=imageswap-mwc="${MANIFEST_DIR}/imageswap-mwc.yaml" --dry-run=client -o yaml >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    kubectl create cm imageswap-maps -n "${NAMESPACE}" --from-file=maps="${MANIFEST_DIR}/imageswap-maps.conf" --dry-run=client -o yaml >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-svc.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-pdb.yaml" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-deploy.yaml"  >> "${TARGET_MANIFEST}"
    echo "---" >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"
    cat "${MANIFEST_DIR}/imageswap-hpa.yaml"  >> "${TARGET_MANIFEST}"
    echo >> "${TARGET_MANIFEST}"

}

################################################################################
#### Main ######################################################################
################################################################################

check_arguments

case ${MODE} in 

    build)

        TARGET_MANIFEST="${INSTALL_MANIFEST}"
        build_manifest
        ;;
  compare)

        TARGET_MANIFEST="${TMP_INSTALL_MANIFEST}"

        # Create temporary directory
        mkdir "${TMP_DIR}"

        build_manifest

        # Compare existing and generated manifest
        if diff "${TMP_INSTALL_MANIFEST}" "${INSTALL_MANIFEST}"; then

            echo "No changes detected"
            EXIT_CODE=0

        else

            echo "Changes detected in manifests. Please run \"make build-single-manifest\" to update install.yaml"
            EXIT_CODE=1

        fi

        # Cleanup temporary directory
        rm -rf "${TMP_DIR}"
        exit "${EXIT_CODE}"
        ;;
        *)
        help_message
        ;; 
esac