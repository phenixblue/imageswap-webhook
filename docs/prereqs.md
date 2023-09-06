# Prereqs

Kubernetes 1.19.0 or above with the `admissionregistration.k8s.io/v1` (or higher) API enabled. Verify that by the following command:

```shell
$ kubectl api-versions | grep admissionregistration.k8s.io/v1
```

The result should be:

```shell
admissionregistration.k8s.io/v1
```

In addition, the `MutatingAdmissionWebhook` and `ValidatingAdmissionWebhook` admission controllers should be added and listed in the correct order in the admission-control flag of kube-apiserver.

## Permissions

ImageSwap requires cluster-admin permissions to deploy to Kubernetes since it requires access to create/read/update/delete cluster scoped resources (MutatingWebhookConfigurations, Certificates, etc.)