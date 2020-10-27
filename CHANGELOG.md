# Change Log

## 1.2.0

This release is a major overhaul to introduce many things I've learned since I first wrote the ImageSwap Webhook.

### Enhancements

- Add additional fields to Admission Response (UID, apiversion, and kind) to support latest standard
- Add Init container to manage certificate and MWC automatically
- Added Service Account for pod to run as
- Add cluster role/CRB for Service Account to support certificate and MWC management
- Add Makefile
- Add GitHub Actions for CI
- Move to single install manifest for simple demo installs
- Add kustomize with example overlays for advanced installs
- Added license boilerplate header/automation
- Added code of conduct, contributor guidelines, and security procedures
- Added Pipfile/Pipfile.lock and docker files for more consistent builds
- Moved to app baked into image vs. mounted via configmap
- Added support for init-containers
- Added functional testing framework
- Updated Readme
- Added simple API metrics
- Added proper logging for INFO and DEBUG log levels

## 1.3.0

### Enhancements

Adds support for image prefixes that end with a `-`. (#14)

