[![Latest release](https://img.shields.io/github/release/phenixblue/imageswap-webhook.svg)](https://github.com/phenixblue/imageswap-webhook/releases/latest)
[![License](https://img.shields.io/badge/License-Apache%202.0-yellowgreen.svg)](https://github.com/tmobile/magtape/blob/master/LICENSE)
![python-checks](https://github.com/phenixblue/imageswap-webhook/workflows/python-checks/badge.svg)
![e2e-checks](https://github.com/phenixblue/imageswap-webhook/workflows/e2e-checks/badge.svg)
![image-build](https://github.com/phenixblue/imageswap-webhook/workflows/image-build/badge.svg)

# ImageSwap Mutating Admission Controller for Kubernetes

The ImageSwap [webhook](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#admission-webhooks) enables you to define one or more mappings to automatically swap image definitions within Kubernetes Pods with a different registry. This is useful to easily transition from external to internal image registries, work around rate limiting issues, or to maintain consistency with manifests in environments that are airgapped and unable to access commonly used image registries (DockerHub, Quay, GCR, etc.)

**An existing image:**

```
nginx/nginx:latest
```

**can be swapped to:**

```
registry.example.com/nginx/nginx:latest
```

## NOTICE

ImageSwap v1.4.0 has major changes

>**MAPS LOGIC:** There is a new [MAPS](#maps-mode) mode logic that has been added to allow for more flexibility in the image swapping logic.
>The existing logic, referred to as `LEGACY` mode, is still available, but has been deprecated.
>To continue using the `LEGACY` mode logic set the `IMAGESWAP_MODE` environment variable accordingly. Please reference the [configuration](#configuration) section for more information. 

>**Image Definition Preservation:** Updates have been made to how image definitions are processed during a swap. Previously the swap logic would drop the image org/project before adding the prefix (ie. `nginx/nginx-ingress:latest` would drop the `nginx/` portion of the image definition).
>In v1.4.0+ the swap logic will preserve all parts of the image except the Registry (ie. `docker.io/nginx/nginx-ingress` will drop the `docker.io` only from the image definition).

## Overview

- [Prereqs](#prereqs)
- [Quickstart](#quickstart)
- [Health Check](#health-check)
- [Image](#image)
- [Configuration](#configuration)
- [Advance Install](./docs/advanced_install.md)
- [Metrics](#metrics)
- [Testing](#testing)
- [Cautions](#cautions)
- [Troubleshooting](#troubleshooting)
- [Contributing](./CONTRIBUTING.md)
- [Adopters](./ADOPTERS.md)

## Prereqs

Kubernetes 1.9.0 or above with the admissionregistration.k8s.io/v1beta1 (or higher) API enabled. Verify that by the following command:

```shell
$ kubectl api-versions | grep admissionregistration.k8s.io/v1beta1
```

The result should be:

```shell
admissionregistration.k8s.io/v1beta1
```

In addition, the `MutatingAdmissionWebhook` and `ValidatingAdmissionWebhook` admission controllers should be added and listed in the correct order in the admission-control flag of kube-apiserver.

### Permissions

ImageSwap requires cluster-admin permissions to deploy to Kubernetes since it requires access to create/read/update/delete cluster scoped resources (MutatingWebhookConfigurations, Certificates, etc.)

### Quickstart

You can use the following command to install ImageSwap from this repo with sane defaults

**NOTE:** The quickstart installation is not meant for production use. Please read through the [Cautions](#cautions) sections, and as always, use your best judgement when configuring ImageSwap for production scenarios.

```shell
$ kubectl apply -f https://raw.githubusercontent.com/phenixblue/imageswap-webhook/v1.4.0/deploy/install.yaml
```

#### This will do the following

- Create the `imageswap-system` namespace
- Create cluster and namespace scoped roles/rolebindings
- Deploy the ImageSwap workload and related configs

#### Once this is complete you can do the following to test

Create and label a test namespace

```shell
$ kubectl create ns test1
$ kubectl label ns test1 k8s.twr.io/imageswap=enabled
```

Deploy some test workloads

```shell
# These examples assume you're in the root directory of this repo
# Example with without expected prefix

$ kubectl apply -f ./testing/deployments/test-deploy01.yaml -n test1

# Example with expected prefix

$ kubectl apply -f ./testing/deployments/test-deploy02.yaml -n test1
```

## Image

ImageSwap uses a couple of images for operation

- [imageswap-init](./app/imageswap-init/Dockerfile)
- [imageswap](./app/imageswap/Dockerfile)

### Init Container

ImageSwap uses the `imageswap-init` init-container to generate/rotate a TLS cert/key pair to secure communication between the Kubernetes API and the webhook. This action takes place on Pod startup.

## Configuration

A new `IMAGESWAP_MODE` environment variable has been added to control the imageswap logic for the webhook. The value should be `LEGACY` or `MAPS` (new default).

### MAPS Mode

MAPS Mode enables a high degree of flexibility for the ImageSwap Webhook.

In MAPS mode, the webhook reads from a `map file` that defines one or more mappings (key/value pairs) for imageswap logic. With the `map file` configuration, swap logic for multiple registries and patterns can be configured. In contrast, the LEGACY mode only allowed for a single `IMAGE_PREFIX` to be defined for image swaps.

A `map file` is composed of key/value pairs separated by a `:` and looks like this:

```
default:default.example.com
docker.io:my.example.com/mirror-
quay.io:quay.example3.com
gitlab.com:registry.example.com/gitlab
#gcr.io: # This is a comment 
cool.io:
registry.internal.twr.io:registry.example.com
harbor.geo.pks.twr.io:harbor2.com ###### This is a comment with many symbols
noswap_wildcards:twr.io, walrus.io
```

NOTE: Lines in the `map file` that are commented out with a leading `#` are ignored. Trailing comments following a map definition are also ignored.

The only mapping that is required in the `map_file` is the `default` map. The `default` map alone provides similar functionality to the `LEGACY` mode.

A map definition that includes a `key` only can be used to disable image swapping for that particular registry.

A map file can also include a special `noswap_wildcards` mapping that disables swapping based on greedy pattern matching. Don't actually include an `*` in this section. A value of `example` is essentialy equivalent to `*example*`. [See examples below for more detail](#example-maps-configs)

By adding additional mappings to the `map file`, you can have much finer granularity to control swapping logic per registry.


#### Example MAPS Configs

- Disable image swapping for all registries EXCEPT `gcr.io`

  ```
  default:
  gcr.io:harbor.internal.example.com
  ```

- Enable image swapping for all registries except `gcr.io`

  ```
  default: harbor.internal.example.com
  gcr.io:
  ```

- Imitate LEGACY functionality as close as possible

  ```
  default:harbor.internal.example.com
  noswap_wildcards:harbor.internal.example.com
  ```

  With this, all images will be swapped except those that already match the `harbor.internal.example.com` pattern

- Enable swapping for all registries except those that match the `example.com` pattern

  ```
  default:harbor.internal.example.com
  noswap_wildcards:example.com
  ```

  With this, images that have any part of the registry that matches `example.com` will skip the swap logic

  EXAMPLE:
    - `example.com/image:latest`
    - `external.example.com/image:v1.0`
    - `edge.example.com/image:latest`)

- Enable swapping for all registries, but skip those that match the `example.com` pattern, except for `external.example.com`

  ```
  default:harbor.internal.example.com
  external.example.com:harbor.internal.example.com
  noswap_wildcards:example.com
  ```

  With this, the `edge.example.com/image:latest` image would skip swapping, but `external.example.com/image:latest` would be swapped to `harbor.internal.example.com/image:latest`

- Enable different swapping for top level "library" images vs. images that are nested under a project/org

  Example library image: `nginx:latest`

  This format is a shortcut for `docker.io/library/nginx:latest`

  [Official Docker documentation on image naming](https://docs.docker.com/registry/introduction/#understanding-image-naming)

  ```
  default:
  docker.io:
  docker.io/library:harbor.example.com/library
  ```

  This map uses a special syntax of adding `/library` to a registry for the key in map file.

  With this, the `nginx:latest` image would be swapped to `harbor.example.com/library/nginx:latest`, but the `tmobile/magtape:latest` image would be swapped to `harbor.example.com/tmobile/magtape:latest`

  This configuration can be useful for scenarios like [Harbor's](https://goharbor.io) [image proxy cache](https://goharbor.io/docs/2.1.0/administration/configure-proxy-cache/) feature].

### LEGACY Mode

**DEPRECATED: This mode will be removed in a future release**

Change the `IMAGE_PREFIX` environment variable definition in the [imageswap-env-cm.yaml](./deploy/manifests/imageswap-env-cm.yaml) manifest to customize the repo/registry for the image prefix mutation.

### Granularly Disable Image Swapping for a Workload

You can also customize the label used to granularly disable ImageSwap on a per workload basis. By default the `k8s.twr.io/imageswap` label is used, but you can override that by specifying a custom label with the `IMAGESWAP_DISABLE_LABEL` environment variable.

The value of the label should be `disabled`.

See the [Break Glass: Per Workload](#per-workload) section for more details.

## Metrics

Prometheus formatted metrics for API rquests are exposed on the `/metrics` endpoint.

## Testing

Assuming you've followed the quickstart steps

- Review Deployment and Pod spec to validate the webhook is working

  ```shell
  $ kubectl get deploy hello-world -n test1 -o yaml
  $ kubectl get pods -n test1
  $ kubectl get pod <pod_name> -n test1 -o yaml
  ```

  NOTE: You should see the swapped image definition instead of the original definition in the `test-deploy.yaml` manifest.

## Cautions

### Production Considerations

- By Default the ImageSwap Mutating Webhook Configuration is set to fail "closed". Meaning if the webhook is unreachable or doesn't return an expected response, requests to the Kubernetes API will be blocked. Please adjust the configuration if this is not something that fits your environment.
- ImageSwap supports operation with multiple replicas that can increase availability and performance for critical clusters.
- The certificate generated by the `imageswap-init` container is valid for 12 months and will be automatically rotated once the Pod restarts within 6 months of expiration. If the certificate expires, calls to the webhook wil fail. Make sure you plan for this certificate rotation.

### Break Glass Scenarios

#### Per Workload

ImageSwap can be disabled on a per workload level by adding the `k8s.twr.io/imageswap` label with a value of `disabled` to the pod template.

Refer to this test manifest as an example: [./testing/deployments/test-deploy05.yaml](./testing/deployments/test-deploy05.yaml)
#### Per Namespace

ImageSwap can be enabled and disabled on a per namespace basis by utilizing the `k8s.twr.io/imageswap` label on the namespace resources. In emergency situations the label can be removed from a namespace to disable image swapping in that namespace.


#### Cluster Wide

If there are cluster-wide issues you can disable ImageSwap completely by removing the `imagewap-webhook` Mutating Webhook Configuration and deleting the ImageSwap deployment.

## Troubleshooting

### Run Docker Image Locally

```
$ docker run -p 5000:5000/tcp -it imageswapwebhook_app bash
$ ./deny-env.py
```

### Access Kubernetes Service without Ingress/LB

```shell
$ kubectl get pods # to get the name of the running pod
$ kubectl port-forward <pod_name> 5000:5000
```

### Use Curl to perform HTTP POST to webhook server

```shell
$ curl -vX POST https://localhost:5000/ -d @test.json -H "Content-Type: application/json"
```

### Follow logs of the webhook pod

```shell
$ kubectl get pods # to get the name of the running pod
$ kubectl logs <pod_name> -f
```
