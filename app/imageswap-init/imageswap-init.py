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
#
# This is based on existing work from the MagTape project:
# https://github.com/tmobile/magtape

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from logging.handlers import MemoryHandler
import base64
import datetime
import json
import logging
import os
import random
import sys
import time
import yaml

# Set Global variables
imageswap_namespace_name = os.environ["IMAGESWAP_NAMESPACE_NAME"]
imageswap_pod_name = os.environ["IMAGESWAP_POD_NAME"]
imageswap_tls_pair_secret_name = "imageswap-tls"
imageswap_tls_rootca_secret_name = "imageswap-tls-ca"
imageswap_byoc_annotation = "imageswap-byoc"
imageswap_service_name = "imageswap"
imageswap_tls_path = "/tls"
imageswap_mwc_template_path = "/mwc"
imageswap_tls_key = ""
imageswap_tls_cert = ""
imageswap_mwc_name = "imageswap-webhook"
imageswap_mwc_template_file = f"{imageswap_mwc_template_path}/imageswap-mwc.yaml"
imageswap_mwc_webhook_name = "imageswap.webhook.k8s.twr.io"
imageswap_tls_byoc = False
imageswap_pks_namespace = "pks-system"

################################################################################
################################################################################
################################################################################


def check_for_byoc(namespace, secret, core_api):
    """Function to check for the "Bring Your Own Cert" annotation"""

    logging.info("We made it to check_for_byoc")

    secret_name = secret.metadata.name
    secret_annotations = secret.metadata.annotations

    if secret_annotations and imageswap_byoc_annotation in secret_annotations:

        logging.info(f'Detected the "Bring Your Own Cert" annotation for secret "{secret_name}"')

        try:

            secret = core_api.read_namespaced_secret(imageswap_tls_rootca_secret_name, namespace)

        except ApiException as exception:

            if exception.status != 404:

                logging.error(
                    f'An error occurred while trying to read secret "{imageswap_tls_rootca_secret_name}" in the "{namespace}" namespace:\n{exception}\n'
                )
                sys.exit(1)

            else:

                logging.error(
                    f'"Bring Your Own Cert" annotation specified, but secret "{imageswap_tls_rootca_secret_name}" was not found in the "{namespace}" namespace:\n{exception}\n'
                )
                sys.exit(1)

        if "rootca.pem" in secret.data and secret.data["rootca.pem"] != "":

            return True

        else:

            logging.error(f'No key found or value is blank for "rootca.pem" in "{secret.metadata.name}" secret')
            sys.exit(1)

    else:

        return False


################################################################################
################################################################################
################################################################################


def build_k8s_csr(namespace, service_name, key):
    """Function to generate Kubernetes CSR"""

    logging.info("Got to building client-side CSR")

    # Store all dns names used for CN/SAN's
    dns_names = list()
    # K8s service intra namespace
    dns_names.insert(0, f"{service_name}")
    # K8s service inter namespace
    dns_names.insert(1, f"{service_name}.{namespace}")
    # K8s service full FQDN and Common Name
    dns_names.insert(2, f"{service_name}.{namespace}.svc")

    # Setup Certificate Signing Request
    csr = x509.CertificateSigningRequestBuilder()
    csr = csr.subject_name(
        # Provide Common Name
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "system:node:" + dns_names[2]), x509.NameAttribute(NameOID.ORGANIZATION_NAME, "system:nodes")])
    )

    csr = csr.add_extension(
        x509.SubjectAlternativeName(
            [
                x509.DNSName(dns_names[0]),
                x509.DNSName(dns_names[1]),
                x509.DNSName(dns_names[2]),
            ]
        ),
        critical=False,
    )

    # Sign the CSR with our private key.
    csr = csr.sign(key, hashes.SHA256(), default_backend())

    csr_pem = csr.public_bytes(serialization.Encoding.PEM)

    # Build Kubernetes CSR
    k8s_csr_meta = client.V1ObjectMeta(
        name=dns_names[1] + ".cert-request",
        namespace=namespace,
        labels={"app": "imageswap"},
    )

    k8s_csr_spec = client.V1CertificateSigningRequestSpec(
        groups=["system:authenticated"],
        usages=["key encipherment", "digital signature", "server auth"],
        request=base64.b64encode(csr_pem).decode("utf-8").rstrip(),
        signer_name="kubernetes.io/kubelet-serving",
    )

    k8s_csr = client.V1CertificateSigningRequest(
        api_version="certificates.k8s.io/v1",
        kind="CertificateSigningRequest",
        metadata=k8s_csr_meta,
        spec=k8s_csr_spec,
    )

    logging.debug(f"CSR: {k8s_csr}\n")

    return k8s_csr


