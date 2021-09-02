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

## 1.3.1
### Enhancements

Bump cryptography from 3.2 to 3.3.2 in /app/imageswap-init (Dependabot)

    Bumps [cryptography](https://github.com/pyca/cryptography) from 3.2 to 3.3.2.
    - [Release notes](https://github.com/pyca/cryptography/releases)
    - [Changelog](https://github.com/pyca/cryptography/blob/master/CHANGELOG.rst)
    - [Commits](https://github.com/pyca/cryptography/compare/3.2...3.3.2)

## 1.4.0

This release addresses a few security fixes for dependent libraries and introduces some major enhancements.

**!!! Please read carefully as there is new functoinality that is not directly backwards compatible !!!**

ImageSwap v1.4.0 requires some new configuration settings and makes major changes to the default image swap logic.


### Enhancements

- Introduces new MAPS swap mode logic (#29)
- Updates to logging when disable label is supplied (#29)
- Added a kustomize overlay for LEGACY swap mode (#29)
- Update image swap logic to preserve image org/project (#29)

>**MAPS LOGIC:** There is a new [MAPS](#maps-mode) mode logic that has been added to allow for more flexibility in the image swapping logic.
>The existing logic, referred to as `LEGACY` mode, is still available, but has been deprecated.
>To continue using the `LEGACY` mode logic set the `IMAGESWAP_MODE` environment variable accordingly. Please reference the [configuration](#configuration) section for more information. 

>**Image Definition Preservation:** Updates have been made to how image definitions are processed during a swap. Previously the swap logic would drop the image org/project before adding the prefix (ie. `nginx/nginx-ingress:latest` would drop the `nginx/` portion of the image definition).
>In v1.4.0+ the swap logic will preserve all parts of the image except the Registry (ie. `docker.io/nginx/nginx-ingress` will drop the `docker.io` only from the image definition).

### Security Fixes

- Bump jinja2 from 2.11.2 to 2.11.3 in /app/imageswap (#28 authored by dependabot)
- Bump urllib3 from 1.26.3 to 1.26.4 in /app/imageswap-init (#26 authored by dependabot)
- Bump urllib3 from 1.26.4 to 1.26.5 in /app/imageswap-init (#25 authored by dependabot)

## 1.4.1

This release adds logic to process maps for library level images differently from images nested under a specific project/organization.

**EXAMPLE:**

```
docker.io:harbor.example.com
docker.io-library:harbor.example.com/library
```

This would be the output for the library vs. non-library images:

`nginx:latest` **->** `harbor.example.com/library/nginx:latest`

`tmobile/magtape:latest` **->** `harbor.example.com/tmobile/magtape:latest`

This is applicable for use cases such as the [Harbor projects image pull-through cache](https://goharbor.io/docs/2.1.0/administration/configure-proxy-cache/)

- See the [maps examples](https://github.com/phenixblue/imageswap-webhook/blob/9e8d9abb9ed9b7e480140e64ff730a4c4eaf716c/README.md#maps-mode) for specific syntax on using the library map
- [Docker documentation for image naming](https://docs.docker.com/registry/introduction/#understanding-image-naming)

### Enhancements

- Add logic to handle maps for library level images (#42)

### Acknowledgements

- Thanks to @fragolinux for the suggestion!

## 1.4.2

This release fixes a bug in the image swap logic related to a scenario where a library level image is used and the image tag contains `.`'s.

More info can be found in this issue: #46

### Enhancements

- Add fix for dotted tag on library image (#47)

### Acknowledgements

- Thanks to @adavenpo for bringing this to our attention

## 1.4.3

This release moves to using a new syntax (`::`) to separate the key and value portions of a map definition in the maps file. Backwards compatibility is maintained for the existing `:` syntax, but this has been deprecated and should not be used. Please update any existing map configurations to use the new syntax.

This release also adds additional validation to catch errors associated with specifying a registry in a map definition key that includes the `:<port_number>` syntax. Previously this would result in an error and a stack trace. This is now handled gracefully and the new map separator syntax should allow for registries to include ports going forward.

### Enhancements

- Add support for new map definition deparator syntax (#50)

### Acknowledgements

- Thanks to @sblair-metrostar for bringing this to our attention

