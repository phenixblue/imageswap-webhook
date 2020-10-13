# Advanced Install

We've tried to build a decent amount of flexibility into ImageSwap. While the simple installation method is great for demos and POC's, more care should be taken when deploying to Production type environments. The information in this document serves as general guidelines for what is possible, but is NOT a step by step guide. Some reading between the lines is required.

## Configuration Options

NOTE: The following environment variable are defined in the `imageswap-env-cm.yaml` manifest and can be used to customize ImageSwap's behavior.

| Variable                 | Description                                 | Values                        |
|---                       |---                                          |---                            |
| `IMAGESWAP_LOG_LEVEL`    | The log level to use                        | `INFO` or `DEBUG`             |
| `IMAGE_PREFIX`           | The prefix to use in the image swap         | Any value supported for the [Kubernetes Container spec image field](https://kubernetes.io/docs/concepts/containers/images/#image-names)      |

## Installation

ImageSwap can be setup to use [kustomize](https://kustomize.io) to handle config substitution and generating the YAML manifests to deploy to Kubernetes.

The kustomize layout uses overlays to allow for flexibility in configuration (ie. per environment (Development, Production, etc.) or per cluster substitutions)

You can find some generic examples of using kustomize overlays to manage per environment configuration in the following directories:

| DIRECTORY                       | DESCRIPTION                                       |
|---                              |---                                                |
| `deploy/manifests`              | The base YAML manifests                           |
| `deploy/overlays/development`   | Development environment specific substitutions    |
| `deploy/overlays/production`    | Production environment specific substitutions     |
| `IMAGESWAP_TLS_SECRET`          | **OPTIONAL** - Overrides the default secret (`imageswap-tls`) for BYOC (Bring Your Own Cert) scenarios  | <name_of_secret> (STRING)     |

Once the proper edits have been made you can generate the YAML manifests:

```shell
$ kustomize build deploy/overlays/development | kubectl -n <namespace> apply -f -
```

### Special Considerations

There are some configurations that will require a little more effort when not using the simple install process:

#### Others

NOTE: A TLS Cert and Key need to be generated for the Webhook. MagTape has an init container that can handle generating the required tls cert/key pair or you can BYOC ([Bring Your Own Cert](#bring-your-own-cert)). The init process uses the Kubernetes `CertificateSigningRequest` API to generate a certificate signed by the Kubernetes CA. The VWC (ValidatingWebhookConfiguration) is also deployed during the init process and the `caBundle` field is automatically populated based on the configuration supplied. The [VWC configuration](#vwc-template) is managed via a template in a configmap.

## Bring Your Own Cert

By default ImageSwap will handle creation and rotation of the required TLS cert/key automatically. In cases where you need to BYOC, you can adjust the configuration.

### Specify a different secret name

Reference the `IMAGESWAP_TLS_SECRET` option in the [configuration options](#configuration-options) section.

### Root CA

The MWC (Mutating Webhook Configuration) needs to be configured with a cert bundle that includes the CA that signed the certificate and key used to secure the ImageSwap API. For now ImageSwap assumes this CA certificate exists in the `imageswap-tls-ca` secret deployed within the `imageswap-system` namespace. This secret must exist prior to installing ImageSwap.

No validation is done currently to ensure the specified CA actually signed the cert and key used to secure ImageSwap's API. 

## MWC Template

ImageSwap makes use of the Kubernetes MWC (Mutating Webhook Configuration) feature. This means it requires a `MutatingWebhookConfiguration` resource to be deployed. The ImageSwap init process takes care of creating the MWC resource for you. ImageSwap uses a template defined within a configmap resource for the MWC creation.  

You can adjust the MWC configuration in [this file](/deploy/manifests/imageswap-mwc.yaml). A configmap generator within the [kustomization.yaml](/deploy/manifests/kustomization.yaml) file is used to take the MWC template and create the configmap.