################################################################################
################################################################################
################################################################################


def submit_and_approve_k8s_csr(namespace, certificates_api, k8s_csr):
    """Function to submit or approve a Kubernetes CSR"""

    new_k8s_csr_name = k8s_csr.metadata.name

    # Read existing Kubernetes CSR
    try:

        logging.info("Looking for existing CSR")
        certificates_api.read_certificate_signing_request(new_k8s_csr_name)

    except ApiException as exception:

        if exception.status != 404:

            logging.error(f"Problem reading existing certificate requests: {exception}\n")
            sys.exit(1)

        elif exception.status == 404:

            logging.info(f"Did not find existing certificate requests")
            logging.debug(f"Exception:\n{exception}\n")

    else:

        try:

            logging.info("Deleting k8s csr")

            certificates_api.delete_certificate_signing_request(new_k8s_csr_name)

        except ApiException as exception:

            if exception.status != 404:

                logging.error(f'Unable to delete existing certificate request "{new_k8s_csr_name}": {exception}\n')
                sys.exit(1)

            elif exception.status == 404:

                logging.info(f'Existing certificate request "{new_k8s_csr_name}" not found')
                logging.debug(f"Exception:\n{exception}\n")
        else:

            logging.info(f"Existing certificate request deleted")

    # Create K8s CSR resource
    try:

        logging.info("Create k8s CSR")
        logging.debug(k8s_csr)
        certificates_api.create_certificate_signing_request(k8s_csr)

    except ApiException as exception:

        logging.error(f'Unable to create certificate request "{new_k8s_csr_name}"\n')
        logging.debug(f"Exception:\n{exception}\n")
        sys.exit(1)

    logging.info(f'Certificate signing request "{new_k8s_csr_name}" has been created')

    # Read newly created K8s CSR resource
    try:

        new_k8s_csr_body = certificates_api.read_certificate_signing_request_status(new_k8s_csr_name)

    except ApiException as exception:

        logging.error(f'Unable to read certificate request status for "{new_k8s_csr_name}"\n')
        logging.debug(f"Exception:\n{exception}\n")
        sys.exit(1)

    new_k8s_csr_approval_conditions = client.V1CertificateSigningRequestCondition(
        last_update_time=datetime.datetime.now(datetime.timezone.utc),
        message=f"This certificate was approved by ImageSwap (pod: {imageswap_pod_name})",
        reason="ImageSwap-Approve",
        type="Approved",
        status="True",
    )

    # Update the CSR status
    new_k8s_csr_body.status.conditions = [new_k8s_csr_approval_conditions]

    # Patch the k8s CSR resource
    try:

        logging.info(f"Patch k8s CSR: {new_k8s_csr_name}")
        certificates_api.replace_certificate_signing_request_approval(new_k8s_csr_name, new_k8s_csr_body)

    except ApiException as exception:

        logging.info(f'Unable to update certificate request status for "{new_k8s_csr_name}": {exception}\n')

    logging.info(f'Certificate signing request "{new_k8s_csr_name}" is approved')

    return new_k8s_csr_body


################################################################################
################################################################################
################################################################################


