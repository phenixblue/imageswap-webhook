# Notice

## Kubernetes APIs upgrades

>**Deprecated APIs in v1.22** Because the end of support for some beta APIs the code received some important updates. Now you need to specify a signer for your Certificate Signing Request. You can take a look on the official documentation about API changes [Reference API deprecation](https://kubernetes.io/docs/reference/using-api/deprecation-guide/#v1-22).

>**K8s prior to v1.19** ImageSwap v1.5.0+ drops support for k8s versions below v1.19 and will no longer work due to the `admissionregistration.k8s.io/v1beta1` api deprecation. For deployment on K8s version v1.19 and before, please use ImageSwap v1.4.x.

>**EKS 1.22** To use ImageSwap you'll need to setup an Amazon exclusive signer [`beta.eks.amazonaws.com/app-serving`](https://docs.aws.amazon.com/eks/latest/userguide/cert-signing.html). Look at `client.V1CertificateSigningRequestSpec()` on `app/imageswap-init/imageswap-init.py`.
```
k8s_csr_spec = client.V1CertificateSigningRequestSpec(
        groups=["system:authenticated"],
        usages=["digital signature", "key encipherment", "server auth"],
        request=base64.b64encode(csr_pem).decode("utf-8").rstrip(),
        signer_name="beta.eks.amazonaws.com/app-serving"
    )
```

## ImageSwap v1.4.0 has major changes

>**MAPS LOGIC:** There is a new [MAPS](#maps-mode) mode logic that has been added to allow for more flexibility in the image swapping logic.
>The existing logic, referred to as `LEGACY` mode, is still available, but has been deprecated.
>To continue using the `LEGACY` mode logic set the `IMAGESWAP_MODE` environment variable accordingly. Please reference the [configuration](#configuration) section for more information.

>**Image Definition Preservation:** Updates have been made to how image definitions are processed during a swap. Previously the swap logic would drop the image org/project before adding the prefix (ie. `nginx/nginx-ingress:latest` would drop the `nginx/` portion of the image definition).
>In v1.4.0+ the swap logic will preserve all parts of the image except the Registry (ie. `docker.io/nginx/nginx-ingress` will drop the `docker.io` only from the image definition).