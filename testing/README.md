# Testing Info

Below is a list of test files to use with testing various features and scenarios of the ImageSwap Webhook. Most of the test files should also have associated JSON files:

- YAML File - Used for applying directly to a Kubernetes cluster
- JSON Request Object File - Used for testing the ImageSwap application outside of Kubernetes
- JSON Response File - Used for validating responses from various functions/calls of the ImageSwap application

Some files listed below don't exist yet. They are listed for tracking purposes and will be added in the future.

## Test Samples Available

| File                               | Test Type                                      |
|---                                 |---                                             |
| **Deployment Tests**                                                                |
| [test-deploy01.yaml](./deployments/test-deploy01.yaml)        | DEPLOYMENT, pass all policies                  |
| [test-deploy02.yaml](./deployments/test-deploy02.yaml)        | DEPLOYMENT, fail all policies                  |

## Functional Tests

Functional tests for ImageSwap are based on the files linked above. Any new tests added will require certain consideration to be picked up by the end-to-end CI tests.

The [functional-tests.yaml](./functional-tests.yaml) file contains the tests that get executed within the CI workflows and what results are expected (pass or fail). Each test should fall under the appropriate resource and result section of the file. For example, a new test for deployments that should result in a fail would be added like this:

```yaml
resources:
  - kind: deployments
    desired: pass
    script:
    manifests:
      - test-deploy01.yaml
      - test-deploy02.yaml
  - kind: deployments
    desired: fail
    script: 
    manifests:
      - test-deploy03.yaml
```