def get_tls_cert_from_request(namespace, secret_name, k8s_csr_name, certificates_api):
    """Function to retrieve tls certificate from approved Kubernetes CSR"""

    start_time = datetime.datetime.now()

    while (datetime.datetime.now() - start_time).seconds < 5:

        # Read existing Kubernetes CSR
        try:

            k8s_csr = certificates_api.read_certificate_signing_request(k8s_csr_name)

            logging.debug(k8s_csr)

        except ApiException as exception:

            logging.info(f'Problem reading certificate request "{k8s_csr_name}"\n')
            logging.debug(f"Exception:\n{exception}\n")

        tls_cert_b64 = k8s_csr.status.certificate
        conditions = k8s_csr.status.conditions or []

        if "Approved" in [condition.type for condition in conditions] and tls_cert_b64 != None:

            logging.info("Found approved certificate")

            break

        logging.info("Waiting for certificate approval")

    else:

        logging.info(f'Timed out reading certificate request "{k8s_csr_name}"\n')

    logging.debug(f"Cert RAW: {k8s_csr}")

    tls_cert = base64.b64decode(k8s_csr.status.certificate)

    logging.debug(f"Cert PEM: {tls_cert}")

    return tls_cert


################################################################################
################################################################################
################################################################################


def build_tls_pair(namespace, secret_name, service_name, certificates_api):
    """Function to generate signed tls certificate for admission webhook"""

    # Generate private key to use for CSR
    tls_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    tls_key_pem = tls_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Build K8s CSR
    logging.info("Building K8s CSR")
    k8s_csr = build_k8s_csr(namespace, service_name, tls_key)
    k8s_csr = submit_and_approve_k8s_csr(namespace, certificates_api, k8s_csr)
    tls_cert_pem = get_tls_cert_from_request(
        namespace,
        imageswap_tls_pair_secret_name,
        k8s_csr.metadata.name,
        certificates_api,
    )

    tls_pair = {
        "cert": tls_cert_pem,
        "key": tls_key_pem,
    }

    logging.debug(tls_pair)

    return tls_pair


################################################################################
################################################################################
################################################################################


def cert_expired(namespace, tls_secret):
    """Function to check tls certificate return number of days until expiration"""

    current_datetime = datetime.datetime.now()
    tls_cert_decoded = base64.b64decode(tls_secret.data["cert.pem"])
    tls_cert = x509.load_pem_x509_certificate(tls_cert_decoded, default_backend())
    expire_days = tls_cert.not_valid_after - current_datetime

    logging.info(f"Days until Cert Expiration: {expire_days.days}")

    return expire_days.days


################################################################################
################################################################################
################################################################################


def cert_should_update(namespace, secret_exists, tls_secret, imageswap_tls_byoc):
    """Function to check if tls certificate should be updated"""

    tls_cert_key = "cert.pem"
    tls_key_key = "key.pem"

    if tls_secret.data != None:

        if tls_cert_key in tls_secret.data and tls_key_key in tls_secret.data:

            if tls_secret.data[tls_cert_key] == "" or tls_secret.data[tls_key_key] == "":

                if imageswap_tls_byoc:

                    logging.error(f'The "Bring Your Own Cert" annotation was used but one or more of the tls cert/key values are blank')
                    sys.exit(1)

                return True

            days = cert_expired(namespace, tls_secret)

            # Determine and report on cert expiry based on number of days from current date.
            # Cert should be valid for a year, but we update sooner to be safe
            if days <= 180:

                return True

            else:

                return False

        else:

            return True

    elif secret_exists:

        return False

    else:

        return True


################################################################################
################################################################################
################################################################################


