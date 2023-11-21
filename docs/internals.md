# Internals

Information about ImageSwap Webhook components

## Image

ImageSwap uses a couple of images for operation

- [imageswap-init](./app/imageswap-init/Dockerfile)
- [imageswap](./app/imageswap/Dockerfile)

### Init Container

ImageSwap uses the `imageswap-init` init-container to generate/rotate a TLS cert/key pair to secure communication between the Kubernetes API and the webhook. This action takes place on Pod startup.