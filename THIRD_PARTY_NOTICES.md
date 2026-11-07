# Third-party notices

The repository's MIT license covers its original launcher, relay, gateway,
audit utilities, configuration and documentation. Upstream software retains
its own copyright and license terms. The project is not affiliated with or
endorsed by the upstream organizations.

| Component | Pinned version | License / source |
| --- | --- | --- |
| Stripe Smokescreen | `v0.1.0` | MIT; [source](https://github.com/stripe/smokescreen/tree/v0.1.0), [license copy](docs/licenses/smokescreen-LICENSE.txt) |
| Pi coding agent (`@earendil-works/pi-coding-agent`) | `1.5.0` | MIT according to the installed package metadata; [source](https://github.com/earendil-works/pi/tree/main/packages/coding-agent) |
| Node.js / Debian base image | `node:24-bookworm-slim`, digest in `Dockerfile` | Node.js and bundled components have their own notices; [Node license](https://github.com/nodejs/node/blob/main/LICENSE), [Docker image source](https://github.com/nodejs/docker-node) |
| Go / Alpine build image | `golang:1.25-alpine`, digest in `Dockerfile.egress` | Go BSD-style license plus bundled components; [Go license](https://go.dev/LICENSE), [Docker image source](https://github.com/docker-library/golang) |

Smokescreen is downloaded as a versioned Go module and compiled inside the
build image. Pi is installed from its published npm package. Their transitive
dependencies retain their upstream licenses; the entries above are not a full
software bill of materials. Debian/Alpine packages installed in the images
also have their own license terms and notices.

OpenRouter is an external API service, and DeepSeek is accessed through that
service. No DeepSeek model weights are distributed by this repository. API
usage is governed by the services' terms and your account settings.

When redistributing built images, retain the applicable upstream notices and
review the licenses of the included packages and dependencies. The Go build
stage is not part of the final runtime image.
