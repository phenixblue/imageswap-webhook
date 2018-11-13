# Image Swap Mutating Webhook for Kubernetes [![](https://images.microbadger.com/badges/version/jmsearcy/imageswap-webhook.svg)](https://microbadger.com/images/jmsearcy/imageswap-webhook "Get your own version badge on microbadger.com") [![](https://images.microbadger.com/badges/image/jmsearcy/imageswap-webhook.svg)](https://microbadger.com/images/jmsearcy/imageswap-webhook "Get your own image badge on microbadger.com")

This is an example Kubernetes Mutating [Admission Webhook](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#admission-webhooks).

This webhook will swap the existing image definition in a deployment with a user specified prefix + the image. This allows you to use the same manifests for airgapped environments that don't have access to commonly used image registries (dockerhub, quay, gcr, etc.). The webhook is written in `Python` using the `Flask` framework.


### Example:

Existing Image Definition:

```
example-image:1.0
```

Image After the Swap:

```
/my/cool/prefix/example-image:1.0
```


## Prereqs

Kubernetes 1.9.0 or above with the admissionregistration.k8s.io/v1beta1 API enabled. Verify that by the following command:

```
$ kubectl api-versions | grep admissionregistration.k8s.io/v1beta1
```

The result should be:

```
admissionregistration.k8s.io/v1beta1
```

In addition, the `MutatingAdmissionWebhook` and `ValidatingAdmissionWebhook` admission controllers should be added and listed in the correct order in the admission-control flag of kube-apiserver.

## Build Image

- Build the image locally

    ```
    $ cd ./docker/
    $ docker-compose build
    ```

- Push the image to a repository

    ```
    $ docker login
    $ docker tag imageswap-webhook:0.1 jmsearcy/imageswap-webhook:0.1
    $ docker push jmsearcy/imageswap-webhook:0.1
    ```

## Deploy Webhook

- Create a signed cert/key pair and store it in a Kubernetes secret

  ```
  ./deploy/webhook-ssl-cert-gen.sh \
    --service imageswap-webhook-svc \
    --secret imageswap-webhook-mwc-patched \
    --namespace default
  ```

- Patch the `MutatingWebhookConfiguration` by substituting the `$CA_BUNDLE` value from the running cluster

  ```
  cat ./deploy/imageswap-webhook-mwc.yaml | \
    ./deploy/webhook-patch-ca-bundle.sh > \
    ./deploy/imageswap-webhook-mwc-patched.yaml
  ```

- Deploy script via Kubernetes configmap

  ```
  $ kubectl create cm imageswap-webhook-cm --from-file=script=./app/imageswap-webhook-deploy.py
  ```

- Deploy resources

  ```
  $ kubectl apply -f ./deploy/imageswap-webhook-deploy.yaml
  $ kubectl apply -f ./deploy/imageswap-webhook-svc.yaml
  $ kubectl apply -f ./deploy/imageswap-webhook-mwc-patched.yaml
  ```

  NOTE: Change the `IMAGE_PREFIX` environment variable definition in the `imageswap-webhook-deploy.yaml` manifest to customize the repo/registry for the image prefix mutation.

## Testing

- Create namespace for testing and label it appropriately to enable image swapping

  ```
  $ kubectl create ns test1
  $ kubectl label ns test1 k8s.twr.io/imageswap=enabled
  ```

- Deploy test deployment to Kubernetes cluster

  ```
  $ kubectl apply -f ./testing/test-deploy.yaml -n test1
  ```

- Review Deployment and Pod spec to validate the webhook is working

  ```
  $ kubectl get deploy hello-world -n test1 -o yaml
  $ kubectl get pods -n test1
  $ kubectl get pod <pod_name> -n test1 -o yaml
  ```

  NOTE: You should see the swapped image definition instead of the original definition in the `test-deploy.yaml` manifest.





## Troubleshooting

### Run Docker Image Locally
```
$ docker run -p 5000:5000/tcp -it imageswapwebhook_app bash
$ ./deny-env.py
```

### Access Kubernetes Service without Ingress/LB
```
$ kubectl get pods # to get the name of the running pod
$ kubectl port-forward <pod_name> 5000:5000
```

### Use Curl to perform HTTP POST to webhook server

```
$ curl -vX POST https://localhost:5000/ -d @test.json -H "Content-Type: application/json"
```

### Follow logs of the webhook pod

```
$ kubectl get pods # to get the name of the running pod
$ kubectl logs <pod_name> -f
