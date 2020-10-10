# ImageSwap Mutating Admission Controller for Kubernetes

This is an example Kubernetes Mutating [Admission Controller](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#admission-webhooks).

This webhook will swap the existing image definition in a deployment with a user specified prefix + the image. This allows you to use the same manifests for airgapped environments that don't have access to commonly used image registries (dockerhub, quay, gcr, etc.). 

The webhook is written in `Python` using the `Flask` framework.

**!!!! I'm currenty working on some major refactoring and the master branch may not be ina  working state. Pease reference specific tags for known good working states.!!!!**

## Example

Existing Image Definition:

```yaml
example-image:1.0
```

Image After the Swap:

```yaml
/my/cool/prefix/example-image:1.0
```

## Overview

- [Prereqs](#prereqs)
- [Quickstart](#quickstart)
- [Health Check](#health-check)
- [Image](#image)
- [Configuration](#configuration)
- [Metrics](#metrics)
- [Testing](#testing)
- [Cautions](#cautions)
- [Troubleshooting](#troubleshooting)

## Prereqs

Kubernetes 1.9.0 or above with the admissionregistration.k8s.io/v1beta1 API enabled. Verify that by the following command:

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
$ kubectl apply -f https://raw.githubusercontent.com/phenixblue/imageswap-webhook/master/deploy/install.yaml
```

#### This will do the following

- Create the `imageswap-system` namespace
- Create cluster scoped role/rolebinding
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

## Configuration

Change the `IMAGE_PREFIX` environment variable definition in the [imageswap-env-cm.yaml](./deploy/manifests/imageswap-env-cm.yaml) manifest to customize the repo/registry for the image prefix mutation.

## Metrics

Prometheus formatted metrics are exposed on the `/metrics` endpoint. Metrics track general resource usage and counters for requests (CPU, Memory, HTTP error rate, etc.).

## Testing

Assuming you've folowed the quickstart steps

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

### Break Glass Scenarios

ImageSwap can be enabled and disabled on a per namespace basis by utilizing the `k8s.twr.io/imageswap` label on namespace resources. In emergency situations the label can be removed from a namespace to disable image swapping in that namespace.

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
