# Release Process

## Overview

The release process consists of two phases: versioning and publishing.

Versioning involves maintaining the following files:

- **CHANGELOG.md** - this file contains a list of all the important changes in each release.
- **Makefile** - the Makefile contains a few `*_VERSION` variables that define the version of a few components in the project.

The steps below explain how to update these files. In addition, the repository
should be tagged with the semantic version identifying the release.

Publishing involves creating a new *Release* on GitHub with the relevant
CHANGELOG.md snippet.

## Versioning

1. Fork and clone the repository.

	```shell
	$ git clone git@github.com:phenixblue/imageswap-webhook.git
	```

1. Set version variables within Makefile:

	```makefile
	IMAGESWAP_VERSION := v1.2.0
	IMAGESWAP_INIT_VERSION := v0.0.1
	```

    NOTE: This version info is used to populate the correct versions throughout several files in the repo.

1. Set the release version and generate new single install manifest:

	```shell
	$ make set-release-version
	$ make build-single-manifest
	```

1. Update the demo install reference in the README (only for stable releases)

	```shell
	$ kubectl apply -f https://raw.githubusercontent.com/phenixblue/imageswap-webhook/<TAG>/deploy/install.yaml
	```

	NOTE: The tip of the master branch may not always provide an ideal user experience so we should keep this link pointed at a stable release tag to provide a smooth experience for visitors browsing the repo.

1. Commit the changes, push to your fork, and open a PR.

	```shell
	$ git commit -a -s -m "Prepare v<version> release"
	$ git push
	```

	NOTE: Verify CI jobs complete successully, have the PR Reviewed, and then Merge the PR

1. Tag repository with release version and push tag.

	```
	$ git tag v<semver>
	$ git push origin --tags
	```

	NOTE: This should be done directly on the ImageSwap repo, not a fork (ie. You must be a Maintainer)

## Publishing

1. Open browser and go to https://github.com/phenixblue/imageswap-webhook/releases

1. Create a new release for the version.
	- Copy the changelog content into the message.

	NOTE: You may have to adjust the Markdown Headers (ie. `#`) since the Headers for a specific release in the CHANGELOG.md file are not top level (ie. They start with `##` instead of `#`)

## Container Images

The `thewebroot/imageswap-init` and `thewebroot/imageswap` Docker images are automatically built and published to Docker Hub when a release is created. 

Images are published for the following platforms:

- linux/amd64
- linux/arm64

There are no manual steps involved here.
