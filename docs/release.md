# Release Process

## Overview

The release process consists of two phases: versioning and publishing.

Versioning involves maintaining the following files:

- **CHANGELOG.md** - this file contains a list of all the important changes in each release.
- **Makefile** - the Makefile contains the `IMAGESWAP_VERSION` and `IMAGESWAP_INIT_VERSION` variables to set the version for each.

The steps below explain how to update these files. In addition, the repository
should be tagged with the semantic version identifying the release.

Publishing involves creating a new *Release* on GitHub with the relevant
CHANGELOG.md snippet.

## Versioning

1. Obtain a copy of repository.

	```
	git clone git@github.com:phenixblue/imageswap-webhook.git
	```

1. Set version variables within Makefile:

	```
	IMAGESWAP_VERSION := v1.2.0
    IMAGESWAP_INIT_VERSION := v0.0.1
	```

1. Update version in deployment manifest and generate new single install manifest:

	```
	make set-release-version
    make build-single-manifest
	```

1. Commit the changes and push to remote repository.

	```
	git commit -a -s -m "Prepare v<version> release"
	git push origin master
	```

1. Tag repository with release version and push tags to remote repository.

	```
	git tag v<semver>
	git push origin --tags
	```

## Publishing

1. Open browser and go to https://github.com/phenixblue/imageswap-webhook/releases

1. Create a new release for the version.
	- Copy the changelog content into the message.

## Notes

- The thewebroot/imageswap-init and thewebroot/imageswap Docker images are automatically built and published to Docker Hub when a release is created. There are no manual steps involved here.
