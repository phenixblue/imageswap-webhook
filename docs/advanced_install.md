# Advanced Install

We've tried to build a decent amount of flexibility into ImageSwap. While the simple installation method is great for demos and POC's, more care should be taken when deploying to Production type environments. The information in this document serves as general guidelines for what is possible, but is NOT a step by step guide. Some reading between the lines is required.

## Configuration Options

NOTE: The following environment variable are defined in the `imageswap-env-cm.yaml` manifest and can be used to customize ImageSwap's behavior.

| Variable                    | Description                                 | Values                        |
|---                          |---                                          |---                            |
| `IMAGESWAP_LOG_LEVEL`       | The log level to use                        | `INFO` or `DEBUG`             |
| `IMAGE_PREFIX` (**DEPRECATED**)          | The prefix to use in the image swap         | Any value supported for the [Kubernetes Container spec image field](https://kubernetes.io/docs/concepts/containers/images/#image-names)      |
| `IMAGESWAP_MODE`            | The operating mode for the swap logic       | `MAPS` (default in v1.4.0+) or `LEGACY`              |
| `IMAGESWAP_MAPS_FILE`       | The location of the MAPS file               | `/app/maps/imageswap-maps.conf` (default)            |
| `IMAGESWAP_DISABLE_LABEL`   | The label to identify granular disablement of image swapping per resource | `k8s.twr.io/imageswap` |
| `IMAGESWAP_CSR_SIGNER_NAME` | The name of the Kubernetes signer to create the API certificate | `kubernetes.io/kubelet-serving`  |

## Installation

ImageSwap can be setup to use [kustomize](https://kustomize.io) to handle config substitution and generating the YAML manifests to deploy to Kubernetes.

The kustomize layout uses overlays to allow for flexibility in configuration (ie. per environment (Development, Production, etc.) or per cluster substitutions)

You can find some generic examples of using kustomize overlays to manage per environment configuration in the following directories:

| DIRECTORY                       | DESCRIPTION                                       |
|---                              |---                                                |
| `deploy/manifests`              | The base YAML manifests                           |
| `deploy/overlays/ghcr.io`       | Base + Image references swapped to ghcr.io registry |
| `deploy/overlays/development`   | Development environment specific substitutions    |
| `deploy/overlays/production`    | Production environment specific substitutions     |

Once the proper edits have been made you can generate the YAML manifests:

```shell
$ kustomize build deploy/overlays/development | kubectl -n <namespace> apply -f -
```

### Special Considerations

There are some configurations that will require a little more effort when not using the simple install process:

#### Others

NOTE: A TLS Cert and Key need to be generated for the Webhook. MagTape has an init container that can handle generating the required tls cert/key pair or you can BYOC ([Bring Your Own Cert](#bring-your-own-cert)). The init process uses the Kubernetes `CertificateSigningRequest` API to generate a certificate signed by the Kubernetes CA. The VWC (ValidatingWebhookConfiguration) is also deployed during the init process and the `caBundle` field is automatically populated based on the configuration supplied. The [VWC configuration](#vwc-template) is managed via a template in a configmap.

## Bring Your Own Cert

By default ImageSwap will use the Kubernetes Certificate API to handle creation and rotation of the required TLS cert/key automatically. In cases where you need to BYOC, you will need to handle certificate creation and rotation yourself.

Create the `imageswap-tls` secret in the `imageswap-system` namespace and add the `imageswap-byoc` anntation.

>NOTE: Any value for this annotation is acceptable, the annotation just needs to exist.

```shell
$ kubectl create secret tls imageswap-tls --cert=/path/to/cert.pem --key=/path/to/key.pem -n imageswap-system
```

Create the `imageswap-tls-ca` secret in the `imageswap-system` and add the pem formatted CA Certificate to the `rootca.pem` key

```shell
$ kubectl create secret generic imageswap-tls-ca --from-file=rootca.pem=./path/to/rootca.pem -n imageswap-system
```

### Root CA

The MWC (Mutating Webhook Configuration) needs to be configured with a cert bundle that includes the CA that signed the certificate and key used to secure the ImageSwap API. For now ImageSwap assumes this CA certificate exists in the `imageswap-tls-ca` secret deployed within the `imageswap-system` namespace. This secret must exist prior to installing ImageSwap.

No validation is done currently to ensure the specified CA actually signed the cert and key used to secure ImageSwap's API.

## MWC Template

ImageSwap makes use of the Kubernetes MWC (Mutating Webhook Configuration) feature. This means it requires a `MutatingWebhookConfiguration` resource to be deployed. The ImageSwap init process takes care of creating the MWC resource for you. ImageSwap uses a template defined within a configmap resource for the MWC creation.  

You can adjust the MWC configuration in [this file](/deploy/manifests/imageswap-mwc.yaml). A configmap generator within the [kustomization.yaml](/deploy/manifests/kustomization.yaml) file is used to take the MWC template and create the configmap.
