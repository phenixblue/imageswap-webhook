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

# NOTE: The version for both `imageswap-init` and `imageswap` should be identical for now.
# Some effort will need to be put in to be able to distringuish changes to one vs. the other
# in CI/Release steps.
IMAGESWAP_VERSION := v1.5.0
IMAGESWAP_INIT_VERSION := v1.5.0

REPO_ROOT := $(CURDIR)
APP_NAME ?= "imageswap.py"
DEPLOY_DIR ?= $(CURDIR)/deploy
TESTING_DIR ?= $(CURDIR)/testing
WEBHOOK_NAMESPACE ?= "imageswap-system"
TEST_NAMESPACE ?= "test1"
DOCKER := docker

# Pin utilities at specific versions for CI stability
KUBECTL_VERSION ?= v1.19.1

###############################################################################
# CI Bootstrap Related Targets ################################################
###############################################################################

# Download and install required utilities
.PHONY: ci-bootstrap
ci-bootstrap:

	# Create local bin directory
	mkdir -p "${GITHUB_WORKSPACE}/bin"
	# Download and install kubectl
	curl -L https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl -o ${GITHUB_WORKSPACE}/bin/kubectl && chmod +x ${GITHUB_WORKSPACE}/bin/kubectl && sudo mv "${GITHUB_WORKSPACE}/bin/kubectl" /usr/local/bin/

###############################################################################
# K8s Related Targets #########################################################
###############################################################################

# Create Namespace for ImageSwap
.PHONY: ns-create-imageswap
ns-create-imageswap:

	kubectl create ns $(WEBHOOK_NAMESPACE)

# Create Namespace for testing
.PHONY: ns-create-test
ns-create-test:

	kubectl create ns $(TEST_NAMESPACE)
	kubectl label ns $(TEST_NAMESPACE) k8s.twr.io/imageswap=enabled --overwrite

# Delete Namespace for ImageSwap
.PHONY: ns-delete-imageswap
ns-delete-imageswap:

	kubectl delete ns $(WEBHOOK_NAMESPACE)

# Delete Namespace for testing
.PHONY: ns-delete-test
ns-delete-test:

	kubectl delete ns $(TEST_NAMESPACE)

# DEPRECATED - Moved to init application. Will be removed in the future.
.PHONY: cert-gen
cert-gen:

	hack/ssl-cert-gen.sh \
    --service imageswap \
    --secret imageswap-certs \
    --namespace $(WEBHOOK_NAMESPACE)

# Install ImageSwap (Demo Install)
.PHONY: install
install:

	kubectl apply -f $(DEPLOY_DIR)/install.yaml

# Uninstall ImageSwap (Demo Install)
.PHONY: uninstall
uninstall:

	kubectl delete -f $(DEPLOY_DIR)/install.yaml --ignore-not-found
	kubectl delete mutatingwebhookconfiguration imageswap-webhook --ignore-not-found
	kubectl delete csr imageswap.imageswap-system.cert-request --ignore-not-found

# Restart ImageSwap Pods (Demo Install)
.PHONY: restart
restart:

	kubectl rollout restart deploy imageswap -n imageswap-system

# Cleanup ImageSwap (Demo Install)
.PHONY: clean
clean: uninstall

###############################################################################
# Python Targets ##############################################################
###############################################################################

# Run unit tests for ImageSwap/ImageSwap-Init
.PHONY: unit-python
unit-python:

	hack/run-python-tests.sh

# Run unit tests for ImageSwap/ImageSwap-Init
.PHONY: test-python
test-python: unit-python

# Lint Python and update python code
.Phony: lint-python
lint-python:

	black app/imageswap-init/ --line-length 160
	black app/imageswap/ --line-length 160

# Verify linting of Python during CI
.PHONY: ci-lint-python
ci-lint-python:

	black --check app/imageswap-init/ --line-length 160
	black --check app/imageswap/ --line-length 160

###############################################################################
# Functional Test Targets #####################################################
###############################################################################