def read_tls_pair(namespace, secret_name, tls_pair, core_api):
    """Function to read cert/key from k8s secret"""

    secret = client.V1Secret()
    secret_exists = False

    # Try and read secret
    try:

        secret = core_api.read_namespaced_secret(secret_name, namespace)

    except ApiException as exception:

        if exception.status != 404:

            logging.error(f'Unable to read secret "{secret_name}" in the "{namespace}" namespace\n')
            logging.debug(f"Exception:\n{exception}\n")
            sys.exit(1)

        else:

            logging.info(f'Did not find secret "{secret_name}" in the "{namespace}" namespace')
            logging.debug(f"Exception:\n{exception}\n")

            logging.debug(f"Secret:\n{secret}\n")

            return secret, tls_pair, secret_exists, False

    tls_cert_pem = base64.b64decode(secret.data["cert.pem"])
    tls_key_pem = base64.b64decode(secret.data["key.pem"])

    if tls_cert_pem != "" or tls_key_pem != "":

        secret_exists = True

    tls_pair = {
        "cert": tls_cert_pem,
        "key": tls_key_pem,
    }

    imageswap_tls_byoc = check_for_byoc(namespace, secret, core_api)

    logging.debug(f"Secret:\n{secret}\n")

    return secret, tls_pair, secret_exists, imageswap_tls_byoc


################################################################################
################################################################################
################################################################################


def write_tls_pair(
    namespace,
    secret_name,
    secret_exists,
    secret_should_update,
    tls_secret,
    tls_pair,
    imageswap_tls_byoc,
    core_api,
):
    """Function to write k8s secret for admission webhook to k8s secret and/or local files"""

    # If the secret isn't found, create it
    if secret_exists:

        logging.info(f'Using existing secret "{secret_name}" in namespace "{namespace}"')
        logging.info("Waiting for race winning pod to startup")

        start_time = datetime.datetime.now()
        race_winner_pod = ""

        while race_winner_pod == "" or (datetime.datetime.now() - start_time).seconds < 30:

            logging.info("Still waiting for race winning pod to startup")

            if "imageswap/updated-by-pod" in tls_secret.metadata.labels:

                race_winner_pod = tls_secret.metadata.labels["imageswap/updated-by-pod"]
                break

            else:

                time.sleep(5)

    else:

        logging.info(f'Creating secret "{secret_name}" in namespace "{namespace}"')

        secret_metadata = client.V1ObjectMeta(
            name=secret_name,
            namespace=namespace,
            labels={
                "app": "imageswap",
                "imageswap/updated-by-pod": imageswap_pod_name,
            },
        )

        secret_data = {
            "cert.pem": base64.b64encode(tls_pair["cert"]).decode("utf-8").rstrip(),
            "key.pem": base64.b64encode(tls_pair["key"]).decode("utf-8").rstrip(),
        }

        secret = client.V1Secret(metadata=secret_metadata, data=secret_data, type="tls")

        logging.debug(f"New secret: \n{secret}\n")

        try:

            core_api.create_namespaced_secret(namespace, secret)

        except ApiException as exception:

            logging.error(f'Unable to create secret "{secret_name}" in the "{namespace}" namespace: {exception}\n')
            sys.exit(1)

        try:

            core_api.read_namespaced_secret(secret_name, namespace)

        except ApiException as exception:

            logging.error(f'Unable to read new secret "{secret_name}" in the "{namespace}" namespace: {exception}\n')
            sys.exit(1)

        logging.info("New secret created")
        secret_exists = True

    # If this is a BYOC pair, then skip the patch
    if not secret_exists and not imageswap_tls_byoc and secret_should_update:

        secret = client.V1Secret()

        secret.metadata.labels = {
            "imageswap/updated-by-pod": imageswap_pod_name,
        }

        secret.data = {
            "cert.pem": base64.b64encode(tls_pair["cert"]).decode("utf-8").rstrip(),
            "key.pem": base64.b64encode(tls_pair["key"]).decode("utf-8").rstrip(),
        }

        try:

            core_api.patch_namespaced_secret(secret_name, namespace, secret)

        except ApiException as exception:

            logging.error(f'Unable to update secret "{secret_name}" in the "{namespace}" namespace: {exception}\n')
            sys.exit(1)

        logging.info(f"Patched new cert/key into existing secret")

        try:

            tls_secret, tls_pair, secret_exists, imageswap_tls_byoc = read_tls_pair(namespace, imageswap_tls_pair_secret_name, tls_pair, core_api)

            logging.debug(f"Cert Data: \n{tls_secret.data}\n")

        except ApiException as exception:

            logging.error(f'Unable to read updated secret "{secret_name}" in the "{namespace}" namespace: {exception}\n')
            sys.exit(1)

        logging.info(f'Updated secret "{secret_name}" in namespace "{namespace}"')

    # Write cert and key to files for Flask/OPA containers
    logging.info("Writing cert and key locally")
    logging.debug(f"TLS Pair: {tls_pair}")

    with open(f"{imageswap_tls_path}/cert.pem", "wb") as cert_file:
        cert_file.write(tls_pair["cert"])

    with open(f"{imageswap_tls_path}/key.pem", "wb") as key_file:
        key_file.write(tls_pair["key"])


