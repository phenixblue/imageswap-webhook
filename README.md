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

Find version/environment specific notices and information [here](./docs/notice.md)

## Overview

- [Prereqs](#prereqs)
- [Quickstart](#quickstart)
- [Internals](./docs/internals.md)
- [Configuration](./docs/configuration.md)
- [Advance Install](./docs/advanced_install.md)
- [Operations](./docs/operations.md)
- [Contributing](./CONTRIBUTING.md)
- [Adopters](./ADOPTERS.md)

### Quickstart

You can use the following command to install ImageSwap from this repo with sane defaults

**NOTE:** The quickstart installation is not meant for production use. Please read through the [Cautions](#cautions) sections, and as always, use your best judgement when configuring ImageSwap for production scenarios.

```shell
$ kubectl apply -f https://raw.githubusercontent.com/phenixblue/imageswap-webhook/v1.5.3/deploy/install.yaml
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