# Run ImageSwap functional tests for Deployments
.PHONY: test-functional
test-functional:

	hack/run-functional-tests.sh test all all test1

# Run ImageSwap functional tests for Deployments
.PHONY: test-clean
test-clean:

	hack/run-functional-tests.sh clean all all test1

# Run all unit and functional tests for ImageSwap/ImageSwap-Init
.PHONY: test-all
test-all: test test-functional

###############################################################################
# Misc Repo Targets ###########################################################
###############################################################################

# Verify copyright boilerplate in files
.PHONY: boilerplate
boilerplate:

	hack/verify-boilerplate.sh

# Build dmeo install manifest for ImageSwap
.PHONY: build-single-manifest
build-single-manifest:

	hack/build-single-manifest.sh build

PHONY: compare-single-manifest
compare-single-manifest:

	hack/build-single-manifest.sh compare

# Set release version in deployment manifest
.PHONY: set-release-version
set-release-version:

	sed -i='' "s/\(image: thewebroot\/imageswap-init:\).*/\1${IMAGESWAP_INIT_VERSION}/" deploy/manifests/imageswap-deploy.yaml
	sed -i='' "s/\(image: thewebroot\/imageswap:\).*/\1${IMAGESWAP_VERSION}/" deploy/manifests/imageswap-deploy.yaml
	sed -i='' "s/\(appVersion: \).*/\1${IMAGESWAP_VERSION}/" helm/imageswap-webhook/Chart.yaml
	sed -i='' "s/\(version\)=\"latest\"\(.*\)/\1=\"${IMAGESWAP_VERSION}\"\2/" app/imageswap/imageswap.py
	sed -i='' "s/\(ImageSwap\).*\(Startup\)/\1 ${IMAGESWAP_VERSION} \2/" app/imageswap/imageswap.py

# Cut new ImageSwap release
.PHONY: release
release: echo

###############################################################################
# Container Image Targets #####################################################
###############################################################################

# Build ImageSwap-Init container image
.PHONY: build-imageswap-init-latest
build-imageswap-init-latest:

	$(DOCKER) build -t thewebroot/imageswap-init:latest app/imageswap-init/

# Push ImageSwap-Init container image to DockerHub
.PHONY: push-imageswap-init-latest
push-imageswap-init-latest:

	$(DOCKER) push thewebroot/imageswap-init:latest

# Build ImageSwap container image
.PHONY: build-imageswap-latest
build-imageswap-latest:

	$(DOCKER) build -t thewebroot/imageswap:latest app/imageswap/

# Push ImageSwap container image to DockerHub
.PHONY: push-imageswap-latest
push-imageswap-latest:

	$(DOCKER) push thewebroot/imageswap:latest

# Build and push all ImageSwap container images to DockerHub
.PHONY: build-latest
build-latest: build-imageswap-init-latest push-imageswap-init-latest build-imageswap-latest push-imageswap-latest

# Build ImageSwap-Init container image
.PHONY: build-imageswap-init-versioned
build-imageswap-init-versioned:

	$(DOCKER) build -t thewebroot/imageswap-init:${IMAGESWAP_INIT_VERSION} app/imageswap-init/

# Push ImageSwap-Init container image to DockerHub
.PHONY: push-imageswap-init-versioned
push-imageswap-init-versioned:

	$(DOCKER) push thewebroot/imageswap-init:${IMAGESWAP_INIT_VERSION}

# Build ImageSwap container image
.PHONY: build-imageswap-versioned
build-imageswap-versioned:

	$(DOCKER) build -t thewebroot/imageswap:${IMAGESWAP_VERSION} app/imageswap/

# Push ImageSwap container image to DockerHub
.PHONY: push-imageswap-versioned
push-imageswap-versioned:

	$(DOCKER) push thewebroot/imageswap:${IMAGESWAP_VERSION}

# Build and push all ImageSwap container images to DockerHub
.PHONY: build-versioned
build-versioned: build-imageswap-init-versioned push-imageswap-init-versioned build-imageswap-versioned push-imageswap-versioned