################################################################################
################################################################################
################################################################################


def init_tls_pair(namespace):
    """Function to load or create tls for admission webhook"""

    tls_pair = ""

    logging.info("Starting TLS init process")

    # Check if custom secret was specified in ENV vars
    imageswap_tls_secret_name = os.getenv("imageswap_tls_secret_name", imageswap_tls_pair_secret_name)

    if imageswap_tls_secret_name != imageswap_tls_pair_secret_name:

        logging.debug("ImageSwap TLS Secret specified")

    try:

        config.load_incluster_config()

    except Exception as exception:

        logging.info(f"Exception loading in-cluster configuration: {exception}")

        try:
            logging.info("Loading local kubeconfig")
            config.load_kube_config()

        except Exception as exception:

            logging.error(f"Exception loading local kubeconfig: {exception}")
            sys.exit(1)

    configuration = client.Configuration()
    core_api = client.CoreV1Api(client.ApiClient())
    certificates_api = client.CertificatesV1Api(client.ApiClient())

    # Read existing secret
    tls_secret, tls_pair, secret_exists, imageswap_tls_byoc = read_tls_pair(namespace, imageswap_tls_pair_secret_name, tls_pair, core_api)

    if secret_exists:

        logging.info("Existing TLS cert and key found")

    # Check if cert should be updated
    secret_should_update = cert_should_update(namespace, secret_exists, tls_secret, imageswap_tls_byoc)

    if secret_should_update:

        if imageswap_tls_byoc:

            logging.warning(
                f"WARN - Certificate used for Admission Webhook is past threshhold for normal rotation. Not rotating because this cert isn't managed by the K8s CA"
            )

        else:

            logging.info(f"Generating new cert/key pair for TLS")

            # Generate TLS Pair
            tls_pair = build_tls_pair(
                namespace,
                imageswap_tls_pair_secret_name,
                imageswap_service_name,
                certificates_api,
            )

    # Handle cert creation or update
    write_tls_pair(
        namespace,
        imageswap_tls_secret_name,
        secret_exists,
        secret_should_update,
        tls_secret,
        tls_pair,
        imageswap_tls_byoc,
        core_api,
    )


################################################################################
################################################################################
################################################################################


def check_for_pks(core_api):
    """Function to if cluster is of PKS origin"""

    # This is a simple test to check for the "pks-system" namespace. May need
    # to do something more in-depth later.

    try:

        namespace_list = core_api.list_namespace()

    except ApiException as exception:

        logging.error(f"Unable to read namespaces\n")
        logging.debug(f"Exception:\n{exception}\n")
        sys.exit(1)

    logging.debug(f"Namespace List:\n{namespace_list}\n")

    ns = any(ns.metadata.name == imageswap_pks_namespace for ns in namespace_list.items)

    if ns:

        return True

    else:

        return False


################################################################################
################################################################################
################################################################################


