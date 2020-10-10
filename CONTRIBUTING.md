# Contributing to ImageSwap

## Welcome

Welcome!

We welcome contributions from the community. Please read the following guidelines carefully to maximize the chances of your PR being merged.

## Communication

- Before starting work on a major feature, please reach out to us via GitHub, email, etc. We will make sure no one else is already working on it and ask you to open a GitHub issue.
- A "major feature" is defined as any change that is > 100 LOC altered (not including tests), or changes to any user-facing behavior. We will use the GitHub issue to discuss the feature and come to agreement on design/implementation.
- Small patches and bug fixes don't need prior communication.

## Coding Style

We don't follow a strict coding style, but we do have a few preferences:

- Favor readability of code...always!
- Don't wrap code unless it makes sense. Our monitors are plenty big that lines beyond 80 chars shouldn't be a problem.
- Use names that are intuitive...shorter isn't always better (ie. No single-character variable names)
- Prefer kebab case for file names where possible (ie. `some-file-name.md` and NOT `Some-file_name.md`)
- Always use `.yaml` and never `.yml`

### Python

For Python code we use [black](https://github.com/psf/black) for code formatting. Run the following if you make changes to any Python code:

```shell
# Lint and apply formatting
$ make lint
```

## Copyright Boilerplate

All code files must include a copyright header unless doing so breaks functionality in some way. This type of header is commonly referred to as "boilerplate" and you can check for boilerplate across all appropriate files by running the following:

```shell
$ make boilerplate
```

Specific contents of the boilerplate can be found in `hack/boilerplate`

## Reporting Issues

This is a great way to contribute. Before reporting an issue, please review current open issues to see if there are any matches.

### How to report an issue

Issues should be reported to this project's Github Issues page: https://github.com/phenixblue/imageswap-webhook/issues

When reporting an issue, please provide as much detail as possible about how to reproduce the problem.

There is a pre-built template for bug ticketing that can be used for reporting issues. Please fill in the requested info specified within the template to ensure quickest resolution.

## Submitting a PR

- Fork the repo
- Create your PR
- Tests should run automatically to cover linting, unit tests, and functional tests where applicable.
- Any PR that changes user-facing functionality should be accompanied by the appropriate documentation (comments, README's, etc.).
- Any PR that makes enhancements to ImageSwap's core code should be accompanied with proper unit and functional tests.
- All code comments and documentation are expected to have proper English grammar and punctuation. If you are not a fluent English speaker (or you are just a bad writer ;-)) please let us know and we will try to find some help but there are no guarantees.
- Once you submit a PR, please do not rebase it. It's much easier to review if subsequent commits are new commits and/or merges.
- We expect that once a PR is opened, it will be actively worked on until it is merged or closed. We reserve the right to close PRs that are not making progress. This is generally defined as no changes for 7 days. Obviously PRs that are closed due to lack of activity can be reopened later. Closing stale PRs helps us to keep on top of all the work currently in flight.

## PR review policy for maintainers

- Typically we try to turn around reviews within 2 business days.
- It is generally expected that a "domain expert" for the code the PR touches should review the PR. This person does not necessarily need to have commit access.
- The above rule may be waived for PRs which only update docs or comments, or trivial changes to tests and tools (where trivial is decided by the maintainer in question).
- Anyone is welcome to review any PR that they want, whether they are a maintainer or not.
