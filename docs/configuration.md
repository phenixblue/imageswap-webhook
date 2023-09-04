# Configuration

A new `IMAGESWAP_MODE` environment variable has been added to control the imageswap logic for the webhook. The value should be `LEGACY` or `MAPS` (new default).

## MAPS Mode

MAPS Mode enables a high degree of flexibility for the ImageSwap Webhook.

In MAPS mode, the webhook reads from a `map file` that defines one or more mappings (key/value pairs) for imageswap logic. With the `map file` configuration, swap logic for multiple registries and patterns can be configured. In contrast, the LEGACY mode only allowed for a single `IMAGE_PREFIX` to be defined for image swaps.

A `map file` is composed of key/value pairs separated by a `::` and looks like this:

```
default::default.example.com
docker.io::my.example.com/mirror-
quay.io::quay.example3.com
gitlab.com::registry.example.com/gitlab
#gcr.io:: # This is a comment 
cool.io::
registry.internal.twr.io::registry.example.com
harbor.geo.pks.twr.io::harbor2.com ###### This is a comment with many symbols
noswap_wildcards::twr.io, walrus.io
# exact image mapping (full docker image name)
[EXACT]ghcr.io/fantasy/coolstuff:v1.0::my-local-registry.com/patched-coolstuff:latest
# replace image mapping (unix shell-style wildcards)
[REPLACE]ghcr.io/public*::my-local-registry.com
```

NOTE: Lines in the `map file` that are commented out with a leading `#` are ignored. Trailing comments following a map definition are also ignored.

NOTE: Previous versions of ImageSwap used a single `:` syntax to separate the key and value portions of a map definition. This syntax is deprecated as of v1.4.3 and will be removed in future versions. Please be sure to update any existing map file configurations to use the new syntax (ie. `::`).

NOTE: Prior to v1.4.3 any use of a registry that includes a port for the key of a map definition will result in errors.

The only mapping that is required in the `map_file` is the `default` map. The `default` map alone provides similar functionality to the `LEGACY` mode.

A map definition that includes a `key` only can be used to disable image swapping for that particular registry.

A map file can also include a special `noswap_wildcards` mapping that disables swapping based on greedy pattern matching. Don't actually include an `*` in this section. A value of `example` is essentially equivalent to `*example*`. [See examples below for more detail](#example-maps-configs)

By adding additional mappings to the `map file`, you can have much finer granularity to control swapping logic per registry.

### Exact Image Mapping

Map definitions can become explicit mappings for individual images by using the `[EXACT]` prefix.

Usage:

```
[EXACT]<source-image>::<target-image>
```

`Exact` maps will be matched exactly against the `<source-image>` name and replaced with the `<target-image>` name. No inferences for registry (ie. `docker.io/`), or tag (ie. `:latest`) will be inferred for `Exact` maps.

Exact image matches are handled before all other mapping rules.

### Replace Image Mapping

Image paths can be completely rewritten by using the `[REPLACE]` prefix. 

Usage:

```
[REPLACE]<pattern>::<replacement>
```

When a `<source-image>` matches against a `Replace` rule, the image will be transformed to `<replacement><image>` where `<image>` includes the tag if it was specified as a part of `<source-image>`.

Replacement rules are handled after exact match rules, but before the rest.

Module used: [fnmatch](https://docs.python.org/3/library/fnmatch.html) — Unix filename pattern matching
 
### Example MAPS Configs

- Disable image swapping for all registries EXCEPT `gcr.io`

  ```
  default:
  gcr.io::harbor.internal.example.com
  ```

- Enable image swapping for all registries except `gcr.io`

  ```
  default::harbor.internal.example.com
  gcr.io::
  ```

- Imitate LEGACY functionality as close as possible

  ```
  default::harbor.internal.example.com
  noswap_wildcards::harbor.internal.example.com
  ```

  With this, all images will be swapped except those that already match the `harbor.internal.example.com` pattern

- Enable swapping for all registries except those that match the `example.com` pattern

  ```
  default::harbor.internal.example.com
  noswap_wildcards::example.com
  ```

  With this, images that have any part of the registry that matches `example.com` will skip the swap logic

  EXAMPLE:
    - `example.com/image:latest`
    - `external.example.com/image:v1.0`
    - `edge.example.com/image:latest`)

- Enable swapping for all registries, but skip those that match the `example.com` pattern, except for `external.example.com`

  ```
  default:harbor.internal.example.com
  external.example.com:harbor.internal.example.com
  noswap_wildcards:example.com
  ```

  With this, the `edge.example.com/image:latest` image would skip swapping, but `external.example.com/image:latest` would be swapped to `harbor.internal.example.com/image:latest`

- Enable different swapping for top level "library" images vs. images that are nested under a project/org

  Example library image: `nginx:latest`

  This format is a shortcut for `docker.io/library/nginx:latest`

  [Official Docker documentation on image naming](https://docs.docker.com/registry/introduction/#understanding-image-naming)

  ```
  default::
  docker.io::
  docker.io/library::harbor.example.com/library
  ```

  This map uses a special syntax of adding `/library` to a registry for the key in map file.

  With this, the `nginx:latest` image would be swapped to `harbor.example.com/library/nginx:latest`, but the `tmobile/magtape:latest` image would be swapped to `harbor.example.com/tmobile/magtape:latest`

  This configuration can be useful for scenarios like [Harbor's](https://goharbor.io) [image proxy cache](https://goharbor.io/docs/2.1.0/administration/configure-proxy-cache/) feature].

## LEGACY Mode

**DEPRECATED: This mode will be removed in a future release**

Change the `IMAGE_PREFIX` environment variable definition in the [imageswap-env-cm.yaml](./deploy/manifests/imageswap-env-cm.yaml) manifest to customize the repo/registry for the image prefix mutation.

## Granularly Disable Image Swapping for a Workload

You can also customize the label used to granularly disable ImageSwap on a per workload basis. By default the `k8s.twr.io/imageswap` label is used, but you can override that by specifying a custom label with the `IMAGESWAP_DISABLE_LABEL` environment variable.

The value of the label should be `disabled`.

See the [Break Glass: Per Workload](#per-workload) section for more details.