def get_rootca(namespace, configuration, imageswap_tls_byoc, core_api):
    """Function to get root ca used for securing admission webhook"""

    if imageswap_tls_byoc:

        # Read from secret
        try:

            secret = core_api.read_namespaced_secret(imageswap_tls_rootca_secret_name, namespace)

        except ApiException as exception:

            if exception.status != 404:

                logging.error(f'Unable to read secret "{imageswap_tls_rootca_secret_name}" in the "{namespace}" namespace\n')
                logging.debug(f"Exception:\n{exception}\n")
                sys.exit(1)

            else:

                logging.error(f'Did not find secret "{imageswap_tls_rootca_secret_name}" in the "{namespace}" namespace')
                logging.debug(f"Exception:\n{exception}\n")
                sys.exit(1)

        root_ca = secret.data["rootca.pem"]

    elif check_for_pks(core_api):

        # PKS Seems to manage certificates and the cluster Root CA slightly
        # different than other K8s distributions. This pulls the Root CA bundle
        # from a configmap that should exist in the kube-system namespace on PKS
        # provisioned clusters.

        pks_cm = "extension-apiserver-authentication"
        kube_system_ns = "kube-system"

        logging.info("PKS Cluster detected\n")

        try:

            configmap = core_api.read_namespaced_config_map(pks_cm, kube_system_ns)

        except ApiException as exception:

            if exception.status != 404:

                logging.error(f'Unable to read configmap "{pks_cm}" in the "{kube_system_ns}" namespace\n')
                logging.debug(f"Exception:\n{exception}\n")
                sys.exit(1)

            else:

                logging.error(f'Did not find configmap "{pks_cm}" in the "{kube_system_ns}" namespace')
                logging.debug(f"Exception:\n{exception}\n")
                sys.exit(1)

        root_ca = base64.b64encode(configmap.data["client-ca-file"].encode("utf-8")).decode("utf-8").rstrip()

    else:

        # Find Cluster CA file from in-cluster kubeconfig
        root_ca_file_path = configuration.ssl_ca_cert

        # Read cert from file
        try:

            with open(root_ca_file_path, "r") as root_ca_file:

                root_ca_raw = root_ca_file.read()

        except EnvironmentError:

            logging.error("Error reading Root CA from in-cluster kubeconfig\n")
            sys.exit(1)

        logging.debug(f"Raw CA data from in-cluster kubeconfig: \n{root_ca_raw}\n")

        root_ca = base64.b64encode(root_ca_raw.encode("utf-8")).decode("utf-8").rstrip()

    return root_ca


################################################################################
################################################################################
################################################################################


def verify_mwc_cert_bundle(namespace, mwc):
    """Function to verify the CA Cert bundle in the MWC"""


################################################################################
################################################################################
################################################################################


def compare_mwc_fields(new, existing):
    """Function to compare MWC fields"""

    # logging.debug(f"Input is of type \"{type(new)}\"")

    if isinstance(new, dict):

        for key in sorted(new):

            if key in existing:

                # logging.debug(f"Field from MWC Template has a value of \"{new[key]}\"")
                # logging.debug(f"Field from existing MWC has a value of \"{existing[key]}\"")

                same = compare_mwc_fields(new[key], existing[key])

                if not same:

                    return False

            else:

                logging.info(f"Changes detected in template. MWC Should update")
                # logging.debug(f"Changes: \n{new}\n")

                return False

    elif isinstance(new, list):

        for index in range(len(new)):

            if index <= len(existing) - 1:

                # logging.debug(f"Field from MWC Template has a value of \"{new[index]}\"")
                # logging.debug(f"Field from existing MWC has a value of \"{existing[index]}\"")

                same = compare_mwc_fields(new[index], existing[index])

                if not same:

                    return False

            else:

                logging.info(f"Changes detected in template. MWC Should update")
                # logging.debug(f"Changes: \n{new}\n")

                return False

    else:

        if existing != new:

            # logging.debug(f"Field from MWC Template has a value of \"{new}\"")
            # logging.debug(f"Field from existing MWC has a value of \"{existing}\"")

            logging.info(f"Changes detected in template. MWC Should update")
            # logging.debug(f"Changes: \n{new}\n")

            return False

    return True


################################################################################
################################################################################
################################################################################


def find_webhook_index(mwc_template):
    """Function to check if the ImageSwap webhook exists in the MWC template and return its index"""

    for index, webhook in enumerate(mwc_template["webhooks"]):

        if isinstance(webhook, dict):

            if webhook["name"] == imageswap_mwc_webhook_name:

                logging.debug(f"ImageSwap webhook index in MWC template: {index}")

                webhook_exists = True
                webhook_index = index

                return webhook_exists, webhook_index

    webhook_exists = False
    webhook_index = ""

    return webhook_exists, webhook_index


################################################################################
################################################################################
################################################################################


def mwc_should_update(
    namespace,
    configuration,
    mwc,
    mwc_template,
    imageswap_tls_byoc,
    core_api,
    admission_api,
):
    """Function to determine if an MWC should be updated"""

    # Need to read MWC again without converting field names to "pythonic" names.
    # This is to facilitate easier comparisons against the MWC template
    # Thanks Alex!
    # Would be nice to use "_preload_content=False" with existing object instance
    # to prevent an additional API call
    try:

        existing_mwc_raw = admission_api.read_mutating_webhook_configuration(mwc_template["metadata"]["name"], _preload_content=False)

    except ApiException as exception:

        logging.error(f'Unable to read MWC "{imageswap_mwc_name}": {exception}\n')
        sys.exit(1)

    existing_mwc = json.loads(existing_mwc_raw.data)

    logging.debug(f"MWC Template with CA Bundle: \n{mwc_template}\n")
    logging.debug(f"Existing MWC: \n{existing_mwc}\n")

    logging.info("Comparing existing MWC to template")
    mwcs_are_equal = compare_mwc_fields(mwc_template, existing_mwc)

    # If existing MWC and Template match, no need to update
    if mwcs_are_equal:

        logging.info(f"Existing MWC matches template")

        new_mwc = ""

        return False, new_mwc
    # If they don't match, we need to update the MWC
    else:

        logging.info(f"Changes were detected to MWC template")

        new_mwc = mwc_template

        return True, new_mwc


################################################################################
################################################################################
################################################################################


def read_mwc_from_template(namespace, configuration, imageswap_tls_byoc, core_api, admission_api):
    """Function to read k8s mutating webhook configuration"""

    # Read MWC template from local file (mounded from configmap)
    try:

        with open(imageswap_mwc_template_file) as mwc_file:

            mwc_template = yaml.safe_load(mwc_file)

            logging.debug(f"MWC Template from File: \n{mwc_template}\n")

    except IOError as exception:

        logging.error(f'Error opening MWC template file "{imageswap_mwc_template_file}": \n{exception}\n')
        sys.exit(1)

    # Get Root CA
    root_ca = get_rootca(namespace, configuration, imageswap_tls_byoc, core_api)
    webhook_exists, webhook_index = find_webhook_index(mwc_template)

    # Set CA Bundle in MWC template
    if webhook_exists:

        logging.info(f"Found ImageSwap webhook defined in the MWC template")

        mwc_template["webhooks"][webhook_index]["clientConfig"]["caBundle"] = root_ca

    else:

        logging.error(f"Did not find ImageSwap webhook defined in the MWC Template")
        sys.exit(1)

    return mwc_template


################################################################################
################################################################################
################################################################################


def read_mwc(admission_api):
    """Function to read k8s MWC"""

    try:

        mwc = admission_api.read_mutating_webhook_configuration(imageswap_mwc_name)

    except ApiException as exception:

        if exception.status != 404:

            logging.error(f'Unable to read MWC "{imageswap_mwc_name}": {exception}\n')
            sys.exit(1)

        elif exception.status == 404:

            logging.info(f'Did not find existing MWC "{imageswap_mwc_name}"')
            logging.debug(f"Exception:\n{exception}\n")

            mwc = ""
            return mwc

    logging.info(f'Existing MWC "{imageswap_mwc_name}" found')

    return mwc


################################################################################
################################################################################
################################################################################


def delete_mwc(namespace, admission_api):
    """Function to delete k8s mutating webhook configuration"""

    try:

        admission_api.delete_mutating_webhook_configuration(imageswap_mwc_name)

    except ApiException as exception:

        logging.error(f'Unable to delete MWC "{imageswap_mwc_name}": {exception}\n')
        sys.exit(1)

    logging.info("Deleted existing MWC")


################################################################################
################################################################################
################################################################################


def write_mwc(namespace, ca_secret_name, mwc, configuration, admission_api, core_api):
    """Function to create or update the k8s mutating webhook configuration"""

    # TO-DO (phenixblue): Need to work out how to validate TLS cert is signed by CA
    # verified = verify_mwc_cert_bundle(imageswap_mwc_name, admission_api)

    mwc_template = read_mwc_from_template(namespace, configuration, imageswap_tls_byoc, core_api, admission_api)

    # Figure out if there's an existing MWC that needs to be updated, or
    # if a new MWC should be created
    #
    # This check helps allow ImageSwap to scale out to multiple replicas without
    # each replica stomping on the MWC
    if mwc != "":

        should_update, mwc = mwc_should_update(
            namespace,
            configuration,
            mwc,
            mwc_template,
            imageswap_tls_byoc,
            core_api,
            admission_api,
        )

        if should_update:

            logging.info(f'Patching MWC "{imageswap_mwc_name}"')

            try:

                admission_api.patch_mutating_webhook_configuration(imageswap_mwc_name, mwc)

            except ApiException as exception:

                logging.error(f'Unable to patch MWC "{imageswap_mwc_name}": {exception}\n')
                sys.exit(1)

    else:

        mwc = mwc_template

        logging.info(f'Creating MWC "{imageswap_mwc_name}"')

        try:

            admission_api.create_mutating_webhook_configuration(mwc)

        except ApiException as exception:

            logging.error(f'Unable to create MWC "{imageswap_mwc_name}": {exception}\n')
            sys.exit(1)


################################################################################
################################################################################
################################################################################


def init_mwc(namespace, imageswap_tls_byoc):
    """Function to handle the k8s mutating webhook configuration"""

    try:

        config.load_incluster_config()

    except Exception as exception:

        logging.info(f"Exception loading incluster configuration: {exception}")

        try:
            logging.info("Loading local kubeconfig")
            config.load_kube_config()

        except Exception as exception:

            logging.error(f"Exception loading local kubeconfig: {exception}")
            sys.exit(1)

    configuration = client.Configuration().get_default_copy()
    core_api = client.CoreV1Api(client.ApiClient(configuration))
    admission_api = client.AdmissionregistrationV1Api(client.ApiClient(configuration))

    mwc = read_mwc(admission_api)
    write_mwc(
        namespace,
        imageswap_tls_rootca_secret_name,
        mwc,
        configuration,
        admission_api,
        core_api,
    )


################################################################################
################################################################################
################################################################################


def main():

    # Setup logging
    logging.basicConfig(
        level=os.getenv("IMAGESWAP_LOG_LEVEL", "INFO"),
        stream=sys.stdout,
        format="[%(asctime)s] %(levelname)s: %(message)s",
    )

    logging.info("ImageSwap Init")
    # Wait random time to help alleviate race conditions with multiple
    # replicas on startup
    # wait_time = random.randint(1,10)
    # time.sleep(wait_time)
    init_tls_pair(imageswap_namespace_name)
    init_mwc(imageswap_namespace_name, imageswap_tls_byoc)
    logging.info("Done")


################################################################################
################################################################################
################################################################################

if __name__ == "__main__":

    main()
