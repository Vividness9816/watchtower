# Manuals


This section contains user guides on how to install, set up, configure, and use
Docker products.

## AI and agents

All the Docker AI tools in one easy-to-access location.



## Application development

End-to-end developer solutions for innovative teams.



## Supply chain security

Security guardrails and image analysis for your software supply chain.



## Platform

Documentation related to the Docker platform, such as administration and
subscription management.



## Enterprise

Targeted at IT administrators with help on deploying Docker Desktop at scale with configuration guidance on security related features.

# Docker Sandboxes


Docker Sandboxes run AI coding agents in isolated microVM sandboxes. Each
sandbox gets its own Docker daemon, filesystem, and network — the agent can
build containers, install packages, and modify files without touching your host
system.

> [!NOTE]
> The `sbx` CLI is free to use, including for commercial work. Only
> [organization governance](/ai/sandboxes/governance) requires a separate paid subscription.

Organization admins can
[centrally manage sandbox network and filesystem policies](/ai/sandboxes/governance/org/)
from the Docker Admin Console, so the same rules apply uniformly across every
developer's machine. Available on a separate paid subscription.

## Get started

For complete system requirements, see the
[get started prerequisites](/ai/sandboxes/get-started/#prerequisites).

Install the `sbx` CLI and sign in:

**macOS**



```console
$ brew install docker/tap/sbx
$ sbx login
```

**Windows**



```powershell
> winget install -h Docker.sbx
> sbx login
```

**Linux (Ubuntu)**



```console
$ curl -fsSL https://get.docker.com | sudo REPO_ONLY=1 sh
$ sudo apt-get install docker-sbx
$ sudo usermod -aG kvm $USER
$ newgrp kvm
$ sbx login
```



Then launch an agent in a sandbox:

```console
$ cd ~/my-project
$ sbx run claude
```

See the [get started guide](/ai/sandboxes/get-started/) for a full walkthrough, or jump to
the [usage guide](/ai/sandboxes/usage/) for common patterns.

## Learn more

- [Agents](/ai/sandboxes/agents) — supported agents and per-agent configuration
- [Customize](/ai/sandboxes/customize) — reusable templates and declarative kits for
  extending or tailoring sandboxes
- [Architecture](/ai/sandboxes/architecture/) — microVM isolation, workspace mounting,
  networking
- [Security](/ai/sandboxes/security) — isolation model, credential handling, and
  network policies
- [CLI reference](/reference/cli/sbx/) — full list of `sbx` commands and options
- [Troubleshooting](/ai/sandboxes/troubleshooting/) — common issues and fixes
- [FAQ](/ai/sandboxes/faq/) — login requirements, telemetry, etc

## Feedback

Your feedback shapes what gets built next. If you run into a bug, hit a
missing feature, or have a suggestion, open an issue at
[github.com/docker/sbx-releases/issues](https://github.com/docker/sbx-releases/issues).

# Docker MCP Catalog and Toolkit




[Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) is
an open protocol that standardizes how AI applications access external tools
and data sources. By connecting LLMs to local development tools, databases,
APIs, and other resources, MCP extends their capabilities beyond their base
training.

The challenge is that running MCP servers locally creates operational friction.
Each server requires separate installation and configuration for every
application you use. You run untrusted code directly on your machine, manage
updates manually, and troubleshoot dependency conflicts yourself. Configure a
GitHub server for Claude, then configure it again for Cursor, and so on. Each
time you manage credentials, permissions, and environment setup.

## Docker MCP features

The [MCP Toolkit](/ai/mcp-catalog-and-toolkit/toolkit/) and [MCP
Gateway](/ai/mcp-catalog-and-toolkit/mcp-gateway/) solve these challenges
through centralized management. Instead of configuring each server for every AI
application separately, you set things up once and connect all your clients to
it. The workflow centers on three concepts: catalogs, profiles, and clients.

![MCP overview](/ai/images/mcp_toolkit.avif)

[Catalogs](/ai/mcp-catalog-and-toolkit/catalog/) are curated collections of
MCP servers. The Docker MCP Catalog provides 300+ verified servers packaged as
container images with versioning, provenance, and security updates. Organizations
can create [custom
catalogs](/ai/mcp-catalog-and-toolkit/catalog/#custom-catalogs) with approved
servers for their teams.

[Profiles](/ai/mcp-catalog-and-toolkit/profiles/) organize servers into named
collections for different projects. Your "web-dev" profile might use GitHub and
Playwright; your "backend" profile, database tools. Profiles support both
containerized servers from catalogs and remote MCP servers. Configure a profile
once, then share it across clients or with your team.

Clients are the AI applications that connect to your profiles. Claude Code,
Cursor, Zed, and others connect through the MCP Gateway, which routes requests
to the right server and handles authentication and lifecycle management.

> [!NOTE]
> MCP Gateway as part of Docker AI Governance is an invite-only feature. [Contact Docker Sales](https://www.docker.com/pricing/contact-sales/) to learn more.

## Learn more


# Docker Model Runner




Docker Model Runner (DMR) makes it easy to manage, run, and
deploy AI models using Docker. Designed for developers,
Docker Model Runner streamlines the process of pulling, running, and serving
large language models (LLMs) and other AI models directly from Docker Hub,
any OCI-compliant registry, or [Hugging Face](https://huggingface.co/).

With seamless integration into Docker Desktop and Docker
Engine, you can serve models via OpenAI and Ollama-compatible APIs, package GGUF files as
OCI Artifacts, and interact with models from both the command line and graphical
interface.

Whether you're building generative AI applications, experimenting with machine
learning workflows, or integrating AI into your software development lifecycle,
Docker Model Runner provides a consistent, secure, and efficient way to work
with AI models locally.

## Key features

- [Pull and push models to and from Docker Hub or any OCI-compliant registry](https://hub.docker.com/u/ai)
- [Pull models from Hugging Face](https://huggingface.co/)
- Serve models on [OpenAI and Ollama-compatible APIs](/ai/model-runner/api-reference/) for easy integration with existing apps
- Support for [llama.cpp, vLLM, and Diffusers inference engines](/ai/model-runner/inference-engines/) (vLLM and Diffusers on Linux with NVIDIA GPUs)
- [Generate images from text prompts](/ai/model-runner/inference-engines/#diffusers) using Stable Diffusion models with the Diffusers backend
- Package GGUF and Safetensors files as OCI Artifacts and publish them to any Container Registry
- Run and interact with AI models directly from the command line or from the Docker Desktop GUI
- [Connect to AI coding tools](/ai/model-runner/ide-integrations/) like Cline, Continue, Cursor, and Aider
- [Configure context size and model parameters](/ai/model-runner/configuration/) to tune performance
- [Set up Open WebUI](/ai/model-runner/openwebui-integration/) for a ChatGPT-like web interface
- Manage local models and display logs
- Display prompt and response details
- Conversational context support for multi-turn interactions

## Requirements

Docker Model Runner is supported on the following platforms:

**Windows**



Windows(amd64):
-  NVIDIA GPUs
-  NVIDIA drivers 576.57+

Windows(arm64):
- OpenCL for Adreno
- Qualcomm Adreno GPU (6xx series and later)

  > [!NOTE]
  > Some llama.cpp features might not be fully supported on the 6xx series.

**MacOS**



- Apple Silicon

**Linux**



Docker Engine only:

- Supports CPU, NVIDIA (CUDA), AMD (ROCm), and Vulkan backends
- Requires NVIDIA driver 575.57.08+ when using NVIDIA GPUs



## How Docker Model Runner works

Models are pulled from Docker Hub, an OCI-compliant registry, or
[Hugging Face](https://huggingface.co/) the first time you use them and are
stored locally. They load into memory only at runtime when a request is made,
and unload when not in use to optimize resources. Because models can be large,
the initial pull may take some time. After that, they're cached locally for
faster access. You can interact with the model using
[OpenAI and Ollama-compatible APIs](/ai/model-runner/api-reference/).

### Inference engines

Docker Model Runner supports three inference engines:

| Engine | Best for | Model format |
|--------|----------|--------------|
| [llama.cpp](/ai/model-runner/inference-engines/#llamacpp) | Local development, resource efficiency | GGUF (quantized) |
| [vLLM](/ai/model-runner/inference-engines/#vllm) | Production, high throughput | Safetensors |
| [Diffusers](/ai/model-runner/inference-engines/#diffusers) | Image generation (Stable Diffusion) | Safetensors |

llama.cpp is the default engine and works on all platforms. vLLM requires NVIDIA GPUs and is supported on Linux x86_64 and Windows with WSL2. Diffusers enables image generation and requires NVIDIA GPUs on Linux (x86_64 or ARM64). See [Inference engines](/ai/model-runner/inference-engines/) for detailed comparison and setup.

### Context size

Models have a configurable context size (context length) that determines how many tokens they can process. The default varies by model but is typically 2,048-8,192 tokens. You can adjust this per-model:

```console
$ docker model configure --context-size 8192 ai/qwen2.5-coder
```

See [Configuration options](/ai/model-runner/configuration/) for details on context size and other parameters.

> [!TIP]
>
> Using Testcontainers or Docker Compose?
> [Testcontainers for Java](https://java.testcontainers.org/modules/docker_model_runner/)
> and [Go](https://golang.testcontainers.org/modules/dockermodelrunner/), and
> [Docker Compose](/ai/compose/models-and-compose/) support Docker
> Model Runner.

## Known issues

### `docker model` is not recognised

If you run a Docker Model Runner command and see:

```text
docker: 'model' is not a docker command
```

It means Docker can't find the plugin because it's not in the expected CLI plugins directory.

To fix this, create a symlink so Docker can detect it:

```console
$ ln -s /Applications/Docker.app/Contents/Resources/cli-plugins/docker-model ~/.docker/cli-plugins/docker-model
```

Once linked, rerun the command.

## Privacy and data collection

Docker Model Runner respects your privacy settings in Docker Desktop. Data collection is controlled by the **Send usage statistics** setting:

- **Disabled**: No usage data is collected
- **Enabled**: Only minimal, non-personal data is collected:
  - [Model names](https://github.com/docker/model-runner/blob/eb76b5defb1a598396f99001a500a30bbbb48f01/pkg/metrics/metrics.go#L96) (via HEAD requests to Docker Hub)
  - User agent information
  - Whether requests originate from the host or containers

When using Docker Model Runner with Docker Engine, HEAD requests to Docker Hub are made to track model names, regardless of any settings.

No prompt content, responses, or personally identifiable information is ever collected.

## Share feedback

Thanks for trying out Docker Model Runner. To report bugs or request features, [open an issue on GitHub](https://github.com/docker/model-runner/issues). You can also give feedback through the **Give feedback** link next to the **Enable Docker Model Runner** setting.

## Next steps

- [Get started with DMR](/ai/model-runner/get-started/) - Enable DMR and run your first model
- [API reference](/ai/model-runner/api-reference/) - OpenAI and Ollama-compatible API documentation
- [Configuration options](/ai/model-runner/configuration/) - Context size and runtime parameters
- [Inference engines](/ai/model-runner/inference-engines/) - llama.cpp, vLLM, and Diffusers details
- [IDE integrations](/ai/model-runner/ide-integrations/) - Connect Cline, Continue, Cursor, and more
- [Open WebUI integration](/ai/model-runner/openwebui-integration/) - Set up a web chat interface

# Docker Agent


[Docker Agent](https://github.com/docker/docker-agent) is an open-source framework
for building teams of specialized AI agents. Instead of prompting one
generalist model, you define agents with specific roles and instructions that
collaborate to solve problems. Run these agent teams from your terminal using
any LLM provider.

> [!NOTE]
> Docker Agent is a framework for building and running custom agent teams.
> For Docker's built-in AI assistant, see [Gordon](/ai/gordon/) (`docker ai`).

## Why agent teams

One agent handling complex work means constant context-switching. Split the work
across focused agents instead - each handles what it's best at. Docker Agent manages
the coordination.

Here's a two-agent team that debugs problems:

```yaml
agents:
  root:
    model: openai/gpt-5-mini # Change to the model that you want to use
    description: Bug investigator
    instruction: |
      Analyze error messages, stack traces, and code to find bug root causes.
      Explain what's wrong and why it's happening.
      Delegate fix implementation to the fixer agent.
    sub_agents: [fixer]
    toolsets:
      - type: filesystem
      - type: mcp
        ref: docker:duckduckgo

  fixer:
    model: anthropic/claude-sonnet-4-5 # Change to the model that you want to use
    description: Fix implementer
    instruction: |
      Write fixes for bugs diagnosed by the investigator.
      Make minimal, targeted changes and add tests to prevent regression.
    toolsets:
      - type: filesystem
      - type: shell
```

The root agent investigates and explains the problem. When it understands the
issue, it hands off to `fixer` for implementation. Each agent stays focused on
its specialty.

## Installation

Docker Agent is included in Docker Desktop 4.63 and later. In Docker Desktop versions 4.49 through 4.62, this feature was called cagent.

For Docker Engine users or custom installations:

- **Homebrew**: `brew install docker-agent`
- **Winget**: `winget install Docker.Agent`
- **Pre-built binaries**: [GitHub
  releases](https://github.com/docker/docker-agent/releases)
- **From source**: See the [Docker Agent
  repository](https://github.com/docker/docker-agent?tab=readme-ov-file#build-from-source)

The `docker-agent` binary should be copied to `~/.docker/cli-plugins` and then can be used with the `docker agent` command. Alternatively, it can be used as a standalone binary.

## Get started

Try the bug analyzer team:

1. Set your API key for the model provider you want to use:

   ```console
   $ export ANTHROPIC_API_KEY=<your_key>  # For Claude models
   $ export OPENAI_API_KEY=<your_key>     # For OpenAI models
   $ export GOOGLE_API_KEY=<your_key>     # For Gemini models
   ```

2. Save the [example configuration](#why-agent-teams) as `debugger.yaml`.

3. Run your agent team:

   ```console
   $ docker agent run debugger.yaml
   ```

You'll see a prompt where you can describe bugs or paste error messages. The
investigator analyzes the problem, then hands off to the fixer for
implementation.

## How it works

You interact with the _root agent_, which can delegate work to sub-agents you
define. Each agent:

- Uses its own model and parameters
- Has its own context (agents don't share knowledge)
- Can access built-in tools like todo lists, memory, and task delegation
- Can use external tools via [MCP
  servers](/ai/mcp-catalog-and-toolkit/mcp-gateway/)

The root agent delegates tasks to agents listed under `sub_agents`. Sub-agents
can have their own sub-agents for deeper hierarchies.

## Configuration options

Agent configurations are YAML files. A basic structure looks like this:

```yaml
agents:
  root:
    model: claude-sonnet-4-0
    description: Brief role summary
    instruction: |
      Detailed instructions for this agent...
    sub_agents: [helper]

  helper:
    model: gpt-5-mini
    description: Specialist agent role
    instruction: |
      Instructions for the helper agent...
```

You can also configure model settings (like context limits), tools (including
MCP servers), and more. See the [configuration
reference](/ai/reference/config/)
for complete details.

## Share agent teams

Agent configurations are packaged as OCI artifacts. Push and pull them like
container images:

```console
$ docker agent share push ./debugger.yaml myusername/debugger
$ docker agent share pull myusername/debugger
```

Use Docker Hub or any OCI-compatible registry. Pushing creates the repository if
it doesn't exist yet.

## What's next

- Follow the [tutorial](/ai/tutorial/) to build your first coding agent
- Learn [best practices](/ai/best-practices/) for building effective agents
- Integrate Docker Agent with your [editor](/ai/integrations/acp/) or use agents as
  [tools in MCP clients](/ai/integrations/mcp/)
- Browse example agent configurations in the [Docker Agent
  repository](https://github.com/docker/docker-agent/tree/main/examples)
- Use `docker agent new` to generate agent teams with AI <!-- TODO: link to some page
  where we explain this, probably a CLI reference? -->
- Connect agents to external tools via the [Docker MCP
  Gateway](/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- Read the full [configuration
  reference](https://github.com/docker/docker-agent?tab=readme-ov-file#-configuration-reference)
  <!-- TODO: move to this site/repo -->

# Docker Desktop


Docker Desktop is a one-click-install application for your Mac, Linux, or Windows environment
that lets you build, share, and run containerized applications and microservices. 

It provides a straightforward GUI (Graphical User Interface) that lets you manage your containers, applications, and images directly from your machine. 

Docker Desktop reduces the time spent on complex setups so you can focus on writing code. It takes care of port mappings, file system concerns, and other default settings, and is regularly updated with bug fixes and security updates.

Docker Desktop integrates with your preferred development tools and languages, and gives you access to a vast ecosystem of trusted images and templates via Docker Hub. This empowers teams to accelerate development, automate builds, enable CI/CD workflows, and collaborate securely through shared repositories.

## Key features

* Ability to containerize and share any application on any cloud platform, in multiple languages and frameworks.
* Quick installation and setup of a complete Docker development environment.
* Includes the latest version of Kubernetes.
* On Windows, the ability to toggle between Linux and Windows containers to build applications.
* Fast and reliable performance with native Windows Hyper-V virtualization.
* Ability to work natively on Linux through WSL 2 on Windows machines.
* Volume mounting for code and data, including file change notifications and easy access to running containers on the localhost network.

## Products inside Docker Desktop

- [Docker MCP Toolkit and Catalog](/ai/mcp-catalog-and-toolkit/)
- [Docker Model Runner](/ai/model-runner/)
- [Gordon](/ai/gordon/)
- [Docker Offload](/offload/)
- [Docker Engine](/engine/)
- Docker CLI client
- [Docker Build](/build/)
- [Docker Compose](/compose/)
- [Docker Scout](/../scout/)
- [Kubernetes](https://github.com/kubernetes/kubernetes/)

## Next steps

# Docker Offload




Docker Offload is a fully managed service that lets you offload building and
running containers to the cloud using the Docker tools you already know. It
enables developers to work efficiently in virtual desktop infrastructure (VDI)
environments or systems that don't support nested virtualization.

In the following topics, learn about Docker Offload, how to set it up, use it
for your workflows, and troubleshoot common issues.

# Docker Build Cloud




Docker Build Cloud is a service that lets you build your container images
faster, both locally and in CI. Builds run on cloud infrastructure optimally
dimensioned for your workloads, no configuration required. The service uses a
remote build cache, ensuring fast builds anywhere and for all team members.

## How Docker Build Cloud works

Using Docker Build Cloud is no different from running a regular build. You invoke a
build the same way you normally would, using `docker buildx build`. The
difference is in where and how that build gets executed.

By default when you invoke a build command, the build runs on a local instance
of BuildKit, bundled with the Docker daemon. With Docker Build Cloud, you send
the build request to a BuildKit instance running remotely, in the cloud.
All data is encrypted in transit.

The remote builder executes the build steps, and sends the resulting build
output to the destination that you specify. For example, back to your local
Docker Engine image store, or to an image registry.

Docker Build Cloud provides several benefits over local builds:

- Improved build speed
- Shared build cache
- Native multi-platform builds

And the best part: you don't need to worry about managing builders or
infrastructure. Just connect to your builders, and start building.
Each cloud builder provisioned to an organization is completely
isolated to a single Amazon EC2 instance, with a dedicated EBS volume for build
cache, and encryption in transit. That means there are no shared processes or
data between cloud builders.

> [!NOTE]
> Docker Build Cloud is only available in the US East region.

## Get Docker Build Cloud

To get started with Docker Build Cloud,
[create a Docker account](/accounts/create-account/). There are two options
to get access to Docker Build Cloud:

- Users with a free Personal account can opt-in to a 7-day free trial, with the option
to subscribe for access. To start your free trial, sign in to [Docker Build Cloud Dashboard](https://app.docker.com/build/) and follow the on-screen instructions.
- All users with a paid Docker subscription have access to Docker Build Cloud included
with their Docker suite of products. See [Docker subscriptions and features](https://www.docker.com/pricing?ref=Docs&refAction=DocsBuildCloud) for more information.

Once you've signed up and created a builder, continue by
[setting up the builder in your local environment](/setup/).

For information about roles and permissions related to Docker Build Cloud, see
[Roles and Permissions](/enterprise/security/roles-and-permissions/#docker-build-cloud-permissions).
# Testcontainers


Testcontainers is a set of open source libraries that provides easy and lightweight APIs for bootstrapping local development and test dependencies with real services wrapped in Docker containers.
Using Testcontainers, you can write tests that depend on the same services you use in production without mocks or in-memory services.



## Quickstart

### Supported languages

Testcontainers provide support for the most popular languages, and Docker sponsors the development of the following Testcontainers implementations:

- [Go](https://golang.testcontainers.org/quickstart/)
- [Java](https://java.testcontainers.org/quickstart/junit_5_quickstart/)

The rest are community-driven and maintained by independent contributors.

### Prerequisites

Testcontainers requires a Docker-API compatible container runtime.
During development, Testcontainers is actively tested against recent versions of Docker on Linux, as well as against Docker Desktop on Mac and Windows.
These Docker environments are automatically detected and used by Testcontainers without any additional configuration being necessary.

It is possible to configure Testcontainers to work for other Docker setups, such as a remote Docker host or Docker alternatives.
However, these are not actively tested in the main development workflow, so not all Testcontainers features might be available
and additional manual configuration might be necessary.

If you have further questions about configuration details for your setup or whether it supports running Testcontainers-based tests,
contact the Testcontainers team and other users from the Testcontainers community on [Slack](https://slack.testcontainers.org/).



## Guides

Explore hands-on Testcontainers guides to learn how to use Testcontainers
with different languages and popular frameworks:

- [Getting started with Testcontainers for .NET](/guides/testcontainers-dotnet-getting-started/)
- [Getting started with Testcontainers for Go](/guides/testcontainers-go-getting-started/)
- [Getting started with Testcontainers for Java](/guides/testcontainers-java-getting-started/)
- [Getting started with Testcontainers for Node.js](/guides/testcontainers-nodejs-getting-started/)
- [Getting started with Testcontainers for Python](/guides/testcontainers-python-getting-started/)
- [Testing a Spring Boot REST API with Testcontainers](/guides/testcontainers-java-spring-boot-rest-api/)
- [Testcontainers container lifecycle management](/guides/testcontainers-java-lifecycle/)
- [Replace H2 with a real database for testing](/guides/testcontainers-java-replace-h2/)
- [Configuration of services running in a container](/guides/testcontainers-java-service-configuration/)
- [Testing an ASP.NET Core web app](/guides/testcontainers-dotnet-aspnet-core/)
- [Testing Spring Boot Kafka Listener](/guides/testcontainers-java-spring-boot-kafka/)
- [Testing REST API integrations using MockServer](/guides/testcontainers-java-mockserver/)
- [Testing AWS service integrations using LocalStack](/guides/testcontainers-java-aws-localstack/)
- [Testing Quarkus applications with Testcontainers](/guides/testcontainers-java-quarkus/)
- [Working with jOOQ and Flyway using Testcontainers](/guides/testcontainers-java-jooq-flyway/)
- [Testing REST API integrations using WireMock](/guides/testcontainers-java-wiremock/)
- [Securing Spring Boot with Keycloak and Testcontainers](/guides/testcontainers-java-keycloak-spring-boot/)
- [Testing Micronaut REST API with WireMock](/guides/testcontainers-java-micronaut-wiremock/)
- [Testing Micronaut Kafka Listener](/guides/testcontainers-java-micronaut-kafka/)

# Docker Build


Docker Build is one of Docker Engine's most used features. Whenever you are
creating an image you are using Docker Build. Build is a key part of your
software development life cycle allowing you to package and bundle your code and
ship it anywhere.

Docker Build is more than a command for building images, and it's not only about
packaging your code. It's a whole ecosystem of tools and features that support
not only common workflow tasks but also provides support for more complex and
advanced scenarios.

# Docker Engine


Docker Engine is an open source containerization technology for building and
containerizing your applications. Docker Engine acts as a client-server
application with:

- A server with a long-running daemon process
  [`dockerd`](/reference/cli/dockerd).
- APIs which specify interfaces that programs can use to talk to and instruct
  the Docker daemon.
- A command line interface (CLI) client
  [`docker`](/reference/cli/docker/).

The CLI uses [Docker APIs](/reference/api/engine/) to control or interact with the Docker
daemon through scripting or direct CLI commands. Many other Docker applications
use the underlying API and CLI. The daemon creates and manages Docker objects,
such as images, containers, networks, and volumes.

For more details, see
[Docker Architecture](/get-started/docker-overview/#docker-architecture).



## Licensing

Commercial use of Docker Engine obtained via Docker Desktop
within larger enterprises (exceeding 250 employees OR with annual revenue surpassing
$10 million USD), requires a [paid subscription](https://www.docker.com/pricing?ref=Docs&refAction=DocsEngine).
Apache License, Version 2.0. See [LICENSE](https://github.com/moby/moby/blob/master/LICENSE) for the full license.

# Docker Compose


Docker Compose is a tool for defining and running multi-container applications. 
It is the key to unlocking a streamlined and efficient development and deployment experience. 

Compose simplifies the control of your entire application stack, making it easy to manage services, networks, and volumes in a single YAML configuration file. Then, with a single command, you create and start all the services
from your configuration file.

Compose works in all environments - production, staging, development, testing, as
well as CI workflows. It also has commands for managing the whole lifecycle of your application:

 - Start, stop, and rebuild services
 - View the status of running services
 - Stream the log output of running services
 - Run a one-off command on a service

# Docker Hub


Docker Hub simplifies development with the world's largest container registry
for storing, managing, and sharing Docker images. By integrating seamlessly with
your tools, it enhances productivity and ensures reliable deployment,
distribution, and access to containerized applications. It also provides
developers with pre-built images and assets to speed up development workflows.

Key features of Docker Hub:

* Unlimited public repositories
* Private repositories
* Webhooks to automate workflows
* GitHub and Bitbucket integrations
* Concurrent and automated builds
* Trusted content featuring high-quality, secure images

In addition to the graphical interface, you can interact with Docker Hub using
the [Docker Hub API](/../../reference/api/hub/latest/) or experimental [Docker
Hub CLI tool](https://github.com/docker/hub-tool#readme).

# Docker Hardened Images


Docker Hardened Images (DHI) provide minimal, secure, and production-ready
container images, Helm charts, and system packages maintained by Docker.
Designed to reduce vulnerabilities and simplify compliance, DHI integrates
easily into your existing Docker-based workflows with little to no retooling
required.

DHI is available in the following three subscriptions.

| Feature | Community | Select | Enterprise |
|---|---|---|---|
| Hardened, minimal images | ✅ | ✅ | ✅ |
| Near-zero CVEs | ✅ | ✅ | ✅ |
| Verifiable SBOMs & SLSA Build L3 provenance | ✅ | ✅ | ✅ |
| Full, unsuppressed CVE visibility | ✅ | ✅ | ✅ |
| Drop-in adoption, no workflow changes | ✅ | ✅ | ✅ |
| Full catalog of open source images under Apache 2.0 | ✅ | ✅ | ✅ |
| Built with Docker Hardened System Packages | ✅ | ✅ | ✅ |
| Upstream cadence for Docker-released patches | ✅ | ✅ | ✅ |
| FIPS/STIG variants | ❌ | ✅ | ✅ |
| Critical CVE fixes < 7 days with SLA-backed continuous patching | ❌ | ✅ | ✅ |
| Customizations | ❌ | ✅ Up to 5 | ✅ Unlimited |
| Access to Hardened System Packages repository | ❌ | ❌ | ✅ |
| Full catalog access available | ❌ | ❌ | ✅ |
| Extended Lifecycle Support add-on available | ❌ | ❌ | ✅ +5 years of hardened updates |

For pricing and more details, see the [Docker Hardened Images subscription
comparison](https://www.docker.com/products/hardened-images/#compare).

Explore the sections below to get started with Docker Hardened Images, integrate
them into your workflow, and learn what makes them secure and enterprise-ready.

# Docker Scout


Container images consist of layers and software packages, which are susceptible to vulnerabilities.
These vulnerabilities can compromise the security of containers and applications.

Docker Scout is a solution for proactively enhancing your software supply chain security.
By analyzing your images, Docker Scout compiles an inventory of components, also known as a Software Bill of Materials (SBOM).
The SBOM is matched against a continuously updated vulnerability database to pinpoint security weaknesses.

Docker Scout is a standalone service and platform that you can interact with
using Docker Hub, the Docker CLI, and the Docker Scout Dashboard.
Docker Scout also facilitates integrations with third-party systems, such as container registries and CI platforms.

# Administration


Administrators can manage companies and organizations using the
[Docker Admin Console](https://app.docker.com/admin). The Admin Console
provides centralized observability, access management, and security controls
across Docker environments.

## Company and organization hierarchy

The [Docker Admin Console](https://app.docker.com/admin) provides administrators with centralized observability, access management, and controls for their company and organizations. To provide these features, Docker uses the following hierarchy and roles.

![Diagram showing Docker’s administration hierarchy with Company at the top, followed by Organizations, Teams, and Members](/images/docker-admin-structure.webp)

### Company

A company groups multiple Docker organizations for centralized configuration. Companies have the company owner administrator role available.

The company owner:

- Can view and manage all organizations within the company
- Has full access to company-wide settings and inherits the same permissions as organization owners
- Does not occupy a seat

Companies are only available for Docker Business subscribers.

### Organization

Organization owners have the organization owner administrator role available. They can manage organization settings, users, and access controls, but occupy a [seat](/admin/organization/organization-faqs/#what-is-the-difference-between-user-invitee-seat-and-member).

- An organization contains teams and repositories.
- All Docker Team and Business subscribers must have at least one organization.

> [!TIP]
> [Upgrading to a Docker Business plan](https://www.docker.com/pricing?ref=Docs&refAction=DocsAdmin) grants you the company owner role so you can manage multiple organizations.

### Team

Teams are optional and let you group members to assign repository permissions
collectively. Teams simplify permission management across projects
or functions.

### Member

A member is any Docker user added to an organization. Organization and company
owners can assign roles to members to define their level of access.

## Admin Console features

Docker's [Admin Console](https://app.docker.com/admin) allows you to:

- Create and manage companies and organizations
- Assign roles and permissions to members
- Group members into teams to manage access by project or role
- Set company-wide policies, including SCIM provisioning and security
  enforcement

## Manage companies and organizations

Learn how to manage companies and organizations in the following sections.

# Docker accounts


This section covers individual Docker accounts and Docker IDs. It does
not cover organizations, companies, or administrator roles.

A Docker account is required to:
- Create a Docker ID
- Access Docker products and services like Docker Hub and Docker Desktop
- Receive organization invitations
- Manage your personal settings and security features

# Security for developers


Docker helps you protect your local environments, infrastructure, and networks
with its developer-level security features.

Use tools like two-factor authentication (2FA), personal access tokens, and
Docker Scout to manage access and detect vulnerabilities early in your workflow.
You can also integrate secrets securely into your development stack using Docker Compose,
or enhance your software supply security with Docker Hardened Images.

Explore the following sections to learn more.

# Isolation layers


AI coding agents need to execute code, install packages, and run tools on
your behalf. Docker Sandboxes run each agent in its own microVM. Five
isolation layers protect your host: hypervisor, network, Docker Engine,
workspace, and credential proxy.

## Hypervisor isolation

Every sandbox runs inside a lightweight microVM with its own Linux kernel.
Unlike containers, which share the host kernel, a sandbox VM cannot access host
processes, files, or resources outside its defined boundaries.

- **Process isolation:** separate kernel per sandbox; processes inside the VM
  are invisible to your host and to other sandboxes
- **Filesystem isolation:** only your workspace directory is shared with the
  host. The rest of the VM filesystem persists across restarts but is removed
  when you delete the sandbox. Symlinks pointing outside the workspace scope
  are not followed.
- **Full cleanup:** when you remove a sandbox with `sbx rm`, the VM and
  everything inside it is deleted

The agent runs as a non-root user with sudo privileges inside the VM. The
hypervisor boundary is the isolation control, not in-VM privilege separation.

## Network isolation

Each sandbox has its own isolated network. Sandboxes cannot communicate with
each other and cannot reach your host's localhost. There is no shared network
between sandboxes or between a sandbox and your host.

All HTTP and HTTPS traffic leaving a sandbox passes through a proxy on your
host that enforces the [network policy](/ai/sandboxes/governance). The sandbox routes
traffic through either a forward proxy or a transparent proxy depending on the
client's configuration. Both enforce the network policy; only the forward proxy
[injects credentials](/ai/sandboxes/security/isolation/credentials/) for AI services.

Raw TCP connections, UDP, and ICMP are blocked at the network layer. DNS
resolution goes through the proxy and is subject to the same network policy —
domains that policy denies are refused at the resolver; loopback names such as
`localhost` are always resolved regardless of policy. Traffic to private IP
ranges, loopback, and link-local addresses is also blocked. Only domains
explicitly listed in the policy are reachable.

For the default set of allowed domains, see
[Default security posture](/ai/sandboxes/security/isolation/defaults/).

## Docker Engine isolation

Agents often need to build images, run containers, and use Docker Compose.
Mounting your host Docker socket into a container would give the agent full
access to your environment.

Docker Sandboxes avoid this by running a separate [Docker
Engine](/engine/) inside the sandbox environment, isolated from
your host. When the agent runs `docker build` or `docker compose up`, those
commands execute against that engine. The agent has no path to your host Docker
daemon.

Each sandbox VM runs its own Docker Engine. The agent runs inside the VM,
alongside that engine, and drives it to create containers, all within the
VM:

```mermaid
flowchart TB
  subgraph host["Host system"]
    subgraph hostd["Host Docker daemon"]
      hc["Your containers and images"]
    end
    subgraph vm["Sandbox (microVM)"]
      a["Agent"]
      subgraph e["Sandbox Docker engine"]
        c["Containers created by agent"]
      end
      a -->|"docker build / compose up"| e
    end
  end
  style host fill:#3b82f622,stroke:#3b82f6
```

## Workspace isolation

When you create a sandbox, you choose one of two ways to share your
workspace with it:

- **Direct mount** (the default): the agent has read-write access to
  your working tree. There is no boundary between the agent's edits and
  your host filesystem.
- **Clone mode** (`--clone`): your repository is mounted read-only into
  the VM and the agent works on a private clone inside the VM. The
  agent's edits never reach your host until you fetch them.

See [Git workflow](/ai/sandboxes/usage/#git-workflow) for the workflow side of
each.

### Direct mount (default)

By default, your workspace is shared into the VM as a read-write mount.
The agent and the host see the same files, and changes the agent makes
appear on your host as soon as they're written.

There is no isolation between the agent and your workspace in this mode.
The agent can create, modify, or delete any file in the workspace,
including:

- Source code and configuration files
- Build files (`Makefile`, `package.json`, `Cargo.toml`)
- Git hooks (`.git/hooks/`)
- CI configuration (`.github/workflows/`, `.gitlab-ci.yml`)
- IDE configuration (`.vscode/tasks.json`, `.idea/` run configurations)
- Hidden files, shell scripts, and executables

Some of these files execute code when you trigger normal development
actions — committing, pushing, building, or opening the project in an IDE.
Review them after any agent session before performing those actions:

- Git hooks (`.git/hooks/`) run on commit, push, and other Git actions.
  These are inside `.git/` and don't appear in `git diff` output —
  check them separately with `ls -la .git/hooks/`.
- CI configuration (`.github/workflows/`, `.gitlab-ci.yml`) runs on
  push.
- Build files (`Makefile`, `package.json` scripts, `Cargo.toml`) run
  during build or install steps.
- IDE configuration (`.vscode/tasks.json`, `.idea/`) can run tasks
  when you open the project.

> [!WARNING]
> Treat sandbox-modified workspace files the same way you would treat a pull
> request from an untrusted contributor: review before you trust them on
> your host.

### Clone mode

When you start a sandbox with [`--clone`](/ai/sandboxes/usage/#clone-mode), the agent
never works directly against your host repository. Even with full root
inside the VM, it cannot modify your `.git` directory, your working tree,
or any tracked file on your host.

```mermaid
flowchart LR
  subgraph host["Host repository (untouched)"]
    direction TB
    repo[".git/ + working tree"]
    remote["remote sandbox-&lt;name&gt;"]
  end
  subgraph vm["Sandbox VM"]
    direction TB
    mount["/run/sandbox/source<br/>(read-only bind mount)"]
    clone["private clone (RW)<br/>agent edits here"]
    daemon["git-daemon"]
  end
  repo -->|"read-only bind mount"| mount
  mount -->|"git clone"| clone
  clone --> daemon
  daemon -->|"git fetch"| remote
```

How the boundary is enforced:

- Your repository's Git root is mounted at `/run/sandbox/source` as
  read-only. Nothing the agent does inside the VM can write back through
  that mount.
- The agent works on a private clone that lives inside the sandbox. The
  clone has its own index, its own refs, and its own working tree. Writes
  to the clone never reach your host.
- The sandbox publishes the clone over a Git daemon bound to localhost on
  the host. The CLI wires it up as a `sandbox-<sandbox-name>` Git remote on
  your host repository. Fetching from that remote uses the same trust
  model as fetching from any third-party remote — nothing is integrated
  until you explicitly merge or check out the fetched refs.

The practical guarantees:

- The agent cannot modify any tracked file or any byte under `.git/` on
  your host. A compromised or buggy agent cannot drop a
  `.git/hooks/pre-commit`, alter `.github/workflows/`, or sneak changes
  into your working tree.
- Concurrent `git` commands on the host and inside the sandbox cannot
  race on a shared `.git/index` or shared refs — there is no shared
  writable state.
- Credentials, signing keys, and any settings in your repository's
  `.git/config` stay on the host. The agent's clone has its own
  independent configuration.

Use clone mode whenever you want a strong boundary between the agent's
Git activity and your host repository — for example when running an
unfamiliar agent, running multiple agents on the same repository at once,
or keeping your working tree clean while the agent works.

## Credential isolation

Most agents need API keys for their model provider. Rather than passing keys
into the sandbox, the host-side proxy intercepts outbound API requests and
injects authentication headers before forwarding each request.

Credential values are never stored inside the VM. They are not available as
environment variables or files inside the sandbox unless you explicitly set
them. This means a compromised sandbox cannot read API keys from the local
environment.

For how to store and manage credentials, see [Credentials](/ai/sandboxes/security/isolation/credentials/).

# Default security posture


A sandbox created with `sbx run` and no additional flags has the following
security posture.

## Network defaults

All outbound HTTP and HTTPS traffic is blocked unless an explicit rule allows
it (deny-by-default). All non-HTTP protocols (raw TCP, UDP including DNS, and
ICMP) are blocked at the network layer. Traffic to private IP ranges, loopback
addresses, and link-local addresses is also blocked.

Run `sbx policy ls` to see the active network rules for your installation.
Rules can be customized per machine with the `sbx policy` CLI, or managed
centrally across your organization from the Admin Console. Org-level rules
take precedence over local rules. See [Governance](/ai/sandboxes/governance).

## Workspace defaults

Sandboxes use a direct mount by default. The agent sees and modifies your
working tree directly, and changes appear on your host immediately.

The agent can read, write, and delete any file within the workspace directory,
including hidden files, configuration files, build scripts, and Git hooks.
See [Workspace isolation](/ai/sandboxes/security/defaults/isolation/#workspace-isolation) for what to
review after an agent session.

## Credential defaults

No credentials are available to the sandbox unless you provide them using
`sbx secret` or environment variables. When credentials are provided, the
host-side proxy injects them into outbound HTTP headers. The agent cannot
read the raw credential values.

See [Credentials](/ai/sandboxes/security/defaults/credentials/) for setup instructions.

## Agent capabilities inside the sandbox

The agent runs with full control inside the sandbox VM:

- `sudo` access (the agent runs as a non-root user with sudo privileges)
- A private Docker Engine for building images and running containers
- Package installation through `apt`, `pip`, `npm`, and other package managers
- Full read and write access to the VM filesystem

Everything the agent installs or creates inside the VM, including packages,
Docker images, and configuration changes, persists across stop and restart
cycles. When you remove the sandbox with `sbx rm`, the VM and its contents
are deleted. Only workspace files remain on the host.

## What is blocked by default

The following are blocked for all sandboxes and cannot be changed through
policy configuration:

- Host filesystem access outside the workspace directory
- Host Docker daemon
- Host network and localhost
- Communication between sandboxes
- Raw TCP, UDP, and ICMP connections
- Traffic to private IP ranges and link-local addresses

Outbound HTTP/HTTPS to domains not in the allow list is also blocked by
default, but you can add allow rules with `sbx policy allow`.

# Credentials


Most agents need an API key for their model provider. An HTTP/HTTPS proxy on
your host intercepts outbound requests from the sandbox, looks up the matching
credential on the host, and overwrites the auth header before forwarding. The
real credential stays on the host; the sandbox sees only a sentinel value. For
the security model behind this, see
[Credential isolation](/ai/sandboxes/security/credentials/isolation/#credential-isolation).

## How credential injection works

When a sandbox makes an outbound request, the host-side proxy decides three
things: whether the request **matches** a service the kit (or built-in agent)
declares, what **header** to write, and what **value** to inject. The kit
declares the match and the header; you provide the value on the host. The real
value never enters the sandbox — the agent sees only a sentinel like
`proxy-managed`.

There are several ways to provide that value. When more than one source has a
value for the same service, the stored secret takes precedence over a host
environment variable.

| Form | What it is | Use it when |
| ---- | ---------- | ----------- |
| [Stored secrets](#stored-secrets) (`sbx secret set`) | A value in your OS keychain, keyed by service | The default for any built-in or kit-declared service |
| [Custom secrets](#custom-secrets) (`sbx secret set-custom`) | A value keyed to a domain and environment variable | The service model doesn't fit — the agent validates the variable's format, or the secret rides in a request body |
| [Environment variables](#environment-variables) | Read from your shell session | One-off testing or CI, where keychain storage isn't worth it |
| OAuth | A host-side sign-in flow; the token never enters the sandbox | The agent supports it, such as Claude Code, Codex, or Cursor |
| [Registry credentials](#registry-credentials) (`sbx secret set --registry`) | Authentication for pulling images and kits | Pulling templates or kits from a private registry |

For multi-provider agents (OpenCode, Docker Agent), the proxy selects
credentials based on the API endpoint being called. See individual
[agent pages](/ai/sandboxes/agents) for provider-specific details.

## Stored secrets

`sbx secret set` stores credentials in your OS keychain, keyed on a service
identifier. Built-in agents declare a fixed set of services. Custom kits can
declare their own. The same `sbx secret set` flow works for both.

### Where secrets are stored

The store backing `sbx secret set` depends on your operating system:

- macOS: the system Keychain.
- Windows: the Windows Credential Manager.
- Linux: the Secret Service exposed by your desktop keyring, such as GNOME
  Keyring or KDE Wallet.

The Ubuntu package depends on GNOME Keyring, so a standard desktop install
needs no extra setup.

On Linux hosts without a running Secret Service — headless servers and some
WSL setups — `sbx` falls back to an encrypted file under your user config
directory `$XDG_CONFIG_HOME/com.docker.sandboxes`, which defaults to
`~/.config/com.docker.sandboxes` when `$XDG_CONFIG_HOME` is unset. The fallback
is automatic and needs no configuration. When you store a secret this way,
`sbx` prints a notice:

```text
No keychain detected - this secret will be stored in an encrypted file on disk
```

The file is encrypted at rest and protected by `0700` directory permissions,
the same posture as `~/.docker/config.json`. This is weaker than an OS
keychain, which also mediates access per application. If you start a Secret
Service on the host later, `sbx` stores new secrets in the keychain again. For
more on running sandboxes without a desktop keyring, see
[Can I use Docker Sandboxes on headless Linux?](/ai/sandboxes/faq/#can-i-use-docker-sandboxes-on-headless-linux)

### Store a secret

```console
$ sbx secret set -g anthropic
```

This prompts you for the secret value interactively. The `-g` flag stores the
secret globally so it's available to all sandboxes. To scope a secret to a
specific sandbox instead:

```console
$ sbx secret set my-sandbox openai
```

> [!NOTE]
> A sandbox-scoped secret takes effect immediately, even if the sandbox is
> running. A global secret (`-g`) only applies when a sandbox is created. If
> you set or change a global secret while a sandbox is running, recreate the
> sandbox for the new value to take effect.

You can also pipe in a value for non-interactive use:

```console
$ echo "$ANTHROPIC_API_KEY" | sbx secret set -g anthropic
```

### Built-in services

Each built-in service name maps to a set of environment variables the proxy
checks and the API domains it authenticates requests to:

| Service     | Environment variables              | API domains                         |
| ----------- | ---------------------------------- | ----------------------------------- |
| `anthropic` | `ANTHROPIC_API_KEY`                | `api.anthropic.com`                 |
| `aws`       | `AWS_ACCESS_KEY_ID`                | AWS Bedrock endpoints               |
| `github`    | `GH_TOKEN`, `GITHUB_TOKEN`         | `api.github.com`, `github.com`      |
| `google`    | `GEMINI_API_KEY`, `GOOGLE_API_KEY` | `generativelanguage.googleapis.com` |
| `groq`      | `GROQ_API_KEY`                     | `api.groq.com`                      |
| `mistral`   | `MISTRAL_API_KEY`                  | `api.mistral.ai`                    |
| `nebius`    | `NEBIUS_API_KEY`                   | `api.studio.nebius.ai`              |
| `openai`    | `OPENAI_API_KEY`                   | `api.openai.com`                    |
| `xai`       | `XAI_API_KEY`                      | `api.x.ai`                          |

When you store a secret with `sbx secret set -g <service>`, the proxy uses it
the same way it would use the corresponding environment variable. You don't
need to set both.

### Services declared by kits

Custom kits can declare their own service identifiers in `spec.yaml` —
they're not limited to the table above. To provide a credential for a
kit-declared service, run `sbx secret set` with the same identifier the kit
declares under `credentials.sources`:

```console
$ sbx secret set -g my-service
```

There's no separate registration step; the keychain entry is keyed on the
identifier the kit already uses. See
[Authenticate to external services](/ai/sandboxes/customize/kits/#authenticate-to-external-services)
for the kit-side wiring.

### List and remove secrets

List all stored secrets:

```console
$ sbx secret ls
SCOPE      TYPE      NAME      SECRET
(global)   service   github    gho_GCaw4o****...****43qy
```

Remove a secret:

```console
$ sbx secret rm -g github
```

> [!NOTE]
> Running `sbx reset` deletes all stored secrets along with all sandbox state.
> You'll need to re-add your secrets after a reset.

### GitHub token

The `github` service gives the agent access to the `gh` CLI inside the
sandbox. Pass your existing GitHub CLI token:

```console
$ echo "$(gh auth token)" | sbx secret set -g github
```

This is useful for agents that create pull requests, open issues, or interact
with GitHub APIs on your behalf.

### SSH agent

If your host has an SSH agent and `SSH_AUTH_SOCK` is set, Docker Sandboxes
forwards the agent into the sandbox and sets `SSH_AUTH_SOCK` there. The
private keys stay on your host. Processes inside the sandbox can request
signatures from the forwarded agent, but they can't read or copy the private
key.

Use SSH agent forwarding for Git operations over SSH and SSH-based commit
signing. The signing key must be loaded in the host SSH agent for sandboxed
commit signing to work. Outbound SSH connections are still subject to sandbox
network policy. For details, see
[Commit signing](/ai/sandboxes/workflows/#commit-signing).

## Custom secrets

> [!IMPORTANT]
> Custom secrets are experimental. Behavior, flags, and the placeholder format may
> change without notice.

For credentials that don't fit the service-identifier model — for example,
when an agent validates the environment variable format at boot, or when the
credential lands in a request body rather than a header — use
`sbx secret set-custom`. The secret is keyed on one or more target domains, an
environment variable name, and an optional placeholder string, instead of a
service identifier.

```console
$ sbx secret set-custom -g \
    --host api.example.com \
    --env API_KEY \
    --value <secret>
```

Repeat `--host` to cover multiple domains with the same secret — useful when
an API is split across related hostnames or when two unrelated endpoints share
a credential:

```console
$ sbx secret set-custom -g \
    --host api.example.com \
    --host uploads.example.com \
    --env API_KEY \
    --value <secret>
```

A `--host` value can also use wildcards, with the same syntax as
[network rules](/ai/sandboxes/governance/concepts/#network-rules): `*` matches a
single label (`*.example.com` covers `api.example.com`) and `**` matches any
number (`**.example.com` covers `api.example.com` and `v2.api.example.com`).

> [!WARNING]
> Passing the secret as `--value <secret>` records it in your shell history
> and exposes it to other processes running as your user. Avoid pasting
> real credentials inline — read the value from a variable that's already
> in your environment, and clear shell history if a real secret was passed
> on the command line.

Inside the sandbox, `API_KEY` is set to a generated placeholder (for example,
`sbx-cs-<rand>`). When a sandboxed process sends a request to any of the
configured hosts and the placeholder appears anywhere in the request, the
proxy replaces it with the real value. The agent never sees the real secret.

Prefer the [service-based flow](#stored-secrets) whenever it's an option —
the kit handles the wiring; you only provide the value.

## Environment variables

As an alternative to stored secrets, export the relevant environment variable
in your shell before running a sandbox:

```console
$ export ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
$ sbx run claude
```

The proxy reads the variable from your terminal session. See individual
[agent pages](/ai/sandboxes/agents) for the variable names each agent expects.

> [!NOTE]
> These environment variables are set on your host, not inside the sandbox.
> Sandbox agents are pre-configured to use credentials managed by the
> host-side proxy. For custom environment variables not tied to a
> [built-in service](#built-in-services), see
> [Setting custom environment variables](/ai/sandboxes/faq/#how-do-i-set-custom-environment-variables-inside-a-sandbox).

## Registry credentials

Registry credentials authenticate to private OCI registries when pulling
[templates](/ai/sandboxes/customize/templates/) or [kits](/ai/sandboxes/customize/kits/), and can
also let the agent pull and push images from inside the sandbox. Use
`sbx secret set --registry <host>` to store them. For Docker Hub, `sbx` reuses
your `sbx login` session — no registry secret needed. For other registries
(GitHub Container Registry, ECR, ACR, self-hosted Nexus, and so on), store
credentials with `sbx secret set --registry`.

The scope you store a credential at controls where it's used — and whether its
value enters the sandbox. The scope comes from how you target `sbx secret set`:

```text
sbx secret set [-g | SANDBOX] --registry HOST
```

- **Host-only** (no `-g`, no `SANDBOX`): the `sbx` CLI uses it to pull templates
  and kits when creating a sandbox. The credential stays on the host and is
  never available inside the sandbox.
- **Global** (`-g`): same as host-only, plus written into
  `~/.docker/config.json` in every new sandbox so the agent can pull and push
  images. The value lives inside the VM, where the agent can read it, so it's
  less isolated than the proxy-injected service credentials above. Use it when
  agents build and publish container images.
- **Sandbox-scoped** (`SANDBOX`): same in-sandbox behavior as global, but only
  for the named sandbox. Use it when only one sandbox needs registry access.

> [!NOTE]
> Registry credentials are written into a sandbox at creation time. Recreate an
> existing sandbox to pick up credentials added after it was created.

### Store registry credentials

Pipe a token from stdin and target the registry hostname:

```console
$ gh auth token | sbx secret set --registry ghcr.io --password-stdin
```

For registries that require a username (for example, ACR with an admin
account), add `--username`:

```console
$ echo "$ACR_PASSWORD" | sbx secret set \
    --registry myregistry.azurecr.io \
    --username myuser \
    --password-stdin
```

Add `-g` to store the credential globally, before you create the sandbox:

```console
$ gh auth token | sbx secret set -g --registry ghcr.io --password-stdin
$ sbx run claude                      # created with the credential in place
```

To scope the credential to a single sandbox, store it under that sandbox's name
and create the sandbox with the same name:

```console
$ gh auth token | sbx secret set my-app --registry ghcr.io --password-stdin
$ sbx run claude --name my-app
```

`sbx kit pull` also uses these credentials, with the Docker credential
store as a fallback. `sbx kit push` uses only the Docker credential store —
push targets still require a prior `docker login`.

### Remove registry credentials

Remove both the host-only and global entries for a registry:

```console
$ sbx secret rm --registry ghcr.io -f
```

To remove only the global (in-sandbox) entry and leave the
host-only credential in place, pass `-g`:

```console
$ sbx secret rm -g --registry ghcr.io -f
```

To remove a sandbox-scoped credential, pass the sandbox name:

```console
$ sbx secret rm my-sandbox --registry ghcr.io -f
```

## Best practices

- Use [stored secrets](#stored-secrets) over environment variables. Stored
  secrets are encrypted at rest in the OS keychain (or an encrypted file on
  Linux hosts without a keychain), while environment variables are plaintext in
  your shell. See [Where secrets are stored](#where-secrets-are-stored).
- Don't set API keys manually inside the sandbox. Sandbox agents are
  pre-configured to use proxy-managed credentials.
- Registry credentials you make available inside a sandbox are stored in the VM
  (`~/.docker/config.json`), where the agent can read them — unlike
  proxy-injected service credentials, which never enter the sandbox. Reserve
  them for sandboxes that need registry access, and prefer sandbox scope over
  global (`-g`) to limit exposure.
- For Claude Code and Codex, OAuth is another secure option: the flow runs on
  the host, so the token is never exposed inside the sandbox. If you haven't
  stored a credential, both agents prompt you to authenticate before the
  sandbox launches — Codex prompts on the host from `sbx run codex`, and Claude
  Code prompts inside the agent. To authenticate ahead of time, run
  `sbx secret set -g openai --oauth` for Codex, or use `/login` inside Claude
  Code.
- If you store credentials in 1Password, see
  [Sourcing credentials from 1Password](/ai/sandboxes/workflows/#sourcing-credentials-from-1password)
  for how to use `op read` and `op run` with `sbx`.

## Custom templates and placeholder values

When building custom templates or installing agents manually in a shell
sandbox, some agents require environment variables like `OPENAI_API_KEY` to be
set before they start. Set these to placeholder values (e.g. `proxy-managed`)
if needed. The proxy injects actual credentials regardless of the environment
variable value.

# Audit logging


The sandbox daemon records a structured audit event for every policy decision
it makes. Each record captures who triggered the evaluation, when it happened,
which rule matched, and whether the resource was allowed or denied. Records are
written to disk as JSON Lines (`.jsonl`) so existing SIEM and log-shipping
tools can collect them. The records stay on the machine that produced them.
Docker doesn't collect or ingest audit data.

> [!NOTE]
> Audit logging is part of Docker AI Governance and requires a separate paid
> subscription.
> [Contact Docker Sales](https://www.docker.com/products/ai-governance/#contact-sales)
> to request access.

Audit logging is active only while your organization enforces a centralized
governance policy. The subscription alone doesn't produce records. If your
organization hasn't configured and enforced an [organization policy](/ai/sandboxes/governance/audit/org/),
the daemon writes no audit logs. To confirm governance is active, run `sbx
policy ls` — the output begins with a `Governance: managed by <org>` header
when an organization policy is in effect.

Audit logging complements [monitoring](/ai/sandboxes/governance/audit/monitoring/). Monitoring with `sbx
policy ls` and `sbx policy log` is for live, interactive debugging. Audit
logging produces a durable trail for security review and compliance.

## What gets recorded

The daemon writes two categories of record:

- Evaluation records capture each policy decision: the resource, the
  action, the verdict, and the reason for a denial.
- Session lifecycle records mark the start and end of each daemon run.
  Evaluation records share the run's `audit_session_id`, so you can correlate
  every decision back to a single daemon session.

A network evaluation record looks like this:

```json
{
  "audit_event_id": "95e7257f-93c9-4f29-bde7-88830e2dae80",
  "timestamp": "2026-05-28T19:15:00.728933Z",
  "schema_version": "1.82.0",
  "category": "AUDIT_CATEGORY_EVALUATION",
  "decision": "AUDIT_DECISION_DENY",
  "username": "jordandoe",
  "user_email": "jordandoe@example.com",
  "org_id": "9f8e7d6c-5b4a-3210-fedc-ba9876543210",
  "org_name": "Acme Inc",
  "audit_session_id": "8a3bc076-79d0-4502-baf3-cc6ad35fb578",
  "resource_id": "example.com:443",
  "os": "macos",
  "app_version": "v0.31.0",
  "client_name": "sbx",
  "hostname": "host-machine",
  "deny_reason": [
    "no applicable policies for op(action=net:connect:tcp, resource=net:domain:example.com:443)"
  ],
  "action_type": "network_egress",
  "network_egress": { "protocol": "tcp" },
  "agent": "claude"
}
```

Common fields include:

| Field              | Description                                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------------------ |
| `timestamp`        | UTC time of the decision.                                                                                    |
| `schema_version`   | Version of the record schema. Pin your SIEM field mappings to it, as the format is a stable contract.        |
| `category`         | `AUDIT_CATEGORY_EVALUATION` for policy decisions, `AUDIT_CATEGORY_MANAGEMENT` for session lifecycle records. |
| `audit_session_id` | Identifies the daemon run that produced the record.                                                          |
| `username`         | The signed-in Docker user's Docker Hub username.                                                             |
| `user_email`       | The signed-in Docker user's email address.                                                                   |
| `org_id`           | ID of the organization whose governance policy is in effect.                                                 |
| `org_name`         | Display name of the organization whose governance policy is in effect.                                       |
| `action_type`      | The kind of access evaluated, such as `network_egress`.                                                      |
| `resource_id`      | The target of the evaluation, such as a host and port.                                                       |
| `decision`         | `AUDIT_DECISION_ALLOW` or `AUDIT_DECISION_DENY`.                                                             |
| `deny_reason`      | Why a denied request was blocked. Present on deny decisions.                                                 |
| `agent`            | The AI agent driving the sandbox (for example, `claude`, `codex`). Omitted when the agent is unknown.       |

Each record is attributed to the signed-in Docker user and the organization
whose governance policy is in effect.

## Where records are stored

The daemon writes audit records, not the CLI. Running a command such as `sbx
create` sends a request to the daemon, and the daemon emits the resulting
record to its own audit directory.

The default location depends on your operating system:

| OS      | Default path                                                      |
| ------- | ----------------------------------------------------------------- |
| macOS   | `~/Library/Logs/com.docker.sandboxes/sandboxes/auditkit/`         |
| Linux   | `${XDG_STATE_HOME:-~/.local/state}/sandboxes/sandboxes/auditkit/` |
| Windows | `%LOCALAPPDATA%\DockerSandboxes\sandboxes\logs\auditkit\`         |

The directory layout differs by platform because each operating system places
application logs in its own conventional location.

Files are named `audit-<utc-timestamp>-<process-uuid>-<seq>.jsonl`.

The daemon writes in-progress records to a temporary `.tmp` file and seals it
into a final `.jsonl` file by atomic rename. Sealing happens at a rotation
threshold (by default 5 minutes, 1000 events, or 50 MiB, whichever comes
first) or when the daemon shuts down cleanly. Only sealed `.jsonl` files are
complete. Treat `.tmp` files as incomplete and don't collect them.

Sandboxes never delete sealed files. Retention and cleanup are the
responsibility of your log shipper or your own housekeeping.

## Collect records with a SIEM

Point your log shipper at the audit directory and configure it to collect
sealed `.jsonl` files only. Tools such as the Splunk Universal Forwarder,
Filebeat, and CrowdStrike Falcon LogScale read the directory and forward each
line as an event. Because in-progress records live in `.tmp` files until they
are sealed, collectors never see partial records.

# Organization policy


[Local policies](/ai/sandboxes/governance/org/local/) give individual developers control over what their
sandboxes can access. Organization policy moves that control to the admin level:
rules defined in **Admin Console** apply to sandboxes across the organization,
either to every member or to specific teams. When organization governance is active, it replaces local `sbx policy`
rules entirely — local rules are no longer evaluated and can't be used to
supplement or override the organization policy.

Admins can manage organization policies through the Admin Console UI or
programmatically using the [Governance API](/reference/api/ai-governance/).

By default, only organization
[owners](/enterprise/security/roles-and-permissions/core-roles/) can
view and manage AI Governance policies. To let someone other than an owner
manage policies, create a
[custom role](/enterprise/security/roles-and-permissions/custom-roles/)
with the **Governance** permissions and assign it to a user or team.

> [!NOTE]
> Sandbox organization governance is available on a separate paid
> subscription.
> [Contact Docker Sales](https://www.docker.com/products/ai-governance/#contact-sales)
> to request access.

## Create a policy

Manage policies under **Admin Console**, a section in the left-hand navigation
of [Docker Home](https://app.docker.com). Network and filesystem policies are
managed separately, under **Network access** and **Filesystem access**.

To create a policy:

1. Sign in to [Docker Home](https://app.docker.com) and select your
   organization.
1. Select **Admin Console**, then **AI governance**.
1. Select **Network access** or **Filesystem access**, then **Create policy**.
1. Enter a **Policy name**.
1. Set the **Scope** to **Organization** or **Teams**. If you select **Teams**,
   choose the teams the policy applies to. See
   [Scope policies to teams](#scope-policies-to-teams).
1. Select **Add rule** to add each rule. For rule syntax, see
   [Policy concepts](/ai/sandboxes/governance/org/concepts/#rule-syntax).

Existing policies are listed with their name, scope, rule count, and last
update. Use the action menu (⋮) to edit or delete a policy.

## Network policies

### Configuring org-level network rules

A network rule takes a network target and an action (allow or deny). You can
add multiple entries at once, one per line.

For the full syntax reference (exact hostnames, wildcard subdomains, port
suffixes, and CIDR ranges), see [Policy concepts](/ai/sandboxes/governance/org/concepts/#network-rules).

When organization governance is active, local network rules are not evaluated.
The organization policy is the only policy in effect. `sbx policy ls` hides
these inactive local rules by default. See
[Monitoring](/ai/sandboxes/governance/org/monitoring/#showing-inactive-rules) for how to list them and read
the rule view.

## Filesystem policies

Filesystem policies control which host paths a sandbox can mount as
workspaces. By default, sandboxes can mount any directory the user has
access to.

Admins can restrict which paths are mountable with filesystem allow and deny
rules. Each rule takes a path pattern and an action (allow or deny).

For path pattern syntax including the difference between `*` and `**`, see
[Policy concepts](/ai/sandboxes/governance/org/concepts/#filesystem-rules).

## Scope policies to teams

An organization can have more than one policy, and each policy applies either
to the whole organization or to specific teams. Scoping lets you apply different
rules to different parts of the organization.

A policy's [**Scope**](#create-a-policy) controls who it applies to. Set it to
**Organization** to apply the policy to every member, or to **Teams** to apply
it only to members of the teams you select.

### Before you start

Team scoping targets your organization's existing
[teams](/admin/organization/manage/manage-a-team/), so a team must
exist before you can scope a policy to it. Create teams and manage their members
in one of two ways:

- Manually, in the Admin Console.
- Automatically, by using
  [group mapping](/enterprise/security/provisioning/scim/group-mapping/)
  to synchronize your identity provider's groups with the teams in your
  organization. Group mapping creates teams that don't already exist and keeps
  their membership in step with your IdP groups.

Because policies apply by team, a user's policies update automatically as their
team membership changes, including changes synced from your IdP.

### How org-wide and team-scoped policies combine

A user is governed by all of their
[effective policies](/ai/sandboxes/governance/org/concepts/#policy-scope) at once — every org-wide policy,
plus the team-scoped policies for the teams they belong to. The rules combine
into a single evaluation in which deny always wins, so a team-scoped policy can
grant access on top of the org-wide policies but can't loosen a restriction they
impose. For the full evaluation model, see
[Rule evaluation](/ai/sandboxes/governance/org/concepts/#rule-evaluation).

This makes org-wide policies the natural home for guardrails that must hold
everywhere. For example, an org-wide policy can deny a category of domains for
all members, while a team-scoped policy grants a research team access to extra
package mirrors. Research-team members get the extra access, but the org-wide
deny still applies.

## Precedence

When organization governance is active, local rules are not evaluated. Only
organization rules set in the Admin Console determine what is allowed or denied,
and they can't be supplemented or overridden from a developer's machine. The
same applies to filesystem policies: organization rules replace local behavior
entirely. For how a user's organization policies are evaluated together, see
[Policy concepts](/ai/sandboxes/governance/org/concepts/#rule-evaluation).

To unblock a domain when organization governance is active, update the rule in
the Admin Console or via the [API](/reference/api/ai-governance/). Without
organization governance, remove the local rule with `sbx policy rm`.

## Troubleshooting

### Policy changes not taking effect

After updating organization policies in the Admin Console, changes take up
to 5 minutes to propagate to developer machines. To apply changes
immediately, users can run `sbx policy reset`, which stops the daemon and
forces it to pull the latest organization policies on the next `sbx`
command.

> [!WARNING]
> `sbx policy reset` deletes all locally configured policy rules. The command
> prompts for confirmation before proceeding.

### Sandbox cannot mount workspace

If a sandbox fails to mount with a `mount policy denied` error, verify that
the filesystem allow rule in the Admin Console uses `**` rather than `*`. A
single `*` doesn't match across directory separators.

# Local policy


The `sbx policy` command manages network access rules on your local machine.
Rules apply to all sandboxes on the machine when you use the global scope, or
to a single sandbox when scoped by name.

Local rules apply only when your organization doesn't enforce governance:

- **No org governance**: local rules fully control what sandboxes can access.
- **Org governance active**: the organization policy replaces local policy.
  Local rules are inactive, and `sbx policy allow` and `sbx policy deny` have
  no effect. To list the inactive local rules, run
  `sbx policy ls --include-inactive`. See
  [Monitoring](/ai/sandboxes/governance/local/monitoring/#showing-inactive-rules).

See [Organization policy](/ai/sandboxes/governance/local/org/) for how organization governance works.

For domain patterns, wildcards, CIDR ranges, and filesystem path syntax, see
[Policy concepts](/ai/sandboxes/governance/local/concepts/#rule-syntax).

## Default preset

The only way traffic can leave a sandbox is through an HTTP/HTTPS proxy on
your host, which enforces access rules on every outbound request. Non-HTTP TCP
traffic, including SSH, can be allowed by adding a policy rule for the
destination IP and port (for example, `sbx policy allow network "10.1.2.3:22"`).
UDP and ICMP are blocked at the network layer and can't be unblocked with policy
rules.

On first start, and after running `sbx policy reset`, the daemon prompts you
to choose a network preset:

```plaintext
Choose a default network policy:

     1. Open         — All network traffic allowed, no restrictions.
     2. Balanced     — Default deny, with common dev sites allowed.
     3. Locked Down  — All network traffic blocked unless you allow it.

  Use ↑/↓ to navigate, Enter to select, or press 1–3.
```

| Preset      | Description                                                                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Open        | All outbound traffic is allowed. Equivalent to adding a wildcard allow rule with `sbx policy allow network "**"`.                                 |
| Balanced    | Default deny, with a baseline allowlist covering AI provider APIs, package managers, code hosts, container registries, and common cloud services. |
| Locked Down | All outbound traffic is blocked, including model provider APIs (for example, `api.anthropic.com`). You must explicitly allow everything you need. |

The **Balanced** preset's baseline allowlist is a good starting point for most
workflows. Run `sbx policy ls` to see exactly which rules it includes.

> [!NOTE]
> If your organization manages sandbox policies centrally, organization rules
> take precedence over the preset you select here. See
> [Organization policy](/ai/sandboxes/governance/local/org/).

### Non-interactive environments

In non-interactive environments such as CI pipelines or headless servers, the
interactive prompt can't be displayed. Use `sbx policy set-default` to set the
preset before running any other `sbx` commands:

```console
$ sbx policy set-default balanced
```

Available values are `allow-all`, `balanced`, and `deny-all`.

## Managing rules

Use [`sbx policy allow`](/reference/cli/sbx/policy/allow/) and
[`sbx policy deny`](/reference/cli/sbx/policy/deny/) to add or restrict access
on top of the active preset. Changes take effect immediately. Rules apply to
all sandboxes by default:

```console
$ sbx policy allow network api.anthropic.com
$ sbx policy deny network ads.example.com
```

Pass `--sandbox <name>` to scope a rule to one sandbox:

```console
$ sbx policy allow network --sandbox my-sandbox api.example.com
$ sbx policy deny network --sandbox my-sandbox ads.example.com
```

Specify multiple hosts in one command with a comma-separated list:

```console
$ sbx policy allow network "api.anthropic.com,*.npmjs.org,*.pypi.org"
```

Remove a rule by resource or by rule ID:

```console
$ sbx policy rm network --resource ads.example.com
$ sbx policy rm network --id 2d3c1f0e-4a73-4e05-bc9d-f2f9a4b50d67
```

To remove a sandbox-scoped rule, pass `--sandbox <name>`:

```console
$ sbx policy rm network --sandbox my-sandbox --resource api.example.com
```

To inspect which rules are active and where they come from, use
`sbx policy ls`. See [Monitoring](/ai/sandboxes/governance/local/monitoring/).

### Resetting

To remove all custom rules and start fresh with a new preset, use
`sbx policy reset`:

```console
$ sbx policy reset
```

This deletes the local policy store and stops the daemon. When the daemon
restarts on the next command, you are prompted to choose a new preset. Running
sandboxes stop when the daemon shuts down. Pass `--force` to skip the
confirmation prompt:

```console
$ sbx policy reset --force
```

## Troubleshooting

### Local rules have no effect

If rules you add with `sbx policy allow` or `sbx policy deny` don't change
sandbox behavior, your organization likely has governance enabled. Run `sbx
policy ls` to check: if the output starts with a `Governance: managed by <org>`
header, org governance is active. When it's active, the organization policy
replaces local policy, so your rules have no effect. They're hidden from `sbx
policy ls` by default; run `sbx policy ls --include-inactive` to see them with
an `inactive` status.

Organization policy can't be supplemented from your machine. To change what
your sandboxes can access, ask your admin to update the organization policy in
the Admin Console.

### A domain is still blocked after adding an allow rule

If a domain remains blocked after you add a local allow rule, your organization
likely enforces governance, which makes local rules inactive. Run `sbx policy
ls` to check whether org governance is active; if the output starts with a
`Governance: managed by <org>` header, it is. Add `--include-inactive` to
confirm your rule shows an `inactive` status. If so, the block can only be
lifted by updating the org policy in the Admin Console or via the
[API](/reference/api/ai-governance/).

# Policy concepts


## Resource model

Docker sandbox governance is built around two resource types: **policies** and
**rules**.

A **policy** is a named collection of rules that controls sandbox access.
Policies exist at two levels:

- **Local**: configured per machine using the `sbx policy` CLI. Applies to
  sandboxes on that machine only.
- **Organization**: configured in the Docker Admin Console or via the
  [Governance API](/reference/api/ai-governance/). Applies to sandboxes across
  the organization. An organization can have several policies, each applying
  either org-wide or to specific teams. See [Policy scope](#policy-scope).

When organization governance is active, organization policies replace local
policies entirely. See [Precedence](#precedence).

A **rule** is the unit of access control within a policy. Each rule has:

- **Name**: a human-readable label
- **Actions**: the type of access the rule controls
- **Resources**: the targets the rule matches against
- **Decision**: `allow` or `deny`

Rules are grouped by domain: all rules in a policy must share the same domain,
either `network` or `filesystem`.

## Policy scope

Each organization policy applies either across the whole organization or only
to specific teams:

- Org-wide: with no teams assigned, the policy applies to every member of the
  organization.
- Team-scoped: with one or more teams assigned, the policy applies only to
  members of those teams.

Teams are the same [teams](/admin/organization/manage/manage-a-team/)
you manage for your organization; Docker matches a policy's teams against each
user's team membership. Because an organization can mix org-wide and team-scoped
policies, a single user is often subject to several at once. The policies that
apply to a given user are their _effective policies_: every org-wide policy,
plus every team-scoped policy for a team they belong to. See
[Rule evaluation](#rule-evaluation) for how a user's effective policies combine.

## Rule syntax

### Network rules

Network rules use the actions `connect:tcp` and `connect:udp`. Resources are
hostnames, CIDR ranges, or ports.

**Hostname patterns**

| Pattern               | Example           | Matches                                            |
| --------------------- | ----------------- | -------------------------------------------------- |
| Exact hostname        | `example.com`     | `example.com` only, not subdomains                 |
| Single-level wildcard | `*.example.com`   | One subdomain level: `api.example.com`             |
| Multi-level wildcard  | `**.example.com`  | Any depth: `api.example.com`, `v2.api.example.com` |
| Hostname with port    | `example.com:443` | `example.com` on port 443 only                     |

`example.com` and `*.example.com` don't cover each other. Specify both if you
need to match the root domain and its subdomains.

**CIDR ranges**

Both IPv4 and IPv6 notation are supported: `10.0.0.0/8`, `192.168.1.0/24`,
`2001:db8::/32`.

### Filesystem rules

Filesystem rules use the actions `read` and `write`. Resources are host paths
that sandboxes can mount as workspaces.

`~` expands to the user's home directory on every platform, including Windows,
where it resolves to `%USERPROFILE%`. A single `~/**` rule therefore matches
each user's home tree on macOS, Linux, and Windows. The policy engine expands
only `~`: it does not expand environment variables, so a pattern such as
`%USERPROFILE%\**` or `$HOME/**` matches nothing.

For a path outside the home directory, write it in the format the user's
operating system uses. A rule matches only the format it's written in, so a
location that several platforms share needs a rule for each:

| Operating system | Example path                               |
| ---------------- | ------------------------------------------ |
| macOS, Linux     | `/data/project/**`                         |
| Windows          | `C:\data\project\**`                       |
| WSL              | `\\wsl.localhost\<distro>\data\project\**` |

On Windows, `*:` matches any drive letter, so `*:\data\**` matches the path on
any drive.

Wildcards behave the same way in every path format:

| Pattern            | Example    | Matches                                                    |
| ------------------ | ---------- | ---------------------------------------------------------- |
| Exact path         | `/data`    | `/data` only                                               |
| Segment wildcard   | `/data/*`  | `/data/project`, one path segment only, not subdirectories |
| Recursive wildcard | `/data/**` | `/data/project`, `/data/project/src`, any depth            |

Use `**` to match a directory tree recursively. A single `*` matches within one
path segment and won't cross a path separator. For example, `~/**` matches all
paths under the home directory, while `~/*` matches only its direct children.

## Rule evaluation

When organization governance is active, the rules from all of a user's
[effective policies](#policy-scope) are combined and evaluated together against
each request, following two principles:

- Deny wins: if any rule matches with `decision: deny`, the request is denied,
  regardless of any matching allow rules.
- Default deny: anything an allow rule doesn't match is blocked. Outbound
  network traffic is blocked unless a network rule allows the destination, and a
  host path can't be mounted unless a filesystem rule allows it.

Because every effective policy feeds the same evaluation, allows are additive (a
request is allowed if any effective policy allows it) and denies are absolute (a
request is blocked if any effective policy denies it). A deny rule in an
org-wide policy therefore applies to everyone and can't be overridden by a
team-scoped policy, which makes org-wide deny rules useful as guardrails.

Local rules take no part in this evaluation; see [Precedence](#precedence).

## Precedence

Local and organization policies don't combine. Which one applies depends on
whether your organization has governance enabled:

- No organization governance: local rules and any
  [kit-defined network rules](/ai/sandboxes/customize/kits/#control-network-access)
  determine what sandboxes can access.
- Organization governance active: organization rules apply across all developer
  machines, and local and kit-defined rules are not evaluated. `sbx policy ls`
  hides these inactive rules by default; see
  [Monitoring](/ai/sandboxes/governance/concepts/monitoring/#showing-inactive-rules) for how to list them.

When organization governance is active, a user's organization policies are
evaluated together, as described in [Rule evaluation](#rule-evaluation).

# Dockerfile reference


Docker can build images automatically by reading the instructions from a
Dockerfile. A Dockerfile is a text document that contains all the commands a
user could call on the command line to assemble an image. This page describes
the commands you can use in a Dockerfile.

## Overview

The Dockerfile supports the following instructions:

| Instruction                            | Description                                                 |
| :------------------------------------- | :---------------------------------------------------------- |
| [`ADD`](#add)                          | Add local or remote files and directories.                  |
| [`ARG`](#arg)                          | Use build-time variables.                                   |
| [`CMD`](#cmd)                          | Specify default commands.                                   |
| [`COPY`](#copy)                        | Copy files and directories.                                 |
| [`ENTRYPOINT`](#entrypoint)            | Specify default executable.                                 |
| [`ENV`](#env)                          | Set environment variables.                                  |
| [`EXPOSE`](#expose)                    | Describe which ports your application is listening on.      |
| [`FROM`](#from)                        | Create a new build stage from a base image.                 |
| [`HEALTHCHECK`](#healthcheck)          | Check a container's health on startup.                      |
| [`LABEL`](#label)                      | Add metadata to an image.                                   |
| [`MAINTAINER`](#maintainer-deprecated) | Specify the author of an image.                             |
| [`ONBUILD`](#onbuild)                  | Specify instructions for when the image is used in a build. |
| [`RUN`](#run)                          | Execute build commands.                                     |
| [`SHELL`](#shell)                      | Set the default shell of an image.                          |
| [`STOPSIGNAL`](#stopsignal)            | Specify the system call signal for exiting a container.     |
| [`USER`](#user)                        | Set user and group ID.                                      |
| [`VOLUME`](#volume)                    | Create volume mounts.                                       |
| [`WORKDIR`](#workdir)                  | Change working directory.                                   |

## Format

Here is the format of the Dockerfile:

```dockerfile
# Comment
INSTRUCTION arguments
```

The instruction is not case-sensitive. However, convention is for them to
be UPPERCASE to distinguish them from arguments more easily.

Docker runs instructions in a Dockerfile in order. A Dockerfile **must
begin with a `FROM` instruction**. This may be after [parser
directives](#parser-directives), [comments](#format), and globally scoped
[ARGs](#arg). The `FROM` instruction specifies the [base
image](https://docs.docker.com/glossary/#base-image) from which you are
building. `FROM` may only be preceded by one or more `ARG` instructions, which
declare arguments that are used in `FROM` lines in the Dockerfile.

BuildKit treats lines that begin with `#` as a comment, unless the line is
a valid [parser directive](#parser-directives). A `#` marker anywhere
else in a line is treated as an argument. This allows statements like:

```dockerfile
# Comment
RUN echo 'we are running some # of cool things'
```

Comment lines are removed before the Dockerfile instructions are executed.
The comment in the following example is removed before the shell executes
the `echo` command.

```dockerfile
RUN echo hello \
# comment
world
```

The following examples is equivalent.

```dockerfile
RUN echo hello \
world
```

Comments don't support line continuation characters.

> [!NOTE]
> **Note on whitespace**
>
> For backward compatibility, leading whitespace before comments (`#`) and
> instructions (such as `RUN`) are ignored, but discouraged. Leading whitespace
> is not preserved in these cases, and the following examples are therefore
> equivalent:
>
> ```dockerfile
>         # this is a comment-line
>     RUN echo hello
> RUN echo world
> ```
>
> ```dockerfile
> # this is a comment-line
> RUN echo hello
> RUN echo world
> ```
>
> Whitespace in instruction arguments, however, isn't ignored.
> The following example prints `    hello    world`
> with leading whitespace as specified:
>
> ```dockerfile
> RUN echo "\
>      hello\
>      world"
> ```

## Parser directives

Parser directives are optional, and affect the way in which subsequent lines
in a Dockerfile are handled. Parser directives don't add layers to the build,
and don't show up as build steps. Parser directives are written as a
special type of comment in the form `# directive=value`. A single directive
may only be used once.

The following parser directives are supported:

- [`syntax`](#syntax)
- [`escape`](#escape)
- [`check`](#check) (since Dockerfile v1.8.0)

Once a comment, empty line or builder instruction has been processed, BuildKit
no longer looks for parser directives. Instead it treats anything formatted
as a parser directive as a comment and doesn't attempt to validate if it might
be a parser directive. Therefore, all parser directives must be at the
top of a Dockerfile.

Parser directive keys, such as `syntax` or `check`, aren't case-sensitive, but
they're lowercase by convention. Values for a directive are case-sensitive and
must be written in the appropriate case for the directive. For example,
`#check=skip=jsonargsrecommended` is invalid because the check name must use
Pascal case, not lowercase. It's also conventional to include a blank line
following any parser directives. Line continuation characters aren't supported
in parser directives.

Due to these rules, the following examples are all invalid:

Invalid due to line continuation:

```dockerfile
# direc \
tive=value
```

Invalid due to appearing twice:

```dockerfile
# directive=value1
# directive=value2

FROM ImageName
```

Treated as a comment because it appears after a builder instruction:

```dockerfile
FROM ImageName
# directive=value
```

Treated as a comment because it appears after a comment that isn't a parser
directive:

```dockerfile
# About my dockerfile
# directive=value
FROM ImageName
```

The following `unknowndirective` is treated as a comment because it isn't
recognized. The known `syntax` directive is treated as a comment because it
appears after a comment that isn't a parser directive.

```dockerfile
# unknowndirective=value
# syntax=value
```

Non line-breaking whitespace is permitted in a parser directive. Hence, the
following lines are all treated identically:

```dockerfile
#directive=value
# directive =value
#	directive= value
# directive = value
#	  dIrEcTiVe=value
```

### syntax

<a name="external-implementation-features"><!-- included for deep-links to old section --></a>

Use the `syntax` parser directive to declare the Dockerfile syntax version to
use for the build. If unspecified, BuildKit uses a bundled version of the
Dockerfile frontend. Declaring a syntax version lets you automatically use the
latest Dockerfile version without having to upgrade BuildKit or Docker Engine,
or even use a custom Dockerfile implementation.

Most users will want to set this parser directive to `docker/dockerfile:1`,
which causes BuildKit to pull the latest stable version of the Dockerfile
syntax before the build.

```dockerfile
# syntax=docker/dockerfile:1
```

For more information about how the parser directive works, see
[Custom Dockerfile syntax](https://docs.docker.com/build/buildkit/dockerfile-frontend/).

### escape

```dockerfile
# escape=\
```

Or

```dockerfile
# escape=`
```

The `escape` directive sets the character used to escape characters in a
Dockerfile. If not specified, the default escape character is `\`.

The escape character is used both to escape characters in a line, and to
escape a newline. This allows a Dockerfile instruction to
span multiple lines. Note that regardless of whether the `escape` parser
directive is included in a Dockerfile, escaping is not performed in
a `RUN` command, except at the end of a line.

Setting the escape character to `` ` `` is especially useful on
`Windows`, where `\` is the directory path separator. `` ` `` is consistent
with [Windows PowerShell](https://technet.microsoft.com/en-us/library/hh847755.aspx).

Consider the following example which would fail in a non-obvious way on
Windows. The second `\` at the end of the second line would be interpreted as an
escape for the newline, instead of a target of the escape from the first `\`.
Similarly, the `\` at the end of the third line would, assuming it was actually
handled as an instruction, cause it be treated as a line continuation. The result
of this Dockerfile is that second and third lines are considered a single
instruction:

```dockerfile
FROM microsoft/nanoserver
COPY testfile.txt c:\\
RUN dir c:\
```

Results in:

```console
PS E:\myproject> docker build -t cmd .

Sending build context to Docker daemon 3.072 kB
Step 1/2 : FROM microsoft/nanoserver
 ---> 22738ff49c6d
Step 2/2 : COPY testfile.txt c:\RUN dir c:
GetFileAttributesEx c:RUN: The system cannot find the file specified.
PS E:\myproject>
```

One solution to the above would be to use `/` as the target of both the `COPY`
instruction, and `dir`. However, this syntax is, at best, confusing as it is not
natural for paths on Windows, and at worst, error prone as not all commands on
Windows support `/` as the path separator.

By adding the `escape` parser directive, the following Dockerfile succeeds as
expected with the use of natural platform semantics for file paths on Windows:

```dockerfile
# escape=`

FROM microsoft/nanoserver
COPY testfile.txt c:\
RUN dir c:\
```

Results in:

```console
PS E:\myproject> docker build -t succeeds --no-cache=true .

Sending build context to Docker daemon 3.072 kB
Step 1/3 : FROM microsoft/nanoserver
 ---> 22738ff49c6d
Step 2/3 : COPY testfile.txt c:\
 ---> 96655de338de
Removing intermediate container 4db9acbb1682
Step 3/3 : RUN dir c:\
 ---> Running in a2c157f842f5
 Volume in drive C has no label.
 Volume Serial Number is 7E6D-E0F7

 Directory of c:\

10/05/2016  05:04 PM             1,894 License.txt
10/05/2016  02:22 PM    <DIR>          Program Files
10/05/2016  02:14 PM    <DIR>          Program Files (x86)
10/28/2016  11:18 AM                62 testfile.txt
10/28/2016  11:20 AM    <DIR>          Users
10/28/2016  11:20 AM    <DIR>          Windows
           2 File(s)          1,956 bytes
           4 Dir(s)  21,259,096,064 bytes free
 ---> 01c7f3bef04f
Removing intermediate container a2c157f842f5
Successfully built 01c7f3bef04f
PS E:\myproject>
```

### check

```dockerfile
# check=skip=<checks|all>
# check=error=<boolean>
```

The `check` directive is used to configure how [build checks](https://docs.docker.com/build/checks/)
are evaluated. By default, all checks are run, and failures are treated as
warnings.

You can disable specific checks using `#check=skip=<check-name>`. To specify
multiple checks to skip, separate them with a comma:

```dockerfile
# check=skip=JSONArgsRecommended,StageNameCasing
```

To disable all checks, use `#check=skip=all`.

By default, builds with failing build checks exit with a zero status code
despite warnings. To make the build fail on warnings, set `#check=error=true`.

```dockerfile
# check=error=true
```

> [!NOTE]
> When using the `check` directive, with `error=true` option, it is recommended
> to pin the [Dockerfile syntax](#syntax) to a specific version. Otherwise, your build may
> start to fail when new checks are added in the future versions.

To combine both the `skip` and `error` options, use a semi-colon to separate
them:

```dockerfile
# check=skip=JSONArgsRecommended;error=true
```

To see all available checks, see the [build checks reference](https://docs.docker.com/reference/build-checks/).
Note that the checks available depend on the Dockerfile syntax version. To make
sure you're getting the most up-to-date checks, use the [`syntax`](#syntax)
directive to specify the Dockerfile syntax version to the latest stable
version.

## Environment replacement

Environment variables (declared with [the `ENV` statement](#env)) can also be
used in certain instructions as variables to be interpreted by the
Dockerfile. Escapes are also handled for including variable-like syntax
into a statement literally.

Environment variables are notated in the Dockerfile either with
`$variable_name` or `${variable_name}`. They are treated equivalently and the
brace syntax is typically used to address issues with variable names with no
whitespace, like `${foo}_bar`.

The `${variable_name}` syntax also supports a few of the standard `bash`
modifiers as specified below:

- `${variable:-word}` indicates that if `variable` is set and non-empty then
  the result will be that value. If `variable` is unset or empty then `word`
  will be the result.
- `${variable-word}` indicates that if `variable` is set (even if empty) then
  the result will be that value. If `variable` is unset then `word` will be
  the result.
- `${variable:+word}` indicates that if `variable` is set and non-empty then
  `word` will be the result, otherwise the result is the empty string.
- `${variable+word}` indicates that if `variable` is set (even if empty) then
  `word` will be the result, otherwise the result is the empty string.

The following variable replacements are supported in a pre-release version of
Dockerfile syntax, when using the `# syntax=docker/dockerfile-upstream:master` syntax
directive in your Dockerfile:

- `${variable#pattern}` removes the shortest match of `pattern` from `variable`,
  seeking from the start of the string.
  
  ```bash
  str=foobarbaz echo ${str#f*b}     # arbaz
  ```
  
- `${variable##pattern}` removes the longest match of `pattern` from `variable`,
  seeking from the start of the string.

  ```bash
  str=foobarbaz echo ${str##f*b}    # az
  ```

- `${variable%pattern}` removes the shortest match of `pattern` from `variable`,
  seeking backwards from the end of the string.

  ```bash
  string=foobarbaz echo ${string%b*}    # foobar
  ```

- `${variable%%pattern}` removes the longest match of `pattern` from `variable`,
  seeking backwards from the end of the string.

  ```bash
  string=foobarbaz echo ${string%%b*}   # foo
  ```

- `${variable/pattern/replacement}` replace the first occurrence of `pattern`
  in `variable` with `replacement`

  ```bash
  string=foobarbaz echo ${string/ba/fo}  # fooforbaz
  ```

- `${variable//pattern/replacement}` replaces all occurrences of `pattern`
  in `variable` with `replacement`

  ```bash
  string=foobarbaz echo ${string//ba/fo}  # fooforfoz
  ```

In all cases, `word` can be any string, including additional environment
variables.

`pattern` is a glob pattern where `?` matches any single character
and `*` any number of characters (including zero). To match literal `?` and `*`,
use a backslash escape: `\?` and `\*`.

You can escape whole variable names by adding a `\` before the variable: `\$foo` or `\${foo}`,
for example, will translate to `$foo` and `${foo}` literals respectively.

Example (parsed representation is displayed after the `#`):

```dockerfile
FROM busybox
ENV FOO=/bar
WORKDIR ${FOO}   # WORKDIR /bar
ADD . $FOO       # ADD . /bar
COPY \$FOO /quux # COPY $FOO /quux
```

Environment variables are supported by the following list of instructions in
the Dockerfile:

- `ADD`
- `COPY`
- `ENV`
- `EXPOSE`
- `FROM`
- `LABEL`
- `STOPSIGNAL`
- `USER`
- `VOLUME`
- `WORKDIR`
- `ONBUILD` (when combined with one of the supported instructions above)

You can also use environment variables with `RUN`, `CMD`, and `ENTRYPOINT`
instructions, but in those cases the variable substitution is handled by the
command shell, not the builder. Note that instructions using the exec form
don't invoke a command shell automatically. See [Variable
substitution](#variable-substitution).

Environment variable substitution use the same value for each variable
throughout the entire instruction. Changing the value of a variable only takes
effect in subsequent instructions. Consider the following example:

```dockerfile
ENV abc=hello
ENV abc=bye def=$abc
ENV ghi=$abc
```

- The value of `def` becomes `hello`
- The value of `ghi` becomes `bye`

## .dockerignore file

You can use `.dockerignore` file to exclude files and directories from the
build context. For more information, see
[.dockerignore file](https://docs.docker.com/build/building/context/#dockerignore-files).

## Shell and exec form

The `RUN`, `CMD`, and `ENTRYPOINT` instructions all have two possible forms:

- `INSTRUCTION ["executable","param1","param2"]` (exec form)
- `INSTRUCTION command param1 param2` (shell form)

The exec form makes it possible to avoid shell string munging, and to invoke
commands using a specific command shell, or any other executable. It uses a
JSON array syntax, where each element in the array is a command, flag, or
argument.

The shell form is more relaxed, and emphasizes ease of use, flexibility, and
readability. The shell form automatically uses a command shell, whereas the
exec form does not.

### Exec form

The exec form is parsed as a JSON array, which means that
you must use double-quotes (") around words, not single-quotes (').

```dockerfile
ENTRYPOINT ["/bin/bash", "-c", "echo hello"]
```

The exec form is best used to specify an `ENTRYPOINT` instruction, combined
with `CMD` for setting default arguments that can be overridden at runtime. For
more information, see [ENTRYPOINT](#entrypoint).

#### Variable substitution

Using the exec form doesn't automatically invoke a command shell. This means
that normal shell processing, such as variable substitution, doesn't happen.
For example, `RUN [ "echo", "$HOME" ]` won't handle variable substitution for
`$HOME`.

If you want shell processing then either use the shell form or execute a shell
directly with the exec form, for example: `RUN [ "sh", "-c", "echo $HOME" ]`.
When using the exec form and executing a shell directly, as in the case for the
shell form, it's the shell that's doing the environment variable substitution,
not the builder.

#### Backslashes

In exec form, you must escape backslashes. This is particularly relevant on
Windows where the backslash is the path separator. The following line would
otherwise be treated as shell form due to not being valid JSON, and fail in an
unexpected way:

```dockerfile
RUN ["c:\windows\system32\tasklist.exe"]
```

The correct syntax for this example is:

```dockerfile
RUN ["c:\\windows\\system32\\tasklist.exe"]
```

### Shell form

Unlike the exec form, instructions using the shell form always use a command
shell. The shell form doesn't use the JSON array format, instead it's a regular
string. The shell form string lets you escape newlines using the [escape
character](#escape) (backslash by default) to continue a single instruction
onto the next line. This makes it easier to use with longer commands, because
it lets you split them up into multiple lines. For example, consider these two
lines:

```dockerfile
RUN source $HOME/.bashrc && \
echo $HOME
```

They're equivalent to the following line:

```dockerfile
RUN source $HOME/.bashrc && echo $HOME
```

You can also use heredocs with the shell form to break up supported commands.

```dockerfile
RUN <<EOF
  source $HOME/.bashrc
  echo $HOME
EOF
```

For more information about heredocs, see [Here-documents](#here-documents).

### Use a different shell

You can change the default shell using the `SHELL` command. For example:

```dockerfile
SHELL ["/bin/bash", "-c"]
RUN echo hello
```

For more information, see [SHELL](#shell).

## FROM

```dockerfile
FROM [--platform=<platform>] <image> [AS <name>]
```

Or

```dockerfile
FROM [--platform=<platform>] <image>[:<tag>] [AS <name>]
```

Or

```dockerfile
FROM [--platform=<platform>] <image>[@<digest>] [AS <name>]
```

The `FROM` instruction initializes a new build stage and sets the
[base image](https://docs.docker.com/glossary/#base-image) for subsequent
instructions. As such, a valid Dockerfile must start with a `FROM` instruction.
The image can be any valid image.

- `ARG` is the only instruction that may precede `FROM` in the Dockerfile.
  See [Understand how ARG and FROM interact](#understand-how-arg-and-from-interact).
- `FROM` can appear multiple times within a single Dockerfile to
  create multiple images or use one build stage as a dependency for another.
  Simply make a note of the last image ID output by the commit before each new
  `FROM` instruction. Each `FROM` instruction clears any state created by previous
  instructions.
- Optionally a name can be given to a new build stage by adding `AS name` to the
  `FROM` instruction. The name can be used in subsequent `FROM <name>`,
  [`COPY --from=<name>`](#copy---from),
  and [`RUN --mount=type=bind,from=<name>`](#run---mounttypebind) instructions
  to refer to the image built in this stage.

  Using a previous build stage as the base for a subsequent stage is a common
  pattern for sharing a common base environment:

  ```dockerfile
  FROM ubuntu AS base
  RUN apt-get update && apt-get install -y shared-tooling

  FROM base AS dev
  RUN apt-get install -y dev-tooling

  FROM base AS prod
  COPY --from=build /app /app
  ```
- The `tag` or `digest` values are optional. If you omit either of them, the
  builder assumes a `latest` tag by default. The builder returns an error if it
  can't find the `tag` value.

The optional `--platform` flag can be used to specify the platform of the image
in case `FROM` references a multi-platform image. For example, `linux/amd64`,
`linux/arm64`, or `windows/amd64`. By default, the target platform of the build
request is used. Global build arguments can be used in the value of this flag,
for example [automatic platform ARGs](#automatic-platform-args-in-the-global-scope)
allow you to force a stage to native build platform (`--platform=$BUILDPLATFORM`),
and use it to cross-compile to the target platform inside the stage.

### Understand how ARG and FROM interact

`FROM` instructions support variables that are declared by any `ARG`
instructions that occur before the first `FROM`.

```dockerfile
ARG  CODE_VERSION=latest
FROM base:${CODE_VERSION}
CMD  /code/run-app

FROM extras:${CODE_VERSION}
CMD  /code/run-extras
```

An `ARG` declared before a `FROM` is outside of a build stage, so it
can't be used in any instruction after a `FROM`. To use the default value of
an `ARG` declared before the first `FROM` use an `ARG` instruction without
a value inside of a build stage:

```dockerfile
ARG VERSION=latest
FROM busybox:$VERSION
ARG VERSION
RUN echo $VERSION > image_version
```

## RUN

The `RUN` instruction will execute any commands to create a new layer on top of
the current image. The added layer is used in the next step in the Dockerfile.
`RUN` has two forms:

```dockerfile
# Shell form:
RUN [OPTIONS] <command> ...
# Exec form:
RUN [OPTIONS] [ "<command>", ... ]
```

For more information about the differences between these two forms, see
[shell or exec forms](#shell-and-exec-form).

The shell form is most commonly used, and lets you break up longer
instructions into multiple lines, either using newline [escapes](#escape), or
with [heredocs](#here-documents):

```dockerfile
RUN <<EOF
apt-get update
apt-get install -y curl
EOF
```

The available `[OPTIONS]` for the `RUN` instruction are:

| Option                          | Minimum Dockerfile version |
|---------------------------------|----------------------------|
| [`--device`](#run---device)     | 1.14-labs                  |
| [`--mount`](#run---mount)       | 1.2                        |
| [`--network`](#run---network)   | 1.3                        |
| [`--security`](#run---security) | 1.20                       |

### Cache invalidation for RUN instructions

The cache for `RUN` instructions isn't invalidated automatically during
the next build. The cache for an instruction like
`RUN apt-get dist-upgrade -y` will be reused during the next build. The
cache for `RUN` instructions can be invalidated by using the `--no-cache`
flag, for example `docker build --no-cache`.

See the [Dockerfile Best Practices
guide](https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/) for more information.

The cache for `RUN` instructions can be invalidated by [`ADD`](#add) and [`COPY`](#copy) instructions.

### RUN --device

> [!NOTE]
> Not yet available in stable syntax, use [`docker/dockerfile:1-labs`](#syntax)
> version. It also needs BuildKit 0.20.0 or later.

```dockerfile
RUN --device=name,[required]
```

`RUN --device` allows build to request [CDI devices](https://github.com/moby/buildkit/blob/master/docs/cdi.md)
to be available to the build step.

> [!WARNING]
> The use of `--device` is protected by the `device` entitlement, which needs
> to be enabled when starting the buildkitd daemon with
> `--allow-insecure-entitlement device` flag or in [buildkitd config](https://github.com/moby/buildkit/blob/master/docs/buildkitd.toml.md),
> and for a build request with [`--allow device` flag](https://docs.docker.com/engine/reference/commandline/buildx_build/#allow).

The device `name` is provided by the CDI specification registered in BuildKit.

In the following example, multiple devices are registered in the CDI
specification for the `vendor1.com/device` vendor.

```yaml
cdiVersion: "0.6.0"
kind: "vendor1.com/device"
devices:
  - name: foo
    containerEdits:
      env:
        - FOO=injected
  - name: bar
    annotations:
      org.mobyproject.buildkit.device.class: class1
    containerEdits:
      env:
        - BAR=injected
  - name: baz
    annotations:
      org.mobyproject.buildkit.device.class: class1
    containerEdits:
      env:
        - BAZ=injected
  - name: qux
    annotations:
      org.mobyproject.buildkit.device.class: class2
    containerEdits:
      env:
        - QUX=injected
annotations:
  org.mobyproject.buildkit.device.autoallow: true
```

The device name format is flexible and accepts various patterns to support
multiple device configurations:

* `vendor1.com/device`: request the first device found for this vendor
* `vendor1.com/device=foo`: request a specific device
* `vendor1.com/device=*`: request all devices for this vendor
* `class1`: request devices by `org.mobyproject.buildkit.device.class` annotation

> [!NOTE]
> Annotations are supported by the CDI specification since 0.6.0.

> [!NOTE]
> To automatically allow all devices registered in the CDI specification, you
> can set the `org.mobyproject.buildkit.device.autoallow` annotation. You can
> also set this annotation for a specific device.

#### Example: CUDA-Powered LLaMA Inference

In this example we use the `--device` flag to run `llama.cpp` inference using
an NVIDIA GPU device through CDI:

```dockerfile
# syntax=docker/dockerfile:1-labs

FROM scratch AS model
ADD https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf /model.gguf

FROM scratch AS prompt
COPY <<EOF prompt.txt
Q: Generate  a list of 10 unique biggest countries by population in JSON with their estimated poulation in 1900 and 2024. Answer only newline formatted JSON with keys "country", "population_1900", "population_2024" with 10 items.
A:
[
    {

EOF

FROM ghcr.io/ggml-org/llama.cpp:full-cuda-b5124
RUN --device=nvidia.com/gpu=all \
    --mount=from=model,target=/models \
    --mount=from=prompt,target=/tmp \
    ./llama-cli -m /models/model.gguf -no-cnv -ngl 99 -f /tmp/prompt.txt
```

### RUN --mount

```dockerfile
RUN --mount=[type=<TYPE>][,option=<value>[,option=<value>]...]
```

`RUN --mount` allows you to create filesystem mounts that the build can access.
This can be used to:

- Create bind mount to the host filesystem or other build stages
- Access build secrets or ssh-agent sockets
- Use a persistent package management cache to speed up your build

The supported mount types are:

| Type                                     | Description                                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| [`bind`](#run---mounttypebind) (default) | Bind-mount context directories (read-only).                                                                              |
| [`cache`](#run---mounttypecache)         | Mount a temporary directory to cache directories for compilers and package managers.                                     |
| [`tmpfs`](#run---mounttypetmpfs)         | Mount a `tmpfs` in the build container.                                                                                  |
| [`secret`](#run---mounttypesecret)       | Allow the build container to access secure files such as private keys without baking them into the image or build cache. |
| [`ssh`](#run---mounttypessh)             | Allow the build container to access SSH keys via SSH agents, with support for passphrases.                               |

### RUN --mount=type=bind

This mount type allows binding files or directories to the build container. A
bind mount is read-only by default.

| Option                             | Description                                                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `target`, `dst`, `destination`[^1] | Mount path.                                                                                                                                   |
| `source`                           | Source path in the `from`. Defaults to the root of the `from`.                                                                                |
| `from`                             | Build stage, context, or image name for the root of the source. Defaults to the build context.                                                |
| `rw`,`readwrite`                   | Allow writes on the mount. Written data will be discarded after the `RUN` instruction completes and will not be committed to the image layer. |


### RUN --mount=type=cache

This mount type allows the build container to cache directories for compilers
and package managers.

| Option                             | Description                                                                                                                                                                                                                                                                |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                               | Optional ID to identify separate/different caches. Defaults to value of `target`.                                                                                                                                                                                          |
| `target`, `dst`, `destination`[^1] | Mount path.                                                                                                                                                                                                                                                                |
| `ro`,`readonly`                    | Read-only if set.                                                                                                                                                                                                                                                          |
| `sharing`                          | One of `shared`, `private`, or `locked`. Defaults to `shared`. A `shared` cache mount can be used concurrently by multiple writers. `private` creates a new mount if there are multiple writers. `locked` pauses the second writer until the first one releases the mount. |
| `from`                             | Build stage, context, or image name to use as a base of the cache mount. Defaults to empty directory.                                                                                                                                                                      |
| `source`                           | Subpath in the `from` to mount. Defaults to the root of the `from`.                                                                                                                                                                                                        |
| `mode`                             | File mode for new cache directory in octal. Default `0755`.                                                                                                                                                                                                                |
| `uid`                              | User ID for new cache directory. Default `0`.                                                                                                                                                                                                                              |
| `gid`                              | Group ID for new cache directory. Default `0`.                                                                                                                                                                                                                             |

Contents of the cache directories persists between builder invocations without
invalidating the instruction cache. Cache mounts should only be used for better
performance. Your build should work with any contents of the cache directory as
another build may overwrite the files or GC may clean it if more storage space
is needed.

#### Example: cache Go packages

```dockerfile
# syntax=docker/dockerfile:1
FROM golang
RUN --mount=type=cache,target=/root/.cache/go-build \
  go build ...
```

#### Example: cache apt packages

```dockerfile
# syntax=docker/dockerfile:1
FROM ubuntu
RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
  --mount=type=cache,target=/var/lib/apt,sharing=locked \
  apt-get update && apt-get --no-install-recommends install -y gcc
```

Apt needs exclusive access to its data, so the caches use the option
`sharing=locked`, which will make sure multiple parallel builds using
the same cache mount will wait for each other and not access the same
cache files at the same time. You could also use `sharing=private` if
you prefer to have each build create another cache directory in this
case.

### RUN --mount=type=tmpfs

This mount type allows mounting `tmpfs` in the build container.

| Option                             | Description                                           |
| ---------------------------------- | ----------------------------------------------------- |
| `target`, `dst`, `destination`[^1] | Mount path.                                           |
| `size`                             | Specify an upper limit on the size of the filesystem. |

### RUN --mount=type=secret

This mount type allows the build container to access secret values, such as
tokens or private keys, without baking them into the image.

By default, the secret is mounted as a file. You can also mount the secret as
an environment variable by setting the `env` option.

| Option                         | Description                                                                                                     |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| `id`                           | ID of the secret. Defaults to basename of the target path.                                                      |
| `target`, `dst`, `destination` | Mount the secret to the specified path. Defaults to `/run/secrets/` + `id` if unset and if `env` is also unset. |
| `env`                          | Mount the secret to an environment variable instead of a file, or both. (since Dockerfile v1.10.0)              |
| `required`                     | If set to `true`, the instruction errors out when the secret is unavailable. Defaults to `false`.               |
| `mode`                         | File mode for secret file in octal. Default `0400`.                                                             |
| `uid`                          | User ID for secret file. Default `0`.                                                                           |
| `gid`                          | Group ID for secret file. Default `0`.                                                                          |

#### Example: access to S3

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3
RUN pip install awscli
RUN --mount=type=secret,id=aws,target=/root/.aws/credentials \
  aws s3 cp s3://... ...
```

```console
$ docker buildx build --secret id=aws,src=$HOME/.aws/credentials .
```

#### Example: Mount as environment variable

The following example takes the secret `API_KEY` and mounts it as an
environment variable with the same name.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
RUN --mount=type=secret,id=API_KEY,env=API_KEY \
    some-command --token-from-env $API_KEY
```

Assuming that the `API_KEY` environment variable is set in the build
environment, you can build this with the following command:

```console
$ docker buildx build --secret id=API_KEY .
```

### RUN --mount=type=ssh

This mount type allows the build container to access SSH keys via SSH agents,
with support for passphrases.

| Option                         | Description                                                                                    |
| ------------------------------ | ---------------------------------------------------------------------------------------------- |
| `id`                           | ID of SSH agent socket or key. Defaults to "default".                                          |
| `target`, `dst`, `destination` | SSH agent socket path. Defaults to `/run/buildkit/ssh_agent.${N}`.                             |
| `required`                     | If set to `true`, the instruction errors out when the key is unavailable. Defaults to `false`. |
| `mode`                         | File mode for socket in octal. Default `0600`.                                                 |
| `uid`                          | User ID for socket. Default `0`.                                                               |
| `gid`                          | Group ID for socket. Default `0`.                                                              |

#### Example: access to GitLab

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
RUN apk add --no-cache openssh-client
RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan gitlab.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh \
  ssh -q -T git@gitlab.com 2>&1 | tee /hello
# "Welcome to GitLab, @GITLAB_USERNAME_ASSOCIATED_WITH_SSHKEY" should be printed here
# with the type of build progress is defined as `plain`.
```

```console
$ eval $(ssh-agent)
$ ssh-add ~/.ssh/id_rsa
(Input your passphrase here)
$ docker buildx build --ssh default=$SSH_AUTH_SOCK .
```

You can also specify a path to `*.pem` file on the host directly instead of `$SSH_AUTH_SOCK`.
However, pem files with passphrases are not supported.

### RUN --network

```dockerfile
RUN --network=<TYPE>
```

`RUN --network` allows control over which networking environment the command
is run in.

The supported network types are:

| Type                                         | Description                            |
| -------------------------------------------- | -------------------------------------- |
| [`default`](#run---networkdefault) (default) | Run in the default network.            |
| [`none`](#run---networknone)                 | Run with no network access.            |
| [`host`](#run---networkhost)                 | Run in the host's network environment. |

### RUN --network=default

Equivalent to not supplying a flag at all, the command is run in the default
network for the build.

### RUN --network=none

The command is run with no network access (`lo` is still available, but is
isolated to this process)

#### Example: isolating external effects

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.6
ADD mypackage.tgz wheels/
RUN --network=none pip install --find-links wheels mypackage
```

`pip` will only be able to install the packages provided in the tarfile, which
can be controlled by an earlier build stage.

### RUN --network=host

The command is run in the host's network environment (similar to
`docker build --network=host`, but on a per-instruction basis)

> [!WARNING]
> The use of `--network=host` is protected by the `network.host` entitlement,
> which needs to be enabled when starting the buildkitd daemon with
> `--allow-insecure-entitlement network.host` flag or in [buildkitd config](https://github.com/moby/buildkit/blob/master/docs/buildkitd.toml.md),
> and for a build request with [`--allow network.host` flag](https://docs.docker.com/engine/reference/commandline/buildx_build/#allow).

### RUN --security

```dockerfile
RUN --security=<sandbox|insecure>
```

The default security mode is `sandbox`.
With `--security=insecure`, the builder runs the command without sandbox in insecure
mode, which allows to run flows requiring elevated privileges (e.g. containerd).
This is equivalent to running `docker run --privileged`.

> [!WARNING]
> In order to access this feature, entitlement `security.insecure` should be
> enabled when starting the buildkitd daemon with
> `--allow-insecure-entitlement security.insecure` flag or in [buildkitd config](https://github.com/moby/buildkit/blob/master/docs/buildkitd.toml.md),
> and for a build request with [`--allow security.insecure` flag](https://docs.docker.com/engine/reference/commandline/buildx_build/#allow).

Default sandbox mode can be activated via `--security=sandbox`, but that is no-op.

#### Example: check entitlements

```dockerfile
# syntax=docker/dockerfile:1
FROM ubuntu
RUN --security=insecure cat /proc/self/status | grep CapEff
```

```text
#84 0.093 CapEff:	0000003fffffffff
```

## CMD

The `CMD` instruction sets the command to be executed when running a container
from an image.

You can specify `CMD` instructions using
[shell or exec forms](#shell-and-exec-form):

- `CMD ["executable","param1","param2"]` (exec form)
- `CMD ["param1","param2"]` (exec form, as default parameters to `ENTRYPOINT`)
- `CMD command param1 param2` (shell form)

There can only be one `CMD` instruction in a Dockerfile. If you list more than
one `CMD`, only the last one takes effect.

The purpose of a `CMD` is to provide defaults for an executing container. These
defaults can include an executable, or they can omit the executable, in which
case you must specify an `ENTRYPOINT` instruction as well.

If you would like your container to run the same executable every time, then
you should consider using `ENTRYPOINT` in combination with `CMD`. See
[`ENTRYPOINT`](#entrypoint). If the user specifies arguments to `docker run`
then they will override the default specified in `CMD`, but still use the
default `ENTRYPOINT`.

If `CMD` is used to provide default arguments for the `ENTRYPOINT` instruction,
both the `CMD` and `ENTRYPOINT` instructions should be specified in the
[exec form](#exec-form).

> [!NOTE]
> Don't confuse `RUN` with `CMD`. `RUN` actually runs a command and commits
> the result; `CMD` doesn't execute anything at build time, but specifies
> the intended command for the image.

## LABEL

```dockerfile
LABEL <key>=<value> [<key>=<value>...]
```

The `LABEL` instruction adds metadata to an image. A `LABEL` is a
key-value pair. To include spaces within a `LABEL` value, use quotes and
backslashes as you would in command-line parsing. A few usage examples:

```dockerfile
LABEL "com.example.vendor"="ACME Incorporated"
LABEL com.example.label-with-value="foo"
LABEL version="1.0"
LABEL description="This text illustrates \
that label-values can span multiple lines."
```

An image can have more than one label. You can specify multiple labels on a
single line. Prior to Docker 1.10, this decreased the size of the final image,
but this is no longer the case. You may still choose to specify multiple labels
in a single instruction, in one of the following two ways:

```dockerfile
LABEL multi.label1="value1" multi.label2="value2" other="value3"
```

```dockerfile
LABEL multi.label1="value1" \
      multi.label2="value2" \
      other="value3"
```

> [!NOTE]
> Be sure to use double quotes and not single quotes. Particularly when you are
> using string interpolation (e.g. `LABEL example="foo-$ENV_VAR"`), single
> quotes will take the string as is without unpacking the variable's value.

Labels included in base images (images in the `FROM` line) are inherited by
your image. If a label already exists but with a different value, the
most-recently-applied value overrides any previously-set value.

In a multi-stage build, labels from intermediate stages are only present in
the final image if the final stage is directly or indirectly based on them
(via `FROM`). Labels from a stage that you only reference with
`COPY --from` or `RUN --mount=from=` are not included in the output image.
Labels from the base image specified in the final `FROM` instruction are
always inherited.

To view an image's labels, use the `docker image inspect` command. You can use
the `--format` option to show just the labels;

```console
$ docker image inspect --format='{{json .Config.Labels}}' myimage
```

```json
{
  "com.example.vendor": "ACME Incorporated",
  "com.example.label-with-value": "foo",
  "version": "1.0",
  "description": "This text illustrates that label-values can span multiple lines.",
  "multi.label1": "value1",
  "multi.label2": "value2",
  "other": "value3"
}
```

## MAINTAINER (deprecated)

```dockerfile
MAINTAINER <name>
```

The `MAINTAINER` instruction sets the _Author_ field of the generated images.
The `LABEL` instruction is a much more flexible version of this and you should use
it instead, as it enables setting any metadata you require, and can be viewed
easily, for example with `docker inspect`. To set a label corresponding to the
`MAINTAINER` field you could use:

```dockerfile
LABEL org.opencontainers.image.authors="SvenDowideit@home.org.au"
```

This will then be visible from `docker inspect` with the other labels.

## EXPOSE

```dockerfile
EXPOSE <port> [<port>/<protocol>...]
```

The `EXPOSE` instruction informs Docker that the container listens on the
specified network ports at runtime. You can specify whether the port listens on
TCP or UDP, and the default is TCP if you don't specify a protocol.

The `EXPOSE` instruction doesn't actually publish the port. It functions as a
type of documentation between the person who builds the image and the person who
runs the container, about which ports are intended to be published. To
publish the port when running the container, use the `-p` flag on `docker run`
to publish and map one or more ports, or the `-P` flag to publish all exposed
ports and map them to high-order ports.

By default, `EXPOSE` assumes TCP. You can also specify UDP:

```dockerfile
EXPOSE 80/udp
```

To expose on both TCP and UDP, include two lines:

```dockerfile
EXPOSE 80/tcp
EXPOSE 80/udp
```

In this case, if you use `-P` with `docker run`, the port will be exposed once
for TCP and once for UDP. Remember that `-P` uses an ephemeral high-ordered host
port on the host, so TCP and UDP doesn't use the same port.

Regardless of the `EXPOSE` settings, you can override them at runtime by using
the `-p` flag. For example

```console
$ docker run -p 80:80/tcp -p 80:80/udp ...
```

To set up port redirection on the host system, see [using the -P flag](https://docs.docker.com/reference/cli/docker/container/run/#publish).
The `docker network` command supports creating networks for communication among
containers without the need to expose or publish specific ports, because the
containers connected to the network can communicate with each other over any
port. For detailed information, see the
[overview of this feature](https://docs.docker.com/engine/userguide/networking/).

## ENV

```dockerfile
ENV <key>=<value> [<key>=<value>...]
```

The `ENV` instruction sets the environment variable `<key>` to the value
`<value>`. This value will be in the environment for all subsequent instructions
in the build stage and can be [replaced inline](#environment-replacement) in
many as well. The value will be interpreted for other environment variables, so
quote characters will be removed if they are not escaped. Like command line parsing,
quotes and backslashes can be used to include spaces within values.

Example:

```dockerfile
ENV MY_NAME="John Doe"
ENV MY_DOG=Rex\ The\ Dog
ENV MY_CAT=fluffy
```

The `ENV` instruction allows for multiple `<key>=<value> ...` variables to be set
at one time, and the example below will yield the same net results in the final
image:

```dockerfile
ENV MY_NAME="John Doe" MY_DOG=Rex\ The\ Dog \
    MY_CAT=fluffy
```

The environment variables set using `ENV` will persist when a container is run
from the resulting image. You can view the values using `docker inspect`, and
change them using `docker run --env <key>=<value>`.

A stage inherits any environment variables that were set using `ENV` by its
parent stage or any ancestor. Refer to the [multi-stage builds section](https://docs.docker.com/build/building/multi-stage/)
in the manual for more information.

Environment variable persistence can cause unexpected side effects. For example,
setting `ENV DEBIAN_FRONTEND=noninteractive` changes the behavior of `apt-get`,
and may confuse users of your image.

If an environment variable is only needed during build, and not in the final
image, consider setting a value for a single command instead:

```dockerfile
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y ...
```

Or using [`ARG`](#arg), which is not persisted in the final image:

```dockerfile
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y ...
```

> [!NOTE]
> **Alternative syntax**
>
> The `ENV` instruction also allows an alternative syntax `ENV <key> <value>`,
> omitting the `=`. For example:
>
> ```dockerfile
> ENV MY_VAR my-value
> ```
>
> This syntax does not allow for multiple environment-variables to be set in a
> single `ENV` instruction, and can be confusing. For example, the following
> sets a single environment variable (`ONE`) with value `"TWO= THREE=world"`:
>
> ```dockerfile
> ENV ONE TWO= THREE=world
> ```
>
> The alternative syntax is supported for backward compatibility, but discouraged
> for the reasons outlined above, and may be removed in a future release.

## ADD

ADD has two forms.
The latter form is required for paths containing whitespace.

```dockerfile
ADD [OPTIONS] <src> ... <dest>
ADD [OPTIONS] ["<src>", ... "<dest>"]
```

The available `[OPTIONS]` are:

| Option                                  | Minimum Dockerfile version |
| --------------------------------------- | -------------------------- |
| [`--keep-git-dir`](#add---keep-git-dir) | 1.1                        |
| [`--checksum`](#add---checksum)         | 1.6                        |
| [`--chmod`](#add---chmod)               | 1.2                        |
| [`--chown`](#add---chown)               |                            |
| [`--link`](#add---link)                 | 1.4                        |
| [`--unpack`](#add---unpack)             | 1.17                       |
| [`--exclude`](#add---exclude)           | 1.19                       |

The `ADD` instruction copies new files or directories from `<src>` and adds
them to the filesystem of the image at the path `<dest>`. Files and directories
can be copied from the build context, a remote URL, or a Git repository.

The `ADD` and `COPY` instructions are functionally similar, but serve slightly different purposes.
Learn more about the [differences between `ADD` and `COPY`](https://docs.docker.com/build/building/best-practices/#add-or-copy).

### Source

You can specify multiple source files or directories with `ADD`. The last
argument must always be the destination. For example, to add two files,
`file1.txt` and `file2.txt`, from the build context to `/usr/src/things/` in
the build container:

```dockerfile
ADD file1.txt file2.txt /usr/src/things/
```

If you specify multiple source files, either directly or using a wildcard, then
the destination must be a directory (must end with a slash `/`).

To add files from a remote location, you can specify a URL or the address of a
Git repository as the source. For example:

```dockerfile
ADD https://example.com/archive.zip /usr/src/things/
ADD git@github.com:user/repo.git /usr/src/things/
```

BuildKit detects the type of `<src>` and processes it accordingly.

- If `<src>` is a local file or directory, the contents of the directory are
  copied to the specified destination. See [Adding files from the build context](#adding-files-from-the-build-context).
- If `<src>` is a local tar archive, it is decompressed and extracted to the
  specified destination. See [Adding local tar archives](#adding-local-tar-archives).
- If `<src>` is a URL, the contents of the URL are downloaded and placed at
  the specified destination. See [Adding files from a URL](#adding-files-from-a-url).
- If `<src>` is a Git repository, the repository is cloned to the specified
  destination. See [Adding files from a Git repository](#adding-files-from-a-git-repository).

#### Adding files from the build context

Any relative or local path that doesn't begin with a `http://`, `https://`, or
`git@` protocol prefix is considered a local file path. The local file path is
relative to the build context. For example, if the build context is the current
directory, `ADD file.txt /` adds the file at `./file.txt` to the root of the
filesystem in the build container.

Specifying a source path with a leading slash or one that navigates outside the
build context, such as `ADD ../something /something`, automatically removes any
parent directory navigation (`../`). Trailing slashes in the source path are
also disregarded, making `ADD something/ /something` equivalent to `ADD
something /something`.

If the source is a directory, the contents of the directory are copied,
including filesystem metadata. The directory itself isn't copied, only its
contents. If it contains subdirectories, these are also copied, and merged with
any existing directories at the destination. Any conflicts are resolved in
favor of the content being added, on a file-by-file basis, except if you're
trying to copy a directory onto an existing file, in which case an error is
raised.

If the source is a file, the file and its metadata are copied to the
destination. File permissions are preserved. If the source is a file and a
directory with the same name exists at the destination, an error is raised.

If you pass a Dockerfile through stdin to the build (`docker build - <
Dockerfile`), there is no build context. In this case, you can only use the
`ADD` instruction to copy remote files. You can also pass a tar archive through
stdin: (`docker build - < archive.tar`), the Dockerfile at the root of the
archive and the rest of the archive will be used as the context of the build.

##### Pattern matching

For local files, each `<src>` may contain wildcards and matching will be done
using Go's [filepath.Match](https://golang.org/pkg/path/filepath#Match) rules.

For example, to add all files and directories in the root of the build context
ending with `.png`:

```dockerfile
ADD *.png /dest/
```

In the following example, `?` is a single-character wildcard, matching e.g.
`index.js` and `index.ts`.

```dockerfile
ADD index.?s /dest/
```

When adding files or directories that contain special characters (such as `[`
and `]`), you need to escape those paths following the Golang rules to prevent
them from being treated as a matching pattern. For example, to add a file
named `arr[0].txt`, use the following;

```dockerfile
ADD arr[[]0].txt /dest/
```

#### Adding local tar archives

When using a local tar archive as the source for `ADD`, and the archive is in a
recognized compression format (`gzip`, `bzip2` or `xz`, or uncompressed), the
archive is decompressed and extracted into the specified destination. Local tar
archives are extracted by default, see the [`ADD --unpack` flag].

When a directory is extracted, it has the same behavior as `tar -x`.
The result is the union of:

1. Whatever existed at the destination path, and
2. The contents of the source tree, with conflicts resolved in favor of the
   content being added, on a file-by-file basis.

> [!NOTE]
> Whether a file is identified as a recognized compression format or not is
> done solely based on the contents of the file, not the name of the file. For
> example, if an empty file happens to end with `.tar.gz` this isn't recognized
> as a compressed file and doesn't generate any kind of decompression error
> message, rather the file will simply be copied to the destination.

#### Adding files from a URL

In the case where source is a remote file URL, the destination will have
permissions of 600. If the HTTP response contains a `Last-Modified` header, the
timestamp from that header will be used to set the `mtime` on the destination
file. However, like any other file processed during an `ADD`, `mtime` isn't
included in the determination of whether or not the file has changed and the
cache should be updated.

If remote file is a tar archive, the archive is not extracted by default. To
download and extract the archive, use the [`ADD --unpack` flag].

If the destination ends with a trailing slash, then the filename is inferred
from the URL path. For example, `ADD http://example.com/foobar /` would create
the file `/foobar`. The URL must have a nontrivial path so that an appropriate
filename can be discovered (`http://example.com` doesn't work).

If the destination doesn't end with a trailing slash, the destination path
becomes the filename of the file downloaded from the URL. For example, `ADD
http://example.com/foo /bar` creates the file `/bar`.

If your URL files are protected using authentication, you need to use `RUN wget`,
`RUN curl` or use another tool from within the container as the `ADD` instruction
doesn't support authentication.

##### Secrets

You can use the `HTTP_AUTH_HEADER_<host>` and `HTTP_AUTH_TOKEN_<host>` secrets
to set credentials for remote sources. For more information, see
[Build secrets](https://docs.docker.com/build/building/secrets/#http-authentication-for-add).

#### Adding files from a Git repository

To use a Git repository as the source for `ADD`, you can reference the
repository's HTTP or SSH address as the source. The repository is cloned to the
specified destination in the image.

```dockerfile
ADD https://github.com/user/repo.git /mydir/
```

You can use URL fragments to specify a specific branch, tag, commit, or
subdirectory. For example, to add the `docs` directory of the `v0.14.1` tag of
the `buildkit` repository:

```dockerfile
ADD git@github.com:moby/buildkit.git#v0.14.1:docs /buildkit-docs
```

For more information about Git URL fragments,
see [URL fragments](https://docs.docker.com/build/building/context/#url-fragments).

When adding from a Git repository, the permissions bits for files
are 644. If a file in the repository has the executable bit set, it will have
permissions set to 755. Directories have permissions set to 755.

When using a Git repository as the source, the repository must be accessible
from the build context. To add a repository via SSH, whether public or private,
you must pass an SSH key for authentication. For example, given the following
Dockerfile:

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
ADD git@git.example.com:foo/bar.git /bar
```

To build this Dockerfile, pass the `--ssh` flag to the `docker build` to mount
the SSH agent socket to the build. For example:

```console
$ docker build --ssh default .
```

For more information about building with secrets,
see [Build secrets](https://docs.docker.com/build/building/secrets/).

### Destination

If the destination path begins with a forward slash, it's interpreted as an
absolute path, and the source files are copied into the specified destination
relative to the root of the current build stage.

```dockerfile
# create /abs/test.txt
ADD test.txt /abs/
```

Trailing slashes are significant. For example, `ADD test.txt /abs` creates a
file at `/abs`, whereas `ADD test.txt /abs/` creates `/abs/test.txt`.

If the destination path doesn't begin with a leading slash, it's interpreted as
relative to the working directory of the build container.

```dockerfile
WORKDIR /usr/src/app
# create /usr/src/app/rel/test.txt
ADD test.txt rel/
```

If destination doesn't exist, it's created, along with all missing directories
in its path.

If the source is a file, and the destination doesn't end with a trailing slash,
the source file will be written to the destination path as a file.

### ADD --keep-git-dir

```dockerfile
ADD [--keep-git-dir=<boolean>] <src> ... <dir>
```

When `<src>` is the HTTP or SSH address of a remote Git repository,
BuildKit adds the contents of the Git repository to the image
excluding the `.git` directory by default.

The `--keep-git-dir=true` flag lets you preserve the `.git` directory.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
ADD --keep-git-dir=true https://github.com/moby/buildkit.git#v0.10.1 /buildkit
```

### ADD --checksum

```dockerfile
ADD [--checksum=<hash>] <src> ... <dir>
```

The `--checksum` flag lets you verify the checksum of a remote Git or HTTP
resource:

- For Git sources, the checksum is the commit SHA. It can be the full commit
  SHA or match on the prefix (1 or more characters).
- For HTTP sources, the checksum is the SHA-256 content digest, formatted as
  `sha256:<hash>`. SHA-256 is the only supported hash algorithm.

```dockerfile
ADD --checksum=be1f38e https://github.com/moby/buildkit.git#v0.26.2 /
ADD --checksum=sha256:24454f830cdb571e2c4ad15481119c43b3cafd48dd869a9b2945d1036d1dc68d https://mirrors.edge.kernel.org/pub/linux/kernel/Historic/linux-0.01.tar.gz /
```

### ADD --chmod

See [`COPY --chmod`](#copy---chmod).

### ADD --chown

See [`COPY --chown`](#copy---chown).

### ADD --link

See [`COPY --link`](#copy---link).

### ADD --unpack

```dockerfile
ADD [--unpack=<bool>] <src> ... <dir>
```

The `--unpack` flag controls whether or not to automatically unpack tar
archives (including compressed formats like `gzip` or `bzip2`) when adding them
to the image. Local tar archives are unpacked by default, whereas remote tar
archives (where `src` is a URL) are downloaded without unpacking.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
# Download and unpack archive.tar.gz into /download:
ADD --unpack=true https://example.com/archive.tar.gz /download
# Add local tar without unpacking:
ADD --unpack=false my-archive.tar.gz .
```

### ADD --exclude

See [`COPY --exclude`](#copy---exclude).

## COPY

COPY has two forms.
The latter form is required for paths containing whitespace.

```dockerfile
COPY [OPTIONS] <src> ... <dest>
COPY [OPTIONS] ["<src>", ... "<dest>"]
```

The available `[OPTIONS]` are:

| Option                             | Minimum Dockerfile version |
| ---------------------------------- | -------------------------- |
| [`--from`](#copy---from)           |                            |
| [`--chmod`](#copy---chmod)         | 1.2                        |
| [`--chown`](#copy---chown)         |                            |
| [`--link`](#copy---link)           | 1.4                        |
| [`--parents`](#copy---parents)     | 1.20                       |
| [`--exclude`](#copy---exclude)     | 1.19                       |

The `COPY` instruction copies new files or directories from `<src>` and adds
them to the filesystem of the image at the path `<dest>`. Files and directories
can be copied from the build context, build stage, named context, or an image.

The `ADD` and `COPY` instructions are functionally similar, but serve slightly different purposes.
Learn more about the [differences between `ADD` and `COPY`](https://docs.docker.com/build/building/best-practices/#add-or-copy).

### Source

You can specify multiple source files or directories with `COPY`. The last
argument must always be the destination. For example, to copy two files,
`file1.txt` and `file2.txt`, from the build context to `/usr/src/things/` in
the build container:

```dockerfile
COPY file1.txt file2.txt /usr/src/things/
```

If you specify multiple source files, either directly or using a wildcard, then
the destination must be a directory (must end with a slash `/`).

`COPY` accepts a flag `--from=<name>` that lets you specify the source location
to be a build stage, context, or image. The following example copies files from
a stage named `build`:

```dockerfile
FROM golang AS build
WORKDIR /app
RUN --mount=type=bind,target=. go build -o /myapp ./cmd

COPY --from=build /myapp /usr/bin/
```

For more information about copying from named sources, see the
[`--from` flag](#copy---from).

#### Copying from the build context

When copying source files from the build context, paths are interpreted as
relative to the root of the context.

Specifying a source path with a leading slash or one that navigates outside the
build context, such as `COPY ../something /something`, automatically removes
any parent directory navigation (`../`). Trailing slashes in the source path
are also disregarded, making `COPY something/ /something` equivalent to `COPY
something /something`.

If the source is a directory, the contents of the directory are copied,
including filesystem metadata. The directory itself isn't copied, only its
contents. If it contains subdirectories, these are also copied, and merged with
any existing directories at the destination. Any conflicts are resolved in
favor of the content being added, on a file-by-file basis, except if you're
trying to copy a directory onto an existing file, in which case an error is
raised.

If the source is a file, the file and its metadata are copied to the
destination. File permissions are preserved. If the source is a file and a
directory with the same name exists at the destination, an error is raised.

If you pass a Dockerfile through stdin to the build (`docker build - <
Dockerfile`), there is no build context. In this case, you can only use the
`COPY` instruction to copy files from other stages, named contexts, or images,
using the [`--from` flag](#copy---from). You can also pass a tar archive
through stdin: (`docker build - < archive.tar`), the Dockerfile at the root of
the archive and the rest of the archive will be used as the context of the
build.

When using a Git repository as the build context, the permissions bits for
copied files are 644. If a file in the repository has the executable bit set,
it will have permissions set to 755. Directories have permissions set to 755.

##### Pattern matching

For local files, each `<src>` may contain wildcards and matching will be done
using Go's [filepath.Match](https://golang.org/pkg/path/filepath#Match) rules.

For example, to add all files and directories in the root of the build context
ending with `.png`:

```dockerfile
COPY *.png /dest/
```

In the following example, `?` is a single-character wildcard, matching e.g.
`index.js` and `index.ts`.

```dockerfile
COPY index.?s /dest/
```

When adding files or directories that contain special characters (such as `[`
and `]`), you need to escape those paths following the Golang rules to prevent
them from being treated as a matching pattern. For example, to add a file
named `arr[0].txt`, use the following;

```dockerfile
COPY arr[[]0].txt /dest/
```

### Destination

If the destination path begins with a forward slash, it's interpreted as an
absolute path, and the source files are copied into the specified destination
relative to the root of the current build stage.

```dockerfile
# create /abs/test.txt
COPY test.txt /abs/
```

Trailing slashes are significant. For example, `COPY test.txt /abs` creates a
file at `/abs`, whereas `COPY test.txt /abs/` creates `/abs/test.txt`.

If the destination path doesn't begin with a leading slash, it's interpreted as
relative to the working directory of the build container.

```dockerfile
WORKDIR /usr/src/app
# create /usr/src/app/rel/test.txt
COPY test.txt rel/
```

If destination doesn't exist, it's created, along with all missing directories
in its path.

If the source is a file, and the destination doesn't end with a trailing slash,
the source file will be written to the destination path as a file.

### COPY --from

By default, the `COPY` instruction copies files from the build context. The
`COPY --from` flag lets you copy files from an image, a build stage,
or a named context instead.

```dockerfile
COPY [--from=<image|stage|context>] <src> ... <dest>
```

To copy from a build stage in a
[multi-stage build](https://docs.docker.com/build/building/multi-stage/),
specify the name of the stage you want to copy from. You specify stage names
using the `AS` keyword with the `FROM` instruction.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine AS build
COPY . .
RUN apk add clang
RUN clang -o /hello hello.c

FROM scratch
COPY --from=build /hello /
```

You can also copy files directly from named contexts (specified with
`--build-context <name>=<source>`) or images. The following example copies an
`nginx.conf` file from the official Nginx image.

```dockerfile
COPY --from=nginx:latest /etc/nginx/nginx.conf /nginx.conf
```

The source path of `COPY --from` is always resolved from filesystem root of the
image or stage that you specify.

### COPY --chmod

```dockerfile
COPY [--chmod=<perms>] <src> ... <dest>
```

The `--chmod` flag supports octal notation (e.g., `755`, `644`) and symbolic
notation (e.g., `+x`, `g=u`). Symbolic notation (added in Dockerfile version 1.14)
is useful when octal isn't flexible enough. For example, `u=rwX,go=rX` sets
directories to 755 and files to 644, while preserving the executable bit on files
that already have it. (Capital `X` means "executable only if it's a directory or
already executable.")

For more information about symbolic notation syntax, see the
[chmod(1) manual](https://man.freebsd.org/cgi/man.cgi?chmod).

Examples using octal notation:

```dockerfile
COPY --chmod=755 app.sh /app/
COPY --chmod=644 file.txt /data/
ARG MODE=440
COPY --chmod=$MODE . .
```

Examples using symbolic notation:

```dockerfile
COPY --chmod=+x script.sh /app/
COPY --chmod=u=rwX,go=rX . /app/
COPY --chmod=g=u config/ /config/
```

The `--chmod` flag is not supported when building Windows containers.

### COPY --chown

```dockerfile
COPY [--chown=<user>:<group>] <src> ... <dest>
```

Sets ownership of copied files. Without this flag, files are created with UID
and GID of 0.

The flag accepts usernames, group names, UIDs, or GIDs in any combination.
If you specify only a user, the GID is set to the same numeric value as the UID.

```dockerfile
COPY --chown=55:mygroup files* /somedir/
COPY --chown=bin files* /somedir/
COPY --chown=1 files* /somedir/
COPY --chown=10:11 files* /somedir/
COPY --chown=myuser:mygroup --chmod=644 files* /somedir/
```

When using names instead of numeric IDs, BuildKit resolves them using
`/etc/passwd` and `/etc/group` in the container's root filesystem. If these
files are missing or don't contain the specified names, the build fails.
Numeric IDs don't require this lookup.

The `--chown` flag is not supported when building Windows containers.

### COPY --link

```dockerfile
COPY [--link[=<boolean>]] <src> ... <dest>
```

Enabling this flag in `COPY` or `ADD` commands allows you to copy files with
enhanced semantics where your files remain independent on their own layer and
don't get invalidated when commands on previous layers are changed.

When `--link` is used your source files are copied into an empty destination
directory. That directory is turned into a layer that is linked on top of your
previous state.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
COPY --link /foo /bar
```

Is equivalent of doing two builds:

```dockerfile
FROM alpine
```

and

```dockerfile
FROM scratch
COPY /foo /bar
```

and merging all the layers of both images together.

#### Benefits of using `--link`

Use `--link` to reuse already built layers in subsequent builds with
`--cache-from` even if the previous layers have changed. This is especially
important for multi-stage builds where a `COPY --from` statement would
previously get invalidated if any previous commands in the same stage changed,
causing the need to rebuild the intermediate stages again. With `--link` the
layer the previous build generated is reused and merged on top of the new
layers. This also means you can easily rebase your images when the base images
receive updates, without having to execute the whole build again. In backends
that support it, BuildKit can do this rebase action without the need to push or
pull any layers between the client and the registry. BuildKit will detect this
case and only create new image manifest that contains the new layers and old
layers in correct order.

The same behavior where BuildKit can avoid pulling down the base image can also
happen when using `--link` and no other commands that would require access to
the files in the base image. In that case BuildKit will only build the layers
for the `COPY` commands and push them to the registry directly on top of the
layers of the base image.

#### Incompatibilities with `--link=false`

When using `--link` the `COPY/ADD` commands are not allowed to read any files
from the previous state. This means that if in previous state the destination
directory was a path that contained a symlink, `COPY/ADD` can not follow it.
In the final image the destination path created with `--link` will always be a
path containing only directories.

If you don't rely on the behavior of following symlinks in the destination
path, using `--link` is always recommended. The performance of `--link` is
equivalent or better than the default behavior and, it creates much better
conditions for cache reuse.

When copying a path into a subdirectory, `--link` will always copy from the
root of the filesystem. When copying a directory, the existing mode is
overridden with the new mode from the copied path. If you need a specific mode
for a directory, such as the more permissive `/tmp` directory, you may need to
either avoid using `--link`, unroll the copy into its base components, or use
`--chmod` to ensure the overwriting directory contains the same permissions.

### COPY --parents

```dockerfile
COPY [--parents[=<boolean>]] <src> ... <dest>
```

The `--parents` flag preserves parent directories for `src` entries. This flag defaults to `false`.

```dockerfile
# syntax=docker/dockerfile:1
FROM scratch

COPY ./x/a.txt ./y/a.txt /no_parents/
COPY --parents ./x/a.txt ./y/a.txt /parents/

# /no_parents/a.txt
# /parents/x/a.txt
# /parents/y/a.txt
```

This behavior is similar to the [Linux `cp` utility's](https://www.man7.org/linux/man-pages/man1/cp.1.html)
`--parents` or [`rsync`](https://man7.org/linux/man-pages/man1/rsync.1.html) `--relative` flag.

As with Rsync, it is possible to limit which parent directories are preserved by
inserting a dot and a slash (`./`) into the source path. If such point exists, only parent
directories after it will be preserved. This may be especially useful copies between stages
with `--from` where the source paths need to be absolute.

```dockerfile
# syntax=docker/dockerfile:1
FROM scratch

COPY --parents ./x/./y/*.txt /parents/

# Build context:
# ./x/y/a.txt
# ./x/y/b.txt
#
# Output:
# /parents/y/a.txt
# /parents/y/b.txt
```

The `**` wildcard matches any number of path components, including none, and
can be used to recursively match files across directory levels:

```dockerfile
# syntax=docker/dockerfile:1
FROM scratch

COPY --parents ./src/**/*.txt /parents/

# Build context:
# ./src/a.txt
# ./src/x/b.txt
# ./src/x/y/c.txt
#
# Output:
# /parents/src/a.txt
# /parents/src/x/b.txt
# /parents/src/x/y/c.txt
```

Note that, without the `--parents` flag specified, any filename collision will
fail the Linux `cp` operation with an explicit error message
(`cp: will not overwrite just-created './x/a.txt' with './y/a.txt'`), where the
Buildkit will silently overwrite the target file at the destination.

While it is possible to preserve the directory structure for `COPY`
instructions consisting of only one `src` entry, usually it is more beneficial
to keep the layer count in the resulting image as low as possible. Therefore,
with the `--parents` flag, the Buildkit is capable of packing multiple
`COPY` instructions together, keeping the directory structure intact.

### COPY --exclude

```dockerfile
COPY [--exclude=<path> ...] <src> ... <dest>
```

The `--exclude` flag lets you specify a path expression for files to be excluded.

The path expression follows the same format as `<src>`,
supporting wildcards and matching using Go's
[filepath.Match](https://golang.org/pkg/path/filepath#Match) rules.
For example, to add all files starting with "hom", excluding files with a `.txt` extension:

```dockerfile
# syntax=docker/dockerfile:1
FROM scratch

COPY --exclude=*.txt hom* /mydir/
```

You can specify the `--exclude` option multiple times for a `COPY` instruction.
Files matching any of the specified `--exclude` patterns are not copied,
even if their paths match the pattern specified in `<src>`.
To add all files starting with "hom", excluding files with either `.txt` or `.md` extensions:

```dockerfile
# syntax=docker/dockerfile:1
FROM scratch

COPY --exclude=*.txt --exclude=*.md hom* /mydir/
```

## ENTRYPOINT

An `ENTRYPOINT` allows you to configure a container that will run as an executable.

`ENTRYPOINT` has two possible forms:

- The exec form, which is the preferred form:

  ```dockerfile
  ENTRYPOINT ["executable", "param1", "param2"]
  ```

- The shell form:

  ```dockerfile
  ENTRYPOINT command param1 param2
  ```

For more information about the different forms, see [Shell and exec form](#shell-and-exec-form).

The following command starts a container from the `nginx` with its default
content, listening on port 80:

```console
$ docker run -i -t --rm -p 80:80 nginx
```

Command line arguments to `docker run <image>` will be appended after all
elements in an exec form `ENTRYPOINT`, and will override all elements specified
using `CMD`.

This allows arguments to be passed to the entry point, i.e., `docker run
<image> -d` will pass the `-d` argument to the entry point. You can override
the `ENTRYPOINT` instruction using the `docker run --entrypoint` flag.

The shell form of `ENTRYPOINT` ignores any `CMD` or `docker run` command line
arguments. It also starts your `ENTRYPOINT` as a subcommand of `/bin/sh -c`,
which does not pass signals. This means that the executable will not be the
container's `PID 1`, and will not receive Unix signals. In this case, your
executable doesn't receive a `SIGTERM` from `docker stop <container>`.

Only the last `ENTRYPOINT` instruction in the Dockerfile will have an effect.

### Exec form ENTRYPOINT example

You can use the exec form of `ENTRYPOINT` to set fairly stable default commands
and arguments and then use `CMD` to set additional defaults that are more
likely to be changed.

When combining exec form `ENTRYPOINT` with `CMD`, use the exec form of `CMD`
as well. Using the shell form of `CMD` causes it to be wrapped in
`/bin/sh -c`, which means the `ENTRYPOINT` receives a shell invocation as its
argument rather than the bare command and parameters. See
[Understand how CMD and ENTRYPOINT interact](#understand-how-cmd-and-entrypoint-interact).

```dockerfile
FROM ubuntu
ENTRYPOINT ["top", "-b"]
CMD ["-c"]
```

When you run the container, you can see that `top` is the only process:

```console
$ docker run -it --rm --name test  top -H

top - 08:25:00 up  7:27,  0 users,  load average: 0.00, 0.01, 0.05
Threads:   1 total,   1 running,   0 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.1 us,  0.1 sy,  0.0 ni, 99.7 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
KiB Mem:   2056668 total,  1616832 used,   439836 free,    99352 buffers
KiB Swap:  1441840 total,        0 used,  1441840 free.  1324440 cached Mem

  PID USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
    1 root      20   0   19744   2336   2080 R  0.0  0.1   0:00.04 top
```

To examine the result further, you can use `docker exec`:

```console
$ docker exec -it test ps aux

USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  2.6  0.1  19752  2352 ?        Ss+  08:24   0:00 top -b -H
root         7  0.0  0.1  15572  2164 ?        R+   08:25   0:00 ps aux
```

And you can gracefully request `top` to shut down using `docker stop test`.

The following Dockerfile shows using the `ENTRYPOINT` to run Apache in the
foreground (i.e., as `PID 1`):

```dockerfile
FROM debian:stable
RUN apt-get update && apt-get install -y --force-yes apache2
EXPOSE 80 443
VOLUME ["/var/www", "/var/log/apache2", "/etc/apache2"]
ENTRYPOINT ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
```

If you need to write a starter script for a single executable, you can ensure that
the final executable receives the Unix signals by using `exec` and `gosu`
commands:

```bash
#!/usr/bin/env bash
set -e

if [ "$1" = 'postgres' ]; then
    chown -R postgres "$PGDATA"

    if [ -z "$(ls -A "$PGDATA")" ]; then
        gosu postgres initdb
    fi

    exec gosu postgres "$@"
fi

exec "$@"
```

Lastly, if you need to do some extra cleanup (or communicate with other containers)
on shutdown, or are co-ordinating more than one executable, you may need to ensure
that the `ENTRYPOINT` script receives the Unix signals, passes them on, and then
does some more work:

```bash
#!/bin/sh
# Note: I've written this using sh so it works in the busybox container too

# USE the trap if you need to also do manual cleanup after the service is stopped,
#     or need to start multiple services in the one container
trap "echo TRAPed signal" HUP INT QUIT TERM

# start service in background here
/usr/sbin/apachectl start

echo "[hit enter key to exit] or run 'docker stop <container>'"
read

# stop service and clean up here
echo "stopping apache"
/usr/sbin/apachectl stop

echo "exited $0"
```

If you run this image with `docker run -it --rm -p 80:80 --name test apache`,
you can then examine the container's processes with `docker exec`, or `docker top`,
and then ask the script to stop Apache:

```console
$ docker exec -it test ps aux

USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.1  0.0   4448   692 ?        Ss+  00:42   0:00 /bin/sh /run.sh 123 cmd cmd2
root        19  0.0  0.2  71304  4440 ?        Ss   00:42   0:00 /usr/sbin/apache2 -k start
www-data    20  0.2  0.2 360468  6004 ?        Sl   00:42   0:00 /usr/sbin/apache2 -k start
www-data    21  0.2  0.2 360468  6000 ?        Sl   00:42   0:00 /usr/sbin/apache2 -k start
root        81  0.0  0.1  15572  2140 ?        R+   00:44   0:00 ps aux

$ docker top test

PID                 USER                COMMAND
10035               root                {run.sh} /bin/sh /run.sh 123 cmd cmd2
10054               root                /usr/sbin/apache2 -k start
10055               33                  /usr/sbin/apache2 -k start
10056               33                  /usr/sbin/apache2 -k start

$ /usr/bin/time docker stop test

test
real	0m 0.27s
user	0m 0.03s
sys	0m 0.03s
```

> [!NOTE]
> You can override the `ENTRYPOINT` setting using `--entrypoint`,
> but this can only set the binary to exec (no `sh -c` will be used).

### Shell form ENTRYPOINT example

You can specify a plain string for the `ENTRYPOINT` and it will execute in `/bin/sh -c`.
This form will use shell processing to substitute shell environment variables,
and will ignore any `CMD` or `docker run` command line arguments.
To ensure that `docker stop` will signal any long running `ENTRYPOINT` executable
correctly, you need to remember to start it with `exec`:

```dockerfile
FROM ubuntu
ENTRYPOINT exec top -b
```

When you run this image, you'll see the single `PID 1` process:

```console
$ docker run -it --rm --name test top

Mem: 1704520K used, 352148K free, 0K shrd, 0K buff, 140368121167873K cached
CPU:   5% usr   0% sys   0% nic  94% idle   0% io   0% irq   0% sirq
Load average: 0.08 0.03 0.05 2/98 6
  PID  PPID USER     STAT   VSZ %VSZ %CPU COMMAND
    1     0 root     R     3164   0%   0% top -b
```

Which exits cleanly on `docker stop`:

```console
$ /usr/bin/time docker stop test

test
real	0m 0.20s
user	0m 0.02s
sys	0m 0.04s
```

If you forget to add `exec` to the beginning of your `ENTRYPOINT`:

```dockerfile
FROM ubuntu
ENTRYPOINT top -b
CMD -- --ignored-param1
```

You can then run it (giving it a name for the next step):

```console
$ docker run -it --name test top --ignored-param2

top - 13:58:24 up 17 min,  0 users,  load average: 0.00, 0.00, 0.00
Tasks:   2 total,   1 running,   1 sleeping,   0 stopped,   0 zombie
%Cpu(s): 16.7 us, 33.3 sy,  0.0 ni, 50.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st
MiB Mem :   1990.8 total,   1354.6 free,    231.4 used,    404.7 buff/cache
MiB Swap:   1024.0 total,   1024.0 free,      0.0 used.   1639.8 avail Mem

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    1 root      20   0    2612    604    536 S   0.0   0.0   0:00.02 sh
    6 root      20   0    5956   3188   2768 R   0.0   0.2   0:00.00 top
```

You can see from the output of `top` that the specified `ENTRYPOINT` is not `PID 1`.

If you then run `docker stop test`, the container will not exit cleanly - the
`stop` command will be forced to send a `SIGKILL` after the timeout:

```console
$ docker exec -it test ps waux

USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.4  0.0   2612   604 pts/0    Ss+  13:58   0:00 /bin/sh -c top -b --ignored-param2
root         6  0.0  0.1   5956  3188 pts/0    S+   13:58   0:00 top -b
root         7  0.0  0.1   5884  2816 pts/1    Rs+  13:58   0:00 ps waux

$ /usr/bin/time docker stop test

test
real	0m 10.19s
user	0m 0.04s
sys	0m 0.03s
```

### Understand how CMD and ENTRYPOINT interact

Both `CMD` and `ENTRYPOINT` instructions define what command gets executed when running a container.
There are few rules that describe their co-operation.

1. Dockerfile should specify at least one of `CMD` or `ENTRYPOINT` commands.

2. `ENTRYPOINT` should be defined when using the container as an executable.

3. `CMD` should be used as a way of defining default arguments for an `ENTRYPOINT` command
   or for executing an ad-hoc command in a container.

4. `CMD` will be overridden when running the container with alternative arguments.

The table below shows what command is executed for different `ENTRYPOINT` / `CMD` combinations:

|                                | No ENTRYPOINT              | ENTRYPOINT exec_entry p1_entry | ENTRYPOINT ["exec_entry", "p1_entry"]          |
| :----------------------------- | :------------------------- | :----------------------------- | :--------------------------------------------- |
| **No CMD**                     | error, not allowed         | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry                            |
| **CMD ["exec_cmd", "p1_cmd"]** | exec_cmd p1_cmd            | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry exec_cmd p1_cmd            |
| **CMD exec_cmd p1_cmd**        | /bin/sh -c exec_cmd p1_cmd | /bin/sh -c exec_entry p1_entry | exec_entry p1_entry /bin/sh -c exec_cmd p1_cmd |

> [!NOTE]
> If `CMD` is defined from the base image, setting `ENTRYPOINT` will
> reset `CMD` to an empty value. In this scenario, `CMD` must be defined in the
> current image to have a value.

## VOLUME

```dockerfile
VOLUME ["/data"]
```

The `VOLUME` instruction creates a mount point with the specified name
and marks it as holding externally mounted volumes from native host or other
containers. The value can be a JSON array, `VOLUME ["/var/log/"]`, or a plain
string with multiple arguments, such as `VOLUME /var/log` or `VOLUME /var/log
/var/db`. For more information/examples and mounting instructions via the
Docker client, refer to
[_Share Directories via Volumes_](https://docs.docker.com/storage/volumes/)
documentation.

The `docker run` command initializes the newly created volume with any data
that exists at the specified location within the base image. For example,
consider the following Dockerfile snippet:

```dockerfile
FROM ubuntu
RUN mkdir /myvol
RUN echo "hello world" > /myvol/greeting
VOLUME /myvol
```

This Dockerfile results in an image that causes `docker run` to
create a new mount point at `/myvol` and copy the `greeting` file
into the newly created volume.

### Notes about specifying volumes

Keep the following things in mind about volumes in the Dockerfile.

- **Volumes on Windows-based containers**: When using Windows-based containers,
  the destination of a volume inside the container must be one of:

  - a non-existing or empty directory
  - a drive other than `C:`

- **Changing the volume from within the Dockerfile**: If any build steps change the
  data within the volume after it has been declared, those changes will be discarded
  when using the legacy builder. When using Buildkit, the changes will instead be kept.

- **JSON formatting**: The list is parsed as a JSON array.
  You must enclose words with double quotes (`"`) rather than single quotes (`'`).

- **The host directory is declared at container run-time**: The host directory
  (the mountpoint) is, by its nature, host-dependent. This is to preserve image
  portability, since a given host directory can't be guaranteed to be available
  on all hosts. For this reason, you can't mount a host directory from
  within the Dockerfile. The `VOLUME` instruction does not support specifying a `host-dir`
  parameter. You must specify the mountpoint when you create or run the container.

## USER

```dockerfile
USER <user>[:<group>]
```

or

```dockerfile
USER <UID>[:<GID>]
```

The `USER` instruction sets the user name (or UID) and optionally the user
group (or GID) to use as the default user and group for the remainder of the
current stage. The specified user is used for `RUN` instructions and at
runtime runs the relevant `ENTRYPOINT` and `CMD` commands.

> Note that when specifying a group for the user, the user will have _only_ the
> specified group membership. Any other configured group memberships will be ignored.

> [!WARNING]
> When the user doesn't have a primary group then the image (or the next
> instructions) will be run with the `root` group.
>
> On Windows, the user must be created first if it's not a built-in account.
> This can be done with the `net user` command called as part of a Dockerfile.

```dockerfile
FROM microsoft/windowsservercore
# Create Windows user in the container
RUN net user /add patrick
# Set it for subsequent commands
USER patrick
```

## WORKDIR

```dockerfile
WORKDIR /path/to/workdir
```

The `WORKDIR` instruction sets the working directory for any `RUN`, `CMD`,
`ENTRYPOINT`, `COPY` and `ADD` instructions that follow it in the Dockerfile.
If the `WORKDIR` doesn't exist, it will be created even if it's not used in any
subsequent Dockerfile instruction.

The `WORKDIR` instruction can be used multiple times in a Dockerfile. If a
relative path is provided, it will be relative to the path of the previous
`WORKDIR` instruction. For example:

```dockerfile
WORKDIR /a
WORKDIR b
WORKDIR c
RUN pwd
```

The output of the final `pwd` command in this Dockerfile would be `/a/b/c`.

The `WORKDIR` instruction can resolve environment variables previously set using
`ENV`. You can only use environment variables explicitly set in the Dockerfile.
For example:

```dockerfile
ENV DIRPATH=/path
WORKDIR $DIRPATH/$DIRNAME
RUN pwd
```

The output of the final `pwd` command in this Dockerfile would be
`/path/$DIRNAME`

If not specified, the default working directory is `/`. In practice, if you aren't building a Dockerfile from scratch (`FROM scratch`),
the `WORKDIR` may likely be set by the base image you're using.

Therefore, to avoid unintended operations in unknown directories, it's best practice to set your `WORKDIR` explicitly.

## ARG

```dockerfile
ARG <name>[=<default value>] [<name>[=<default value>]...]
```

The `ARG` instruction defines a variable that users can pass at build time to
the builder with the `docker build` command using the `--build-arg <varname>=<value>`
flag. This variable can be used in subsequent instructions such as `FROM`, `ENV`,
`WORKDIR`, and others using the `${VAR}` or `$VAR` template syntax.
It is also passed to all subsequent `RUN` instructions as a build-time
environment variable.

Unlike `ENV`, an `ARG` variable is not embedded in the image and is not available
in the final container.

> [!WARNING]
> It isn't recommended to use build arguments for passing secrets such as
> user credentials, API tokens, etc. Build arguments are visible in the
> `docker history` command and in `max` mode provenance attestations,
> which are attached to the image by default if you use the Buildx GitHub Actions
> and your GitHub repository is public.
>
> Refer to the [`RUN --mount=type=secret`](#run---mounttypesecret) section to
> learn about secure ways to use secrets when building images.

A Dockerfile may include one or more `ARG` instructions. For example,
the following is a valid Dockerfile:

```dockerfile
FROM busybox
ARG user1
ARG buildno
# ...
```

### Default values

An `ARG` instruction can optionally include a default value:

```dockerfile
FROM busybox
ARG user1=someuser
ARG buildno=1
# ...
```

If an `ARG` instruction has a default value and if there is no value passed
at build-time, the builder uses the default.

### Scope

An `ARG` variable comes into effect from the line on which it is declared in
the Dockerfile. For example, consider this Dockerfile:

```dockerfile
FROM busybox
USER ${username:-some_user}
ARG username
USER $username
# ...
```

A user builds this file by calling:

```console
$ docker build --build-arg username=what_user .
```

- The `USER` instruction on line 2 evaluates to the `some_user` fallback,
  because the `username` variable is not yet declared.
- The `username` variable is declared on line 3, and available for reference in
  Dockerfile instruction from that point onwards.
- The `USER` instruction on line 4 evaluates to `what_user`, since at that
  point the `username` argument has a value of `what_user` which was passed on
  the command line. Prior to its definition by an `ARG` instruction, any use of
  a variable results in an empty string.

An `ARG` variable declared within a build stage is automatically inherited by
other stages based on that stage. Unrelated build stages do not have access to
the variable. To use an argument in multiple distinct stages, each stage must
include the `ARG` instruction, or they must both be based on a shared base
stage in the same Dockerfile where the variable is declared.

For more information, refer to [variable scoping](https://docs.docker.com/build/building/variables/#scoping).

### Using ARG variables

You can use an `ARG` or an `ENV` instruction to specify variables that are
available to the `RUN` instruction. Environment variables defined using the
`ENV` instruction always override an `ARG` instruction of the same name. Consider
this Dockerfile with an `ENV` and `ARG` instruction.

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
ENV CONT_IMG_VER=v1.0.0
RUN echo $CONT_IMG_VER
```

Then, assume this image is built with this command:

```console
$ docker build --build-arg CONT_IMG_VER=v2.0.1 .
```

In this case, the `RUN` instruction uses `v1.0.0` instead of the `ARG` setting
passed by the user:`v2.0.1` This behavior is similar to a shell
script where a locally scoped variable overrides the variables passed as
arguments or inherited from environment, from its point of definition.

Using the example above but a different `ENV` specification you can create more
useful interactions between `ARG` and `ENV` instructions:

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
ENV CONT_IMG_VER=${CONT_IMG_VER:-v1.0.0}
RUN echo $CONT_IMG_VER
```

Unlike an `ARG` instruction, `ENV` values are always persisted in the built
image. Consider a docker build without the `--build-arg` flag:

```console
$ docker build .
```

Using this Dockerfile example, `CONT_IMG_VER` is still persisted in the image but
its value would be `v1.0.0` as it is the default set in line 3 by the `ENV` instruction.

The variable expansion technique in this example allows you to pass arguments
from the command line and persist them in the final image by leveraging the
`ENV` instruction. Variable expansion is only supported for [a limited set of
Dockerfile instructions.](#environment-replacement)

### Predefined ARGs

Docker has a set of predefined `ARG` variables that you can use without a
corresponding `ARG` instruction in the Dockerfile.

- `HTTP_PROXY`
- `http_proxy`
- `HTTPS_PROXY`
- `https_proxy`
- `FTP_PROXY`
- `ftp_proxy`
- `NO_PROXY`
- `no_proxy`
- `ALL_PROXY`
- `all_proxy`

To use these, pass them on the command line using the `--build-arg` flag, for
example:

```console
$ docker build --build-arg HTTPS_PROXY=https://my-proxy.example.com .
```

By default, these pre-defined variables are excluded from the output of
`docker history`. Excluding them reduces the risk of accidentally leaking
sensitive authentication information in an `HTTP_PROXY` variable.

For example, consider building the following Dockerfile using
`--build-arg HTTP_PROXY=http://user:pass@proxy.lon.example.com`

```dockerfile
FROM ubuntu
RUN echo "Hello World"
```

In this case, the value of the `HTTP_PROXY` variable is not available in the
`docker history` and is not cached. If you were to change location, and your
proxy server changed to `http://user:pass@proxy.sfo.example.com`, a subsequent
build does not result in a cache miss.

If you need to override this behaviour then you may do so by adding an `ARG`
statement in the Dockerfile as follows:

```dockerfile
FROM ubuntu
ARG HTTP_PROXY
RUN echo "Hello World"
```

When building this Dockerfile, the `HTTP_PROXY` is preserved in the
`docker history`, and changing its value invalidates the build cache.

### Automatic platform ARGs in the global scope

This feature is only available when using the [BuildKit](https://docs.docker.com/build/buildkit/)
backend.

BuildKit supports a predefined set of `ARG` variables with information on the platform of
the node performing the build (build platform) and on the platform of the
resulting image (target platform). The target platform can be specified with
the `--platform` flag on `docker build`.

The following `ARG` variables are set automatically:

- `TARGETPLATFORM` - platform of the build result. Eg `linux/amd64`, `linux/arm/v7`, `windows/amd64`.
- `TARGETOS` - OS component of TARGETPLATFORM
- `TARGETARCH` - architecture component of TARGETPLATFORM
- `TARGETVARIANT` - variant component of TARGETPLATFORM
- `BUILDPLATFORM` - platform of the node performing the build.
- `BUILDOS` - OS component of BUILDPLATFORM
- `BUILDARCH` - architecture component of BUILDPLATFORM
- `BUILDVARIANT` - variant component of BUILDPLATFORM

These arguments are defined in the global scope so are not automatically
available inside build stages or for your `RUN` commands. To expose one of
these arguments inside the build stage redefine it without value.

For example:

```dockerfile
FROM alpine
ARG TARGETPLATFORM
RUN echo "I'm building for $TARGETPLATFORM"
```

### BuildKit built-in build args

| Arg                             | Type   | Description                                                                                                                                                                                                      |
|---------------------------------|--------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `BUILDKIT_BUILD_NAME`           | String | Override the build name shown in [`buildx history` command](https://docs.docker.com/reference/cli/docker/buildx/history/) and [Docker Desktop Builds view](https://docs.docker.com/desktop/use-desktop/builds/). |
| `BUILDKIT_CACHE_MOUNT_NS`       | String | Set optional cache ID namespace.                                                                                                                                                                                 |
| `BUILDKIT_CONTEXT_KEEP_GIT_DIR` | Bool   | Trigger Git context to keep the `.git` directory.                                                                                                                                                                |
| `BUILDKIT_INLINE_CACHE`[^2]     | Bool   | Inline cache metadata to image config or not.                                                                                                                                                                    |
| `BUILDKIT_MULTI_PLATFORM`       | Bool   | Opt into deterministic output regardless of multi-platform output or not.                                                                                                                                        |
| `BUILDKIT_SANDBOX_HOSTNAME`     | String | Set the hostname (default `buildkitsandbox`)                                                                                                                                                                     |
| `BUILDKIT_SYNTAX`               | String | Set frontend image. Set to `dockerfile.v0` to ignore the Dockerfile `# syntax=` directive and use the built-in frontend instead.                                                                                 |
| `SOURCE_DATE_EPOCH`             | Int    | Set the Unix timestamp for created image and layers. More info from [reproducible builds](https://reproducible-builds.org/docs/source-date-epoch/). Supported since Dockerfile 1.5, BuildKit 0.11                |

#### Example: keep `.git` dir

When using a Git context, `.git` dir is not kept on checkouts. It can be
useful to keep it around if you want to retrieve git information during
your build:

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
WORKDIR /src
RUN --mount=target=. \
  make REVISION=$(git rev-parse HEAD) build
```

```console
$ docker build --build-arg BUILDKIT_CONTEXT_KEEP_GIT_DIR=1 https://github.com/user/repo.git#main
```

### Impact on build caching

`ARG` variables are not persisted into the built image as `ENV` variables are.
However, `ARG` variables do impact the build cache in similar ways. If a
Dockerfile defines an `ARG` variable whose value is different from a previous
build, then a "cache miss" occurs upon its first usage, not its definition. In
particular, all `RUN` instructions following an `ARG` instruction use the `ARG`
variable implicitly (as an environment variable), thus can cause a cache miss.
All predefined `ARG` variables are exempt from caching unless there is a
matching `ARG` statement in the Dockerfile.

For example, consider these two Dockerfile:

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
RUN echo $CONT_IMG_VER
```

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
RUN echo hello
```

If you specify `--build-arg CONT_IMG_VER=<value>` on the command line, in both
cases, the specification on line 2 doesn't cause a cache miss; line 3 does
cause a cache miss. `ARG CONT_IMG_VER` causes the `RUN` line to be identified
as the same as running `CONT_IMG_VER=<value> echo hello`, so if the `<value>`
changes, you get a cache miss.

Consider another example under the same command line:

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
ENV CONT_IMG_VER=$CONT_IMG_VER
RUN echo $CONT_IMG_VER
```

In this example, the cache miss occurs on line 3. The miss happens because
the variable's value in the `ENV` references the `ARG` variable and that
variable is changed through the command line. In this example, the `ENV`
command causes the image to include the value.

If an `ENV` instruction overrides an `ARG` instruction of the same name, like
this Dockerfile:

```dockerfile
FROM ubuntu
ARG CONT_IMG_VER
ENV CONT_IMG_VER=hello
RUN echo $CONT_IMG_VER
```

Line 3 doesn't cause a cache miss because the value of `CONT_IMG_VER` is a
constant (`hello`). As a result, the environment variables and values used on
the `RUN` (line 4) doesn't change between builds.

## ONBUILD

```dockerfile
ONBUILD <INSTRUCTION>
```

The `ONBUILD` instruction adds to the image a trigger instruction to
be executed at a later time, when the image is used as the base for
another build. The trigger will be executed in the context of the
downstream build, as if it had been inserted immediately after the
`FROM` instruction in the downstream Dockerfile.

This is useful if you are building an image which will be used as a base
to build other images, for example an application build environment or a
daemon which may be customized with user-specific configuration.

For example, if your image is a reusable Python application builder, it
will require application source code to be added in a particular
directory, and it might require a build script to be called after
that. You can't just call `ADD` and `RUN` now, because you don't yet
have access to the application source code, and it will be different for
each application build. You could simply provide application developers
with a boilerplate Dockerfile to copy-paste into their application, but
that's inefficient, error-prone and difficult to update because it
mixes with application-specific code.

The solution is to use `ONBUILD` to register advance instructions to
run later, during the next build stage.

Here's how it works:

1. When it encounters an `ONBUILD` instruction, the builder adds a
   trigger to the metadata of the image being built. The instruction
   doesn't otherwise affect the current build.
2. At the end of the build, a list of all triggers is stored in the
   image manifest, under the key `OnBuild`. They can be inspected with
   the `docker inspect` command.
3. Later the image may be used as a base for a new build, using the
   `FROM` instruction. As part of processing the `FROM` instruction,
   the downstream builder looks for `ONBUILD` triggers, and executes
   them in the same order they were registered. If any of the triggers
   fail, the `FROM` instruction is aborted which in turn causes the
   build to fail. If all triggers succeed, the `FROM` instruction
   completes and the build continues as usual.
4. Triggers are cleared from the final image after being executed. In
   other words they aren't inherited by "grand-children" builds.

For example you might add something like this:

```dockerfile
ONBUILD ADD . /app/src
ONBUILD RUN /usr/local/bin/python-build --dir /app/src
```

### Copy or mount from stage, image, or context

As of Dockerfile syntax 1.11, you can use `ONBUILD` with instructions that copy
or mount files from other stages, images, or build contexts. For example:

```dockerfile
# syntax=docker/dockerfile:1.11
FROM alpine AS baseimage
ONBUILD COPY --from=build /usr/bin/app /app
ONBUILD RUN --mount=from=config,target=/opt/appconfig ...
```

If the source of `from` is a build stage, the stage must be defined in the
Dockerfile where `ONBUILD` gets triggered. If it's a named context, that
context must be passed to the downstream build.

### ONBUILD limitations

- Chaining `ONBUILD` instructions using `ONBUILD ONBUILD` isn't allowed.
- The `ONBUILD` instruction may not trigger `FROM` or `MAINTAINER` instructions.

## STOPSIGNAL

```dockerfile
STOPSIGNAL signal
```

The `STOPSIGNAL` instruction sets the system call signal that will be sent to the
container to exit. This signal can be a signal name in the format `SIG<NAME>`,
for instance `SIGKILL`, or an unsigned number that matches a position in the
kernel's syscall table, for instance `9`. The default is `SIGTERM` if not
defined.

`STOPSIGNAL` applies to the signal sent by `docker stop` (and by the Docker
daemon when stopping a container). It does not affect signals sent by keyboard
shortcuts such as Ctrl+C, which sends `SIGINT` directly to the process
regardless of the `STOPSIGNAL` setting.

The image's default stopsignal can be overridden per container, using the
`--stop-signal` flag on `docker run` and `docker create`.

## HEALTHCHECK

The `HEALTHCHECK` instruction has two forms:

- `HEALTHCHECK [OPTIONS] CMD command` (check container health by running a command inside the container)
- `HEALTHCHECK NONE` (disable any healthcheck inherited from the base image)

The `HEALTHCHECK` instruction tells Docker how to test a container to check that
it's still working. This can detect cases such as a web server stuck in
an infinite loop and unable to handle new connections, even though the server
process is still running.

When a container has a healthcheck specified, it has a health status in
addition to its normal status. This status is initially `starting`. Whenever a
health check passes, it becomes `healthy` (whatever state it was previously in).
After a certain number of consecutive failures, it becomes `unhealthy`.

The options that can appear before `CMD` are:

- `--interval=DURATION` (default: `30s`)
- `--timeout=DURATION` (default: `30s`)
- `--start-period=DURATION` (default: `0s`)
- `--start-interval=DURATION` (default: `5s`)
- `--retries=N` (default: `3`)

The health check will first run **interval** seconds after the container is
started, and then again **interval** seconds after each previous check completes.
During the **start period**, health checks run at **start interval** frequency
instead.

If a single run of the check takes longer than **timeout** seconds then the check
is considered to have failed. The process performing the check is abruptly stopped
with a `SIGKILL`.

It takes **retries** consecutive failures of the health check for the container
to be considered `unhealthy`.

**start period** provides initialization time for containers that need time to bootstrap.
Probe failure during that period will not be counted towards the maximum number of retries.
However, if a health check succeeds during the start period, the container is considered
started and all consecutive failures will be counted towards the maximum number of retries.

**start interval** is the time between health checks during the start period.
This option requires Docker Engine version 25.0 or later.

There can only be one `HEALTHCHECK` instruction in a Dockerfile. If you list
more than one then only the last `HEALTHCHECK` will take effect.

The command after the `CMD` keyword can be either a shell command (e.g. `HEALTHCHECK
CMD /bin/check-running`) or an exec array (as with other Dockerfile commands;
see e.g. `ENTRYPOINT` for details).

The command's exit status indicates the health status of the container.
The possible values are:

- 0: success - the container is healthy and ready for use
- 1: unhealthy - the container isn't working correctly
- 2: reserved - don't use this exit code

For example, to check every five minutes or so that a web-server is able to
serve the site's main page within three seconds:

```dockerfile
HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost/ || exit 1
```

To help debug failing probes, any output text (UTF-8 encoded) that the command writes
on stdout or stderr will be stored in the health status and can be queried with
`docker inspect`. Such output should be kept short (only the first 4096 bytes
are stored currently).

When the health status of a container changes, a `health_status` event is
generated with the new status.

## SHELL

```dockerfile
SHELL ["executable", "parameters"]
```

The `SHELL` instruction allows the default shell used for the shell form of
commands to be overridden. The default shell on Linux is `["/bin/sh", "-c"]`, and on
Windows is `["cmd", "/S", "/C"]`. The `SHELL` instruction must be written in JSON
form in a Dockerfile.

The `SHELL` instruction is particularly useful on Windows where there are
two commonly used and quite different native shells: `cmd` and `powershell`, as
well as alternate shells available including `sh`.

The `SHELL` instruction can appear multiple times. Each `SHELL` instruction overrides
all previous `SHELL` instructions, and affects all subsequent instructions. For example:

```dockerfile
FROM microsoft/windowsservercore

# Executed as cmd /S /C echo default
RUN echo default

# Executed as cmd /S /C powershell -command Write-Host default
RUN powershell -command Write-Host default

# Executed as powershell -command Write-Host hello
SHELL ["powershell", "-command"]
RUN Write-Host hello

# Executed as cmd /S /C echo hello
SHELL ["cmd", "/S", "/C"]
RUN echo hello
```

The following instructions can be affected by the `SHELL` instruction when the
shell form of them is used in a Dockerfile: `RUN`, `CMD` and `ENTRYPOINT`.

The following example is a common pattern found on Windows which can be
streamlined by using the `SHELL` instruction:

```dockerfile
RUN powershell -command Execute-MyCmdlet -param1 "c:\foo.txt"
```

The command invoked by the builder will be:

```powershell
cmd /S /C powershell -command Execute-MyCmdlet -param1 "c:\foo.txt"
```

This is inefficient for two reasons. First, there is an unnecessary `cmd.exe`
command processor (aka shell) being invoked. Second, each `RUN` instruction in
the shell form requires an extra `powershell -command` prefixing the command.

To make this more efficient, one of two mechanisms can be employed. One is to
use the JSON form of the `RUN` command such as:

```dockerfile
RUN ["powershell", "-command", "Execute-MyCmdlet", "-param1 \"c:\\foo.txt\""]
```

While the JSON form is unambiguous and does not use the unnecessary `cmd.exe`,
it does require more verbosity through double-quoting and escaping. The alternate
mechanism is to use the `SHELL` instruction and the shell form,
making a more natural syntax for Windows users, especially when combined with
the `escape` parser directive:

```dockerfile
# escape=`

FROM microsoft/nanoserver
SHELL ["powershell","-command"]
RUN New-Item -ItemType Directory C:\Example
ADD Execute-MyCmdlet.ps1 c:\example\
RUN c:\example\Execute-MyCmdlet -sample 'hello world'
```

Resulting in:

```console
PS E:\myproject> docker build -t shell .

Sending build context to Docker daemon 4.096 kB
Step 1/5 : FROM microsoft/nanoserver
 ---> 22738ff49c6d
Step 2/5 : SHELL powershell -command
 ---> Running in 6fcdb6855ae2
 ---> 6331462d4300
Removing intermediate container 6fcdb6855ae2
Step 3/5 : RUN New-Item -ItemType Directory C:\Example
 ---> Running in d0eef8386e97


    Directory: C:\


Mode         LastWriteTime              Length Name
----         -------------              ------ ----
d-----       10/28/2016  11:26 AM              Example


 ---> 3f2fbf1395d9
Removing intermediate container d0eef8386e97
Step 4/5 : ADD Execute-MyCmdlet.ps1 c:\example\
 ---> a955b2621c31
Removing intermediate container b825593d39fc
Step 5/5 : RUN c:\example\Execute-MyCmdlet 'hello world'
 ---> Running in be6d8e63fe75
hello world
 ---> 8e559e9bf424
Removing intermediate container be6d8e63fe75
Successfully built 8e559e9bf424
PS E:\myproject>
```

The `SHELL` instruction could also be used to modify the way in which
a shell operates. For example, using `SHELL cmd /S /C /V:ON|OFF` on Windows, delayed
environment variable expansion semantics could be modified.

The `SHELL` instruction can also be used on Linux should an alternate shell be
required such as `zsh`, `csh`, `tcsh` and others.

## Here-Documents

Here-documents allow redirection of subsequent Dockerfile lines to the input of
`RUN` or `COPY` commands. If such command contains a [here-document](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_07_04)
the Dockerfile considers the next lines until the line only containing a
here-doc delimiter as part of the same command.

### Example: Running a multi-line script

```dockerfile
# syntax=docker/dockerfile:1
FROM debian
RUN <<EOT bash
  set -ex
  apt-get update
  apt-get install -y vim
EOT
```

If the command only contains a here-document, its contents is evaluated with
the default shell.

```dockerfile
# syntax=docker/dockerfile:1
FROM debian
RUN <<EOT
  mkdir -p foo/bar
EOT
```

Alternatively, shebang header can be used to define an interpreter.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.6
RUN <<EOT
#!/usr/bin/env python
print("hello world")
EOT
```

More complex examples may use multiple here-documents.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
RUN <<FILE1 cat > file1 && <<FILE2 cat > file2
I am
first
FILE1
I am
second
FILE2
```

### Example: Creating inline files

With `COPY` instructions, you can replace the source parameter with a here-doc
indicator to write the contents of the here-document directly to a file. The
following example creates a `greeting.txt` file containing `hello world` using
a `COPY` instruction.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
COPY <<EOF greeting.txt
hello world
EOF
```

Regular here-doc [variable expansion and tab stripping rules](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html#tag_18_07_04) apply.
The following example shows a small Dockerfile that creates a `hello.sh` script
file using a `COPY` instruction with a here-document.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
ARG FOO=bar
COPY <<-EOT /script.sh
  echo "hello ${FOO}"
EOT
ENTRYPOINT ash /script.sh
```

In this case, file script prints "hello bar", because the variable is expanded
when the `COPY` instruction gets executed.

```console
$ docker build -t heredoc .
$ docker run heredoc
hello bar
```

If instead you were to quote any part of the here-document word `EOT`, the
variable would not be expanded at build-time.

```dockerfile
# syntax=docker/dockerfile:1
FROM alpine
ARG FOO=bar
COPY <<-"EOT" /script.sh
  echo "hello ${FOO}"
EOT
ENTRYPOINT ash /script.sh
```

Note that `ARG FOO=bar` is excessive here, and can be removed. The variable
gets interpreted at runtime, when the script is invoked:

```console
$ docker build -t heredoc .
$ docker run -e FOO=world heredoc
hello world
```

## Dockerfile examples

For examples of Dockerfiles, refer to:

- The [building best practices page](https://docs.docker.com/build/building/best-practices/)
- The ["get started" tutorials](https://docs.docker.com/get-started/)
- The [language-specific getting started guides](https://docs.docker.com/guides/language/)

[^1]: /reference/Value required
[^2]: /reference/For Docker-integrated [BuildKit](https:/docs.docker.com/build/buildkit#getting-started) and `docker buildx build`

# Troubleshoot Docker Desktop


This page contains information on how to diagnose and troubleshoot Docker Desktop, and how to check the logs.

## Troubleshoot menu

To navigate to **Troubleshoot** either:

- Select the Docker menu Docker menu 


![whale menu](/images/whale-x.svg) and then **Troubleshoot**.
- Select the **Troubleshoot** icon near the top-right corner of Docker Dashboard.

The **Troubleshooting** menu contains the following options:

- **Restart Docker Desktop**.

- **Reset Kubernetes cluster**. Select to delete all stacks and Kubernetes resources. For more information, see [Kubernetes](/desktop/settings-and-maintenance/settings/#kubernetes).

- **Clean / Purge data**. This option resets all Docker data without a
  reset to factory defaults. Selecting this option results in the loss of existing settings.

- **Reset to factory defaults**: Choose this option to reset all options on
  Docker Desktop to their initial state, the same as when Docker Desktop was first installed.

If you are a Mac or Linux user, you also have the option to **Uninstall** Docker Desktop from your system.

## Diagnose

> [!TIP]
>
> If you do not find a solution in troubleshooting, browse the GitHub repositories or create a new issue on the [Docker Desktop issue tracker](https://github.com/docker/desktop-feedback).

### Diagnose from the app

1. From **Troubleshoot**, select **Get support**. This opens the in-app Support page and starts collecting the diagnostics.
   > [!NOTE]
   >
   > Gathering diagnostics may take several minutes. Don't close Docker Desktop while the diagnostics are being collected.
2. When the diagnostics collection process is complete, select **Upload to get a Diagnostic ID**.
3. When the diagnostics are uploaded, Docker Desktop prints a diagnostic ID. Copy this ID.
4. Use your diagnostics ID to get help:
   - If you have a paid Docker subscription, select **Contact support**. This opens the Docker Desktop support form. Fill in the information required and add the ID you copied in step three to the **Diagnostics ID field**. Then, select **Submit ticket** to request Docker Desktop support.
     > [!NOTE]
     >
     > You must be signed in to Docker Desktop to access the support form. For information on what's covered as part of Docker Desktop support, see [Support](/support/).
   - If you don't have a paid Docker subscription, select **Report a Bug** to open a new Docker Desktop issue on GitHub. Complete the information required and ensure you add the diagnostic ID you copied in step three.

### Diagnose from an error message

1. When an error message appears, select **Gather diagnostics**.
   > [!NOTE]
   >
   > Gathering diagnostics may take several minutes. Don't close Docker Desktop while the diagnostics are being collected.
2. When the diagnostics are uploaded, Docker Desktop prints a diagnostic ID. Copy this ID.
3. Use your diagnostics ID to get help:
   - If you have a paid Docker subscription, select **Contact support**. This opens the Docker Desktop support form. Fill in the information required and add the ID you copied in step three to the **Diagnostics ID field**. Then, select **Submit ticket** to request Docker Desktop support.
     > [!NOTE]
     >
     > You must be signed in to Docker Desktop to access the support form. For information on what's covered as part of Docker Desktop support, see [Support](/support/).
   - If you don't have a paid Docker subscription, you can open a new [Docker Desktop issue on GitHub](https://github.com/docker/desktop-feedback). Complete the information required and ensure you add the diagnostic ID printed in step two.

### Diagnose from the terminal

In some cases, it's useful to run the diagnostics yourself, for instance, if
Docker Desktop cannot start.

> [!NOTE]
>
> Gathering diagnostics may take several minutes. Wait for the process to complete before closing the terminal.

**Windows**



1. Locate the `com.docker.diagnose` tool:

   ```console
   # For all-user installations
   $ C:\Program Files\Docker\Docker\resources\com.docker.diagnose.exe

   # For per-user installations
   $ %LOCALAPPDATA%\Programs\DockerDesktop\resources\com.docker.diagnose.exe
   ```

2. Create and upload the diagnostics ID. In PowerShell, run:

   ```console
   # For all-user installations
   $ & "C:\Program Files\Docker\Docker\resources\com.docker.diagnose.exe" gather -upload

   # For per-user installations
   $ & %LOCALAPPDATA%\Programs\DockerDesktop\resources\com.docker.diagnose.exe" gather -upload
   ```

After the diagnostics have finished, the terminal displays your diagnostics ID and the path to the diagnostics file. The diagnostics ID is composed of your user ID and a timestamp. For example `BE9AFAAF-F68B-41D0-9D12-84760E6B8740/20190905152051`.

**Mac**



1. Locate the `com.docker.diagnose` tool:

   ```console
   $ /Applications/Docker.app/Contents/MacOS/com.docker.diagnose
   ```

2. Create and upload the diagnostics ID. Run:

   ```console
   $ /Applications/Docker.app/Contents/MacOS/com.docker.diagnose gather -upload
   ```

After the diagnostics have finished, the terminal displays your diagnostics ID and the path to the diagnostics file. The diagnostics ID is composed of your user ID and a timestamp. For example `BE9AFAAF-F68B-41D0-9D12-84760E6B8740/20190905152051`.

**Linux**



1. Locate the `com.docker.diagnose` tool:

   ```console
   $ /opt/docker-desktop/bin/com.docker.diagnose
   ```

2. Create and upload the diagnostics ID. Run:

   ```console
   $ /opt/docker-desktop/bin/com.docker.diagnose gather -upload
   ```

After the diagnostics have finished, the terminal displays your diagnostics ID and the path to the diagnostics file. The diagnostics ID is composed of your user ID and a timestamp. For example `BE9AFAAF-F68B-41D0-9D12-84760E6B8740/20190905152051`.



> [!TIP]
>
> You can also use the [`docker desktop diagnose` command](/desktop/features/desktop-cli/) to diagnose Docker Desktop and upload the diagnostics ID.

To view the contents of the diagnostic file:

**Windows**



1. Unzip the file. In PowerShell, copy and paste the path to the diagnostics file into the following command and then run it. It should be similar to the following example:

   ```powershell
   $ Expand-Archive -LiteralPath "C:\Users\testUser\AppData\Local\Temp\5DE9978A-3848-429E-8776-950FC869186F\20230607101602.zip" -DestinationPath "C:\Users\testuser\AppData\Local\Temp\5DE9978A-3848-429E-8776-950FC869186F\20230607101602"
   ```

2. Open the file in your preferred text editor. Run:

   ```powershell
   $ code <path-to-file>
   ```

**Mac**



Run:

```console
$ open /tmp/<your-diagnostics-ID>.zip
```

**Linux**



Run:

```console
$ unzip –l /tmp/<your-diagnostics-ID>.zip
```



#### Use your diagnostics ID to get help

If you have a paid Docker subscription, select **Contact support**. This opens the Docker Desktop support form. Fill in the information required and add the ID you copied in step three to the **Diagnostics ID field**. Then, select **Submit ticket** to request Docker Desktop support.

If you don't have a paid Docker subscription, create an issue on [GitHub](https://github.com/docker/desktop-feedback).

### Self-diagnose tool

> [!IMPORTANT]
>
> This tool has been deprecated.

## Check the logs

In addition to using the diagnose option to submit logs, you can browse the logs yourself.

**Windows**



In PowerShell, run:

```powershell
$ code $Env:LOCALAPPDATA\Docker\log
```

This opens up all the logs in your preferred text editor for you to explore.

**Mac**



### From terminal

To watch the live flow of Docker Desktop logs in the command line, run the following script from your preferred shell.

```console
$ pred='process matches ".*(ocker|vpnkit).*" || (process in {"taskgated-helper", "launchservicesd", "kernel"} && eventMessage contains[c] "docker")'
$ /usr/bin/log stream --style syslog --level=debug --color=always --predicate "$pred"
```

Alternatively, to collect the last day of logs (`1d`) in a file, run:

```console
$ /usr/bin/log show --debug --info --style syslog --last 1d --predicate "$pred" >/tmp/logs.txt
```

### From the Console app

Mac provides a built-in log viewer, named **Console**, which you can use to check
Docker logs.

The Console lives in `/Applications/Utilities`. You can search for it with
Spotlight Search.

To read the Docker app log messages, type `docker` in the Console window search bar and press Enter. Then select `ANY` to expand the drop-down list next to your `docker` search entry, and select `Process`.

![Mac Console search for Docker app](/images/console.png)

You can use the Console Log Query to search logs, filter the results in various
ways, and create reports.

**Linux**



You can access Docker Desktop logs by running the following command:

```console
$ journalctl --user --unit=docker-desktop
```

You can also find the logs for the internal components included in Docker
Desktop at `$HOME/.docker/desktop/log/`.



## View the Docker daemon logs

Refer to the [Read the daemon logs](/engine/daemon/logs/) section
to learn how to view the Docker Daemon logs.

## Further resources

- View specific [troubleshoot topics](/desktop/troubleshoot-and-support/troubleshoot/topics/).
- View information on [known issues](/desktop/troubleshoot-and-support/troubleshoot/known-issues/)
- [Fix "Docker.app is damaged" on macOS](/desktop/troubleshoot-and-support/troubleshoot/mac-damaged-dialog/) - Resolve macOS installation issues
- [Get support for Docker products](/support/)

# Troubleshoot topics for Docker Desktop


> [!TIP]
>
> If you do not find a solution in troubleshooting, browse the GitHub repositories or [create a new issue](https://github.com/docker/desktop-feedback).

## Topics for all platforms

### Certificates not set up correctly 

#### Error message 

When attempting to pull from a registry using `docker run`, you may encounter the following error:

```console
Error response from daemon: Get http://192.168.203.139:5858/v2/: malformed HTTP response "\x15\x03\x01\x00\x02\x02"
```

Additionally, logs from the registry may show:

```console
2017/06/20 18:15:30 http: TLS handshake error from 192.168.203.139:52882: tls: client didn't provide a certificate
2017/06/20 18:15:30 http: TLS handshake error from 192.168.203.139:52883: tls: first record does not look like a TLS handshake
```

#### Possible causes 

- Docker Desktop ignores certificates listed under insecure registries.
- Client certificates are not sent to insecure registries, causing handshake failures.

#### Solution 

- Ensure that your registry is properly configured with valid SSL certificates.
- If your registry is self-signed, configure Docker to trust the certificate by adding it to Docker’s certificates directory (/etc/docker/certs.d/ on Linux).
- If the issue persists, check your Docker daemon configuration and enable TLS authentication.

### Docker Desktop's UI appears green, distorted, or has visual artifacts

#### Cause

Docker Desktop uses hardware-accelerated graphics by default, which may cause problems for some GPUs.

#### Solution

Disable hardware acceleration:

1. Edit Docker Desktop's `settings-store.json` file. You can find this file at:

   - Mac: `~/Library/Group Containers/group.com.docker/settings-store.json`
   - Windows: `C:\Users\[USERNAME]\AppData\Roaming\Docker\settings-store.json`
   - Linux: `~/.docker/desktop/settings-store.json.`

2. Add the following entry:

   ```JSON
   $ "disableHardwareAcceleration": true
   ```

3. Save the file and restart Docker Desktop.

### Using mounted volumes and getting runtime errors indicating an application file is not found, access to a volume mount is denied, or a service cannot start

#### Cause

If your project directory is located outside your home directory (`/home/<user>`), Docker Desktop requires file sharing permissions to access it.

#### Solution

Enable file sharing in Docker Desktop for Mac and Linux:

1. Navigate to **Settings**, select **Resources** and then **File sharing**.
2. Add the drive or folder that contains the Dockerfile and volume mount paths.

Enable file sharing in Docker Desktop for Windows:

1. From **Settings**, select **Shared Folders**. 
2. Share the folder that contains the Dockerfile and volume mount paths.

### `port already allocated` errors

#### Error message

When starting a container, you may see an error like:

```text
Bind for 0.0.0.0:8080 failed: port is already allocated
```

Or

```text
listen tcp:0.0.0.0:8080: bind: address is already in use
```

#### Cause

- Another application on your system is already using the specified port.
- A previously running container was not stopped properly and is still bound to the port.

#### Solution

To discover the identity of this software, either:
- Use the `resmon.exe` GUI, select **Network** and then **Listening Ports**
- In PowerShell, use `netstat -aon | find /i "listening "` to discover the PID of the process
currently using the port (the PID is the number in the rightmost column). 

Then, decide whether to shut the other process down, or to use a different port in your
Docker app.

## Topics for Linux and Mac

### Docker Desktop fails to start on Mac or Linux platforms

#### Error message 

Docker fails to start due to Unix domain socket path length limitations:

```console
[vpnkit-bridge][F] listen unix <HOME>/Library/Containers/com.docker.docker/Data/http-proxy-control.sock: bind: invalid argument
```

```console
[com.docker.backend][E] listen(vsock:4099) failed: listen unix <HOME>/Library/Containers/com.docker.docker/Data/vms/0/00000002.00001003: bind: invalid argument
```

#### Cause

On Mac and Linux, Docker Desktop creates Unix domain sockets used for inter-process communication. These sockets are created under the user's home directory.

Unix domain sockets have a maximum path length:
 - 104 characters on Mac
 - 108 characters on Linux

If your home directory path is too long, Docker Desktop fails to create necessary sockets.

#### Solution

Ensure your username is short enough to keep paths within the allowed limit:
 - Mac: Username should be ≤ 33 characters
 - Linux: Username should be ≤ 55 characters

## Topics for Mac

### Upgrade requires administrator privileges

#### Cause 

On macOS, users without administrator privileges cannot perform in-app upgrades from the Docker Desktop Dashboard.

#### Solution

> [!IMPORTANT]
>
> Do not uninstall the current version before upgrading. Doing so deletes all local Docker containers, images, and volumes.

To upgrade Docker Desktop:

- Ask an administrator to install the newer version over the existing one.
- Use the []`--user` install flag](/desktop/setup/install/mac-install.md#security-and-access) if appropriate for your setup.

### Persistent notification telling me an application has changed my Desktop configurations

#### Cause 

You receive this notification because the Configuration integrity check feature has detected that a third-party application has altered your Docker Desktop configuration. This usually happens due to incorrect or missing symlinks. The notification ensures you are aware of these changes so you can review and repair any potential issues to maintain system reliability.

Opening the notification presents a pop-up window which provides detailed information about the detected integrity issues.

#### Solution

If you choose to ignore the notification, it will be shown again only at the next Docker Desktop startup. If you choose to repair your configuration, you won't be prompted again.

If you want to switch off Configuration integrity check notifications, navigate to Docker Desktop's settings and in the **General** tab, clear the **Automatically check configuration** setting. 

### `com.docker.vmnetd` is still running after I quit the app

The privileged helper process `com.docker.vmnetd` is started by `launchd` and
runs in the background. The process does not consume any resources unless
`Docker.app` connects to it, so it's safe to ignore.

### Incompatible CPU detected

#### Cause

Docker Desktop requires a processor (CPU) that supports virtualization and, more
specifically, the [Apple Hypervisor
framework](https://developer.apple.com/library/mac/documentation/DriversKernelHardware/Reference/Hypervisor/).

#### Solution

Check that: 

 - You've installed the correct Docker Desktop for your architecture
 - Your Mac supports Apple's Hypervisor framework. To check if your Mac supports the Hypervisor framework, run the following command in a terminal window.

   ```console
   $ sysctl kern.hv_support
   ```

   If your Mac supports the Hypervisor Framework, the command prints `kern.hv_support: 1`.

   If not, the command prints `kern.hv_support: 0`.

See also, [Hypervisor Framework
Reference](https://developer.apple.com/library/mac/documentation/DriversKernelHardware/Reference/Hypervisor/)
in the Apple documentation, and Docker Desktop [Mac system requirements](/desktop/setup/install/mac-install/#system-requirements).

## Topics for Windows

### Docker Desktop fails to start when anti-virus software is installed

#### Cause

Some anti-virus software may be incompatible with Hyper-V and Microsoft
Windows builds. The conflict
typically occurs after a Windows update and
manifests as an error response from the Docker daemon and a Docker Desktop start failure.

#### Solution

For a temporary workaround, uninstall the anti-virus software, or
add Docker to the exclusions/exceptions in your antivirus software.

### Permissions errors on data directories for shared volumes

#### Cause 

When sharing files from Windows, Docker Desktop sets permissions on [shared volumes](/desktop/settings-and-maintenance/settings/#file-sharing)
to a default value of [0777](https://chmodcommand.com/chmod-0777/)
(`read`, `write`, `execute` permissions for `user` and for `group`).

The default permissions on shared volumes are not configurable. 

#### Solution

If you are
working with applications that require different permissions, either:
 - Use non-host-mounted volumes  
 - Find a way to make the applications work with the default file permissions

### Unexpected syntax errors, use Unix style line endings for files in containers

#### Cause 

Docker containers expect Unix-style line `\n` endings, not Windows style: `\r\n`. This includes files referenced at the command line for builds and in RUN commands in Docker files.

Keep this in mind when authoring files such as shell scripts using Windows
tools, where the default is likely to be Windows style line endings. These
commands ultimately get passed to Unix commands inside a Unix based container
(for example, a shell script passed to `/bin/sh`). If Windows style line endings
are used, `docker run` fails with syntax errors.

#### Solution 

 - Convert files to Unix-style line endings using:
   
   ```console
   $ dos2unix script.sh
   ```
- In VS Code, set line endings to `LF` (Unix) instead of `CRLF` (Windows).

### Path conversion errors on Windows

#### Cause

Unlike Linux, Windows requires explicit path conversion for volume mounting.


On Linux, the system takes care of mounting a path to another path. For example, when you run the following command on Linux:

```console
$ docker run --rm -ti -v /home/user/work:/work alpine
```

It adds a `/work` directory to the target container to mirror the specified path.

#### Solution

Update the source path. For example, if you are using 
the legacy Windows shell (`cmd.exe`), you can use the following command:

```console
$ docker run --rm -ti -v C:\Users\user\work:/work alpine
```

This starts the container and ensures the volume becomes usable. This is possible because Docker Desktop detects
the Windows-style path and provides the appropriate conversion to mount the directory.

Docker Desktop also allows you to use Unix-style path to the appropriate format. For example:

```console
$ docker run --rm -ti -v /c/Users/user/work:/work alpine ls /work
```

### Docker commands failing in Git Bash

#### Error message

```console
$ docker run --rm -ti -v C:\Users\user\work:/work alpine
docker: Error response from daemon: mkdir C:UsersUserwork: Access is denied.
```

```console
$ docker run --rm -ti -v $(pwd):/work alpine
docker: Error response from daemon: OCI runtime create failed: invalid mount {Destination:\Program Files\Git\work Type:bind Source:/run/desktop/mnt/host/c/Users/user/work;C Options:[rbind rprivate]}: mount destination \Program Files\Git\work not absolute: unknown.
```

#### Cause

Git Bash (or MSYS) provides a Unix-like environment on Windows. These tools apply their own
preprocessing on the command line. 

This affects `$(pwd)`, colon-separated paths, and tilde (`~`)

Also, the `\` character has a special meaning in Git Bash. 

#### Solution

 - Disable Git Bash path conversion temporarily. For example, run the command with MSYS path conversion disable:
    ```console
    $ MSYS_NO_PATHCONV=1 docker run --rm -ti -v $(pwd):/work alpine
    ```
 - Use proper path formatting:
    - Use double forward and backslashes (`\\` `//`) instead of single (`\` `/`).
    - If referencing `$(pwd)`, add an extra `/`:

Portability of the scripts is not affected as Linux treats multiple `/` as a single entry.

### Docker Desktop fails due to Virtualization not working

#### Error message

A typical error message is "Docker Desktop - Unexpected WSL error" mentioning the error code
`Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED`. Manually executing `wsl` commands
also fails with the same error code.

#### Cause

- Virtualization settings are disabled in the BIOS.
- Windows Hyper-V or WSL 2 components are missing.

Note some third-party software such as Android emulators will disable Hyper-V on install.

#### Solutions

Your machine must have the following features for Docker Desktop to function correctly:

##### WSL 2 and Windows Home

1. Virtual Machine Platform
2. [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
3. [Virtualization enabled in the BIOS](https://support.microsoft.com/en-gb/windows/enable-virtualization-on-windows-c5578302-6e43-4b4b-a449-8ced115f58e1)
   Note that many Windows devices already have virtualization enabled, so this may not apply.
4. Hypervisor enabled at Windows startup

![WSL 2 enabled](/desktop/images/wsl2-enabled.png)

It must be possible to run WSL 2 commands without error, for example:

```console
PS C:\users\> wsl -l -v
  NAME              STATE           VERSION
* Ubuntu            Running         2
  docker-desktop    Stopped         2
PS C:\users\> wsl -d docker-desktop echo WSL 2 is working
WSL 2 is working
```

If the features are enabled but the commands are not working, first check [Virtualization is turned on](#virtualization-must-be-turned-on)
then [enable the Hypervisor at Windows startup](#hypervisor-enabled-at-windows-startup) if required. If running Docker
Desktop in a Virtual Machine, ensure [the hypervisor has nested virtualization enabled](#turn-on-nested-virtualization).

##### Hyper-V

On Windows 10 Pro or Enterprise, you can also use Hyper-V with the following features enabled:

1. [Hyper-V](https://docs.microsoft.com/en-us/windows-server/virtualization/hyper-v/hyper-v-technology-overview)
   installed and working
2. [Virtualization enabled in the BIOS](https://support.microsoft.com/en-gb/windows/enable-virtualization-on-windows-c5578302-6e43-4b4b-a449-8ced115f58e1)
   Note that many Windows devices already have virtualization enabled, so this may not apply.
3. Hypervisor enabled at Windows startup

![Hyper-V on Windows features](/desktop/images/hyperv-enabled.png)

Docker Desktop requires Hyper-V as well as the Hyper-V Module for Windows
PowerShell to be installed and enabled. The Docker Desktop installer enables
it for you.

Docker Desktop also needs two CPU hardware features to use Hyper-V: Virtualization and Second Level Address Translation (SLAT), which is also called Rapid Virtualization Indexing (RVI). On some systems, Virtualization must be enabled in the BIOS. The steps required are vendor-specific, but typically the BIOS option is called `Virtualization Technology (VTx)` or something similar. Run the command `systeminfo` to check all required Hyper-V features. See [Pre-requisites for Hyper-V on Windows 10](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/reference/hyper-v-requirements) for more details.

To install Hyper-V manually, see [Install Hyper-V on Windows 10](https://msdn.microsoft.com/en-us/virtualization/hyperv_on_windows/quick_start/walkthrough_install). A reboot is *required* after installation. If you install Hyper-V without rebooting, Docker Desktop does not work correctly.

From the start menu, type **Turn Windows features on or off** and press enter.
In the subsequent screen, verify that Hyper-V is enabled.

##### Virtualization must be turned on

In addition to [Hyper-V](#hyper-v) or [WSL 2](/desktop/features/wsl/), virtualization must be turned on. Check the
Performance tab on the Task Manager. Alternatively, you can type `systeminfo` into your terminal. If you see `Hyper-V Requirements: A hypervisor has been detected. Features required for Hyper-V will not be displayed`, then virtualization is enabled.

![Task Manager](/desktop/images/virtualization-enabled.png)

If you manually uninstall Hyper-V, WSL 2 or turn off virtualization,
Docker Desktop cannot start. 

To turn on nested virtualization, see [Run Docker Desktop for Windows in a VM or VDI environment](/desktop/setup/vm-vdi/#turn-on-nested-virtualization).

##### Hypervisor enabled at Windows startup

If you have completed the previous steps and are still experiencing
Docker Desktop startup issues, this could be because the Hypervisor is installed,
but not launched during Windows startup. Some tools (such as older versions of 
Virtual Box) and video game installers turn off hypervisor on boot. To turn it back on:

1. Open an administrative console prompt.
2. Run `bcdedit /set hypervisorlaunchtype auto`.
3. Restart Windows.

You can also refer to the [Microsoft TechNet article](https://social.technet.microsoft.com/Forums/en-US/ee5b1d6b-09e2-49f3-a52c-820aafc316f9/hyperv-doesnt-work-after-upgrade-to-windows-10-1809?forum=win10itprovirt) on Code flow guard (CFG) settings.

##### Turn on nested virtualization

If you are using Hyper-V and you get the following error message when running Docker Desktop in a VDI environment:

```console
The Virtual Machine Management Service failed to start the virtual machine 'DockerDesktopVM' because one of the Hyper-V components is not running
```

Try [enabling nested virtualization](/desktop/setup/vm-vdi/#turn-on-nested-virtualization).

### Docker Desktop with Windows Containers fails with "The media is write protected""

#### Error message

`FSCTL_EXTEND_VOLUME \\?\Volume{GUID}: The media is write protected`

#### Cause

If you're encountering failures when running Docker Desktop with Windows Containers, it might be due to
a specific Windows configuration policy: FDVDenyWriteAccess.

This policy, when enabled, causes Windows to mount all fixed drives not encrypted by BitLocker-encrypted as read-only.
This also affects virtual machine volumes and as a result, Docker Desktop may not be able to start or run containers
correctly because it requires read-write access to these volumes.

FDVDenyWriteAccess is a Windows Group Policy setting that, when enabled, prevents write access to fixed data drives that are not protected
by BitLocker. This is often used in security-conscious environments but can interfere with development tools like Docker.
In the Windows registry it can be found at `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Policies\Microsoft\FVE\FDVDenyWriteAccess`.

#### Solutions

Docker Desktop does not support running Windows Containers on systems where FDVDenyWriteAccess is enabled. This setting interferes with the
ability of Docker to mount volumes correctly, which is critical for container functionality.

To use Docker Desktop with Windows Containers, ensure that FDVDenyWriteAccess is disabled. You can check and change this setting in the registry or through Group Policy Editor (`gpedit.msc`) under:

**Computer Configuration** > **Administrative Templates** > **Windows Components** > **BitLocker Drive Encryption** > **Fixed Data Drives** > **Deny write access to fixed drives not protected by BitLocker**

> [!NOTE]
>
> Modifying Group Policy settings may require administrator privileges and should comply with your organization's IT policies. If the setting gets reset after some time this usually means that it was overridden by the centralized configuration of your IT department. Talk to them before making any changes.

### `Docker Desktop Access Denied` error message when starting Docker Desktop

#### Error message

When starting Docker Desktop, the following error appears:

```text
Docker Desktop - Access Denied
```

#### Cause

The user is not part of the `docker-users` group, which is required for permissions.

#### Solution

If your admin account is different to your user account, add it:

1. Run **Computer Management** as an administrator.
2. Navigate to **Local Users and Groups** > **Groups** > **docker-users**.
3. Right-click to add the user to the group.
4. Sign out and sign back in for the changes to take effect

# Known issues


**For Mac with Intel chip**


- The Mac Activity Monitor reports that Docker is using twice the amount of memory it's actually using. This is due to a [bug in macOS](https://docs.google.com/document/d/17ZiQC1Tp9iH320K-uqVLyiJmk4DHJ3c4zgQetJiKYQM/edit?usp=sharing).

- **"Docker.app is damaged" dialog**: If you see a "Docker.app is damaged and can't be opened" dialog during installation or updates, this is typically caused by non-atomic copy operations when other applications are using the Docker CLI. See [Fix "Docker.app is damaged" on macOS](/desktop/troubleshoot-and-support/troubleshoot/known-issues/mac-damaged-dialog/) for resolution steps.

- Force-ejecting the `.dmg` after running `Docker.app` from it can cause the
  whale icon to become unresponsive, Docker tasks to show as not responding in the Activity Monitor, and for some processes to consume a large amount of CPU resources. Reboot and restart Docker to resolve these issues.

- Docker Desktop uses the `HyperKit` hypervisor
  (https://github.com/docker/hyperkit) in macOS 10.10 Yosemite and higher. If
  you are developing with tools that have conflicts with `HyperKit`, such as
  [Intel Hardware Accelerated Execution Manager
  (HAXM)](https://software.intel.com/en-us/android/articles/intel-hardware-accelerated-execution-manager/),
  the current workaround is not to run them at the same time. You can pause
  `HyperKit` by quitting Docker Desktop temporarily while you work with HAXM.
  This allows you to continue work with the other tools and prevent `HyperKit`
  from interfering.

- If you are working with applications like [Apache
  Maven](https://maven.apache.org/) that expect settings for `DOCKER_HOST` and
  `DOCKER_CERT_PATH` environment variables, specify these to connect to Docker
  instances through Unix sockets. For example:

  ```console
  $ export DOCKER_HOST=unix:///var/run/docker.sock
  ```

**For Mac with Apple silicon**



- Some command line tools do not work when Rosetta 2 is not installed.
  - The old version 1.x of `docker-compose`. Use Compose V2 instead - type `docker compose`.
  - The `docker-credential-ecr-login` credential helper.
- Some images do not support the ARM64 architecture. You can add `--platform linux/amd64` to run (or build) an Intel image using emulation.

   However, attempts to run Intel-based containers on Apple silicon machines under emulation can crash as QEMU sometimes fails to run the container. In addition, filesystem change notification APIs (`inotify`) do not work under QEMU emulation. Even when the containers do run correctly under emulation, they will be slower and use more memory than the native equivalent.

   In summary, running Intel-based containers on Arm-based machines should be regarded as "best effort" only. We recommend running `arm64` containers on Apple silicon machines whenever possible, and encouraging container authors to produce `arm64`, or multi-arch, versions of their containers. This issue should become less common over time, as more and more images are rebuilt [supporting multiple architectures](https://www.docker.com/blog/multi-arch-build-and-images-the-simple-way/).
- Users may occasionally experience data drop when a TCP stream is half-closed.

Complete Docker Troubleshooting Guide
Overview
This comprehensive guide covers systematic troubleshooting approaches for Docker-related issues across different platforms and scenarios. Docker troubleshooting requires understanding container lifecycle, networking, storage, and system integration to effectively diagnose and resolve problems.

Common Docker Issues Categories
Installation and Setup: Docker daemon, service, and configuration issues
Container Lifecycle: Starting, stopping, and runtime container problems
Networking: Port binding, connectivity, and DNS resolution issues
Storage: Volume mounting, permissions, and disk space problems
Performance: Resource usage, memory leaks, and optimization issues
Security: Permission errors, user mapping, and access control problems
Platform-Specific: Windows, Linux, and macOS specific issues
Troubleshooting Methodology
Identify the Problem: Gather symptoms and error messages
Check System Status: Verify Docker daemon and system health
Isolate the Issue: Determine if it's container, network, or system related
Gather Information: Collect logs, configurations, and system state
Apply Solutions: Implement fixes systematically
Verify Resolution: Test and monitor the solution
Document: Record the issue and solution for future reference
Diagnostic Tools and Commands
Essential Docker Commands
System Information
# Check Docker version and system info
docker version
docker system info
docker system df

# Check Docker daemon status
sudo systemctl status docker  # Linux
Get-Service Docker            # Windows PowerShell

# View system-wide Docker events
docker system events

# Check resource usage
docker system df -v
docker stats --no-stream

Container Diagnostics
# List all containers (running and stopped)
docker ps -a

# Inspect container configuration
docker inspect <container_name>

# View container logs
docker logs <container_name>
docker logs --tail 50 --follow <container_name>

# Execute commands in running container
docker exec -it <container_name> /bin/bash
docker exec -it <container_name> /bin/sh

# Check container processes
docker top <container_name>

# View container resource usage
docker stats <container_name>

Network Diagnostics
# List Docker networks
docker network ls

# Inspect network configuration
docker network inspect <network_name>

# Test network connectivity
docker exec <container_name> ping <target>
docker exec <container_name> nslookup <hostname>
docker exec <container_name> netstat -tulpn

# Check port bindings
docker port <container_name>

Image and Storage Diagnostics
# List images
docker images -a

# Inspect image layers
docker history <image_name>

# Check disk usage
docker system df
docker system df -v

# List volumes
docker volume ls

# Inspect volume
docker volume inspect <volume_name>

Container Issues
Issue 1: Container Won't Start
Symptoms
Container exits immediately after starting
"Container exited with code X" errors
Container stuck in "Restarting" state
Diagnostic Steps
# Check container status and exit code
docker ps -a

# View container logs
docker logs <container_name>

# Inspect container configuration
docker inspect <container_name>

# Check if image exists and is accessible
docker images | grep <image_name>

# Try running container interactively
docker run -it <image_name> /bin/bash

Common Solutions
# Fix 1: Check and fix command/entrypoint
docker run -it --entrypoint /bin/bash <image_name>

# Fix 2: Check environment variables
docker run -e ENV_VAR=value <image_name>

# Fix 3: Fix volume mount issues
docker run -v /host/path:/container/path:ro <image_name>

# Fix 4: Check resource limits
docker run --memory=1g --cpus=1 <image_name>

# Fix 5: Fix user permissions
docker run --user $(id -u):$(id -g) <image_name>

Issue 2: Container Performance Problems
Symptoms
Slow container response
High CPU or memory usage
Container becoming unresponsive
Diagnostic Steps
# Monitor resource usage
docker stats <container_name>

# Check container processes
docker exec <container_name> top
docker exec <container_name> ps aux

# Check system resources
free -h
df -h
iostat -x 1

# Analyze container logs for errors
docker logs <container_name> | grep -i error

Solutions
# Increase resource limits
docker run --memory=2g --cpus=2 <image_name>

# Optimize container configuration
docker run --restart=unless-stopped <image_name>

# Use multi-stage builds to reduce image size
# Add to Dockerfile:
# FROM node:alpine AS builder
# ... build steps ...
# FROM node:alpine AS runtime
# COPY --from=builder /app /app

# Enable logging driver optimization
docker run --log-driver=json-file --log-opt max-size=10m --log-opt max-file=3 <image_name>


Issue 3: Container Networking Problems
Symptoms
Cannot connect to container services
Port binding failures
DNS resolution issues
Diagnostic Steps
# Check port bindings
docker port <container_name>
netstat -tulpn | grep <port>

# Test network connectivity
docker exec <container_name> ping google.com
docker exec <container_name> nslookup <hostname>

# Check network configuration
docker network ls
docker network inspect bridge

# Test container-to-container communication
docker exec <container1> ping <container2>

Solutions
# Fix port binding conflicts
docker run -p 8080:80 <image_name>  # Use different host port

# Create custom network for container communication
docker network create mynetwork
docker run --network=mynetwork --name=app1 <image1>
docker run --network=mynetwork --name=app2 <image2>

# Fix DNS issues
docker run --dns=8.8.8.8 <image_name>

# Enable host networking (Linux only)
docker run --network=host <image_name>

Networking Issues
Issue 4: Port Binding and Firewall Problems
Windows Firewall Configuration
PowerShell Method (Advanced)
# Check if ports are blocked by Windows Firewall
Test-NetConnection -ComputerName localhost -Port 80
Test-NetConnection -ComputerName localhost -Port 443

# Add firewall rules for Docker ports
New-NetFirewallRule -DisplayName "Docker HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "Docker HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
New-NetFirewallRule -DisplayName "Docker Custom" -Direction Inbound -Protocol TCP -LocalPort 9000 -Action Allow

# Check existing firewall rules
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Docker*"}

# Disable Windows Firewall temporarily for testing (not recommended for production)
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False


GUI Method (Step-by-Step)
If your Docker containers are not loading, follow these steps to allow apps through Windows Firewall:

Go to Control Panel
Search Firewall and Select Windows Defender Firewall
image

Select Advanced Settings
image

Click Inbound Rules
image

Click New Rule
image

Check Port
image

Add TCP Ports 9000 (If you haven't added Caddy ports yet, do so as well for 443, 80, 2019)
image

Leave Default Click Next
image

Leave Default Click Next
image

Name the rule whatever you want
image

Port Checking
Checking Your Ports:

Go to https://portchecker.co/ and see if your port 443 and 80 are open.
If they are not, you need to make sure your router connected to your modem has those ports port-forwarded for your computer hosting the services.
Linux Firewall Configuration
# Check if ports are accessible
ss -tulpn | grep :80
netstat -tulpn | grep :80

# Configure UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 9000/tcp
sudo ufw status

# Configure firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload

# Configure iptables directly
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4

Issue 5: Docker Network Connectivity
Symptoms
Containers cannot communicate with each other
External network access issues
DNS resolution failures
Diagnostic Steps
# Check Docker network configuration
docker network ls
docker network inspect bridge

# Test container network connectivity
docker run --rm -it alpine ping google.com
docker run --rm -it alpine nslookup google.com

# Check Docker daemon network settings
docker system info | grep -A 10 "Network"

# Verify network interfaces
ip addr show  # Linux
ipconfig      # Windows

Solutions
# Restart Docker networking
sudo systemctl restart docker

# Reset Docker networks
docker network prune -f

# Create custom bridge network
docker network create --driver bridge mynetwork
docker run --network=mynetwork <image_name>

# Fix DNS issues
echo '{"dns": ["8.8.8.8", "8.8.4.4"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Configure Docker daemon for proxy (if behind corporate firewall)
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null << 'EOF'
[Service]
Environment="HTTP_PROXY=http://proxy.company.com:8080"
Environment="HTTPS_PROXY=http://proxy.company.com:8080"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker


Storage and Volume Issues
Issue 6: Volume Mount Problems
Symptoms
Files not persisting between container restarts
Permission denied errors when accessing mounted volumes
Volume mount paths not found
Diagnostic Steps
# Check volume mounts
docker inspect <container_name> | grep -A 10 "Mounts"

# List Docker volumes
docker volume ls

# Inspect volume details
docker volume inspect <volume_name>

# Check file permissions
docker exec <container_name> ls -la /mounted/path

# Check disk space
df -h
docker system df

Solutions
# Fix permission issues (Linux)
sudo chown -R $(id -u):$(id -g) /host/path
sudo chmod -R 755 /host/path

# Use named volumes instead of bind mounts
docker volume create myvolume
docker run -v myvolume:/data <image_name>

# Fix Windows path issues
docker run -v C:\host\path:/container/path <image_name>  # Windows
docker run -v /c/host/path:/container/path <image_name>  # Git Bash

# Set correct user in container
docker run --user $(id -u):$(id -g) -v /host/path:/container/path <image_name>

# Use volume with specific driver
docker volume create --driver local --opt type=nfs --opt o=addr=192.168.1.100,rw --opt device=:/path/to/dir myvolume


Issue 7: Disk Space Issues
Symptoms
"No space left on device" errors
Docker operations failing due to disk space
Slow container performance
Diagnostic Steps
# Check overall disk usage
df -h

# Check Docker disk usage
docker system df
docker system df -v

# Check for large containers/images
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort -k 3 -h

# Check container logs size
find /var/lib/docker/containers -name "*.log" -exec ls -lh {} \; | sort -k 5 -h


Solutions
# Clean up Docker resources
docker system prune -a -f
docker container prune -f
docker image prune -a -f
docker volume prune -f
docker network prune -f

# Remove specific unused images
docker rmi $(docker images -f "dangling=true" -q)

# Configure log rotation
echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Move Docker root directory (if needed)
sudo systemctl stop docker
sudo mv /var/lib/docker /new/location/docker
sudo ln -s /new/location/docker /var/lib/docker
sudo systemctl start docker


Performance Issues
Issue 8: High Resource Usage
Symptoms
High CPU usage by Docker containers
Memory leaks and out-of-memory errors
Slow I/O performance
Diagnostic Steps
# Monitor system resources
top
htop
iostat -x 1

# Monitor Docker container resources
docker stats
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check container processes
docker exec <container_name> top
docker exec <container_name> ps aux --sort=-%cpu
docker exec <container_name> ps aux --sort=-%mem

# Analyze container logs
docker logs <container_name> | grep -i "memory\|cpu\|performance"


Solutions
# Set resource limits
docker run --memory=1g --cpus=1.5 <image_name>
docker run --memory=1g --memory-swap=2g <image_name>

# Use Docker Compose with resource limits
version: '3.8'
services:
  app:
    image: myapp
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

# Optimize Dockerfile
# Use multi-stage builds
# Minimize layers
# Use .dockerignore
# Choose appropriate base images (alpine, slim)

# Configure Docker daemon for performance
echo '{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

Security Issues
Issue 9: Permission and Access Problems
Symptoms
Permission denied errors
Cannot access files in containers
User mapping issues
Diagnostic Steps
# Check container user
docker exec <container_name> whoami
docker exec <container_name> id

# Check file permissions
docker exec <container_name> ls -la /path/to/files

# Check Docker daemon permissions
ls -la /var/run/docker.sock

# Check SELinux context (if applicable)
ls -Z /path/to/mounted/volume

Solutions
# Run container as specific user
docker run --user $(id -u):$(id -g) <image_name>

# Fix Docker socket permissions
sudo usermod -aG docker $USER
newgrp docker

# Set proper file permissions for volumes
sudo chown -R $(id -u):$(id -g) /host/volume/path
sudo chmod -R 755 /host/volume/path

# Configure SELinux for Docker (if needed)
sudo setsebool -P container_manage_cgroup on
sudo chcon -Rt svirt_sandbox_file_t /host/volume/path

# Use user namespace mapping
echo '{"userns-remap": "default"}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

Platform-Specific Issues
Issue 10: Windows-Specific Problems
Docker Desktop Issues
# Check Docker Desktop status
Get-Process "*docker*"

# Restart Docker Desktop
Stop-Process -Name "Docker Desktop" -Force
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# Check WSL2 integration
wsl --list --verbose
wsl --set-default-version 2

# Fix Hyper-V issues
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
Enable-WindowsOptionalFeature -Online -FeatureName Containers -All

# Check Windows version compatibility
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion

Windows Container Issues
# Switch between Linux and Windows containers
& "C:\Program Files\Docker\Docker\DockerCli.exe" -SwitchDaemon

# Check Windows container support
docker version --format '{{.Server.Os}}'

# Fix Windows path issues in volumes
docker run -v C:\host\path:C:\container\path <windows_image>

# Check Windows container networking
docker run --rm mcr.microsoft.com/windows/nanoserver:ltsc2019 ping google.com


Issue 11: Linux-Specific Problems
SystemD and Service Issues
# Check Docker service status
sudo systemctl status docker
sudo journalctl -u docker.service -f

# Restart Docker service
sudo systemctl restart docker
sudo systemctl enable docker

# Check Docker daemon configuration
sudo dockerd --debug

# Fix Docker daemon startup issues
sudo systemctl edit docker.service
# Add:
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock --debug


Cgroup and Resource Issues
# Check cgroup version
mount | grep cgroup

# Enable cgroup v2 (if needed)
sudo grub-editenv - set "systemd.unified_cgroup_hierarchy=1"
sudo update-grub
sudo reboot

# Fix memory cgroup issues
echo 'GRUB_CMDLINE_LINUX="cgroup_enable=memory swapaccount=1"' | sudo tee -a /etc/default/grub
sudo update-grub
sudo reboot


Advanced Troubleshooting
Issue 12: Docker Compose Problems
Symptoms
Services not starting in correct order
Environment variable issues
Network connectivity between services
Diagnostic Steps
# Validate docker-compose.yml
docker compose config

# Check service status
docker compose ps

# View service logs
docker compose logs <service_name>
docker compose logs -f

# Check service dependencies
docker compose top

Solutions
# Fix service dependencies
version: '3.8'
services:
  web:
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

# Use environment files
docker compose --env-file .env up

# Override configurations
docker compose -f docker-compose.yml -f docker-compose.override.yml up

# Debug networking issues
docker compose exec web ping db
docker compose exec web nslookup db

Issue 13: Registry and Image Issues
Symptoms
Cannot pull images from registry
Authentication failures
Image corruption or verification errors
Diagnostic Steps
# Test registry connectivity
docker pull hello-world

# Check registry authentication
docker login <registry_url>

# Verify image integrity
docker image inspect <image_name>

# Check for image vulnerabilities
docker scan <image_name>  # Docker Desktop

Solutions
# Configure registry mirrors
echo '{
  "registry-mirrors": ["https://mirror.gcr.io"]
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Fix authentication issues
docker logout
docker login -u <username> -p <password> <registry>

# Use insecure registry (development only)
echo '{
  "insecure-registries": ["myregistry.local:5000"]
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Build images with specific platform
docker buildx build --platform linux/amd64,linux/arm64 -t myimage .

Monitoring and Logging
Comprehensive Monitoring Setup
# Create monitoring script
cat > docker-monitor.sh << 'EOF'
#!/bin/bash

echo "=== Docker System Status ==="
docker system info | grep -E "(Server Version|Storage Driver|Logging Driver|Cgroup Driver)"

echo -e "\n=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n=== Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo -e "\n=== Disk Usage ==="
docker system df

echo -e "\n=== Recent Errors ==="
docker events --since 1h --filter type=container --filter event=die

echo -e "\n=== Network Status ==="
docker network ls
EOF

chmod +x docker-monitor.sh


Log Analysis
# Centralized logging with ELK stack
version: '3.8'
services:
  app:
    image: myapp
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=myapp"

# Use syslog driver
docker run --log-driver=syslog --log-opt syslog-address=tcp://logserver:514 myapp

# Analyze container logs
docker logs --since 1h <container_name> | grep ERROR
docker logs --tail 100 <container_name> | grep -E "(error|exception|fail)"


Prevention and Best Practices
Proactive Monitoring
# Set up health checks
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Use proper restart policies
docker run --restart=unless-stopped myapp

# Implement resource limits
docker run --memory=1g --cpus=1 --ulimit nofile=1024:1024 myapp

Configuration Management
# Use Docker Compose for complex applications
# Implement proper secret management
# Use multi-stage builds for optimization
# Implement proper logging strategies
# Regular security scanning and updates

Summary
This comprehensive Docker troubleshooting guide provides:

Systematic diagnostic approaches for identifying and resolving Docker issues
Container lifecycle troubleshooting with startup, runtime, and performance problems
Network troubleshooting including firewall configuration and connectivity issues
Storage and volume problem resolution with permission and mounting issues
Performance optimization with resource management and monitoring
Security troubleshooting with permission and access control issues
Platform-specific solutions for Windows and Linux environments
Advanced troubleshooting for Docker Compose and registry issues

Your Docker troubleshooting skills are now equipped with professional diagnostic tools and systematic approaches to resolve complex containerization issues efficiently.

Introduction
Docker makes it easy to wrap your applications and services in containers so you can run them anywhere. Unfortunately, problems may arise when building your image and integrating all of the layers that your app needs, especially if you’re new to Docker images and containers. You may encounter typos, issues with runtime libraries and modules, naming collisions, or issues when communicating with other containers.

In this troubleshooting guide aimed at people new to Docker, you’ll troubleshoot problems when building Docker images, resolve naming collisions when running containers, and fix issues that come up when communication between containers.

Prerequisites
To complete this tutorial, you will need

Docker installed on a server or your local machine.
To install Docker on a server, you can follow the how-to guides for CentOS 7 or for Ubuntu 16.04.

You can visit the Docker web site or follow the official installation documentation to install Docker on your local machine.

Step 1 — Resolving Problems with the Dockerfile
The most common place you may run into issues is when you’re building your Docker image from a Dockerfile. Before we dive in, let’s clarify the difference between images and containers.

An image is a read-only resource that you create using a configuration file called Dockerfile. It’s what you ship and share through Docker Hub or your private registry.
A container, is a read and write instance that your create out of the image you built.
You can learn more about these concepts in the tutorial Docker Explained: Using Dockerfiles to automate building of images.

When you look at a Dockerfile, you can clearly see the step-by-step process Docker uses build the image because each line in the Dockerfile corresponds to a step in the process. This generally means that if you got to a certain step, then all of the previous steps completed successfully.

Let’s create a little project to explore some issues you might encounter with a Dockerfile. Create a docker_image directory in your home directory, and use nano or your favorite editor to create a Dockerfile in that folder

mkdir ~/docker_image
nano ~/docker_image/Dockerfile
Add the following content to this new file:

~/docker_image/Dockerfile
# base image
FROM debian:latest

# install basic apps
RUN aapt-get install -qy nano
There’s an intentional typo in this code. Can you spot it? Try to build an image from this file to see how Docker handles a bad command. Create the image with the following command:

docker build -t my_image ~/docker_image
You’ll see this message in your terminal, indicating an error:

Output
Step 2 : RUN aapt-get install -qy nano
  ---> Running in 085fa10ffcc2
/bin/sh: 1: aapt-get: not found
The command '/bin/sh -c aapt-get install -qy nano' returned a non-zero code: 127
The error message at the end means that there was a problem with the command in Step 2. In this case it was our intentional typo: we have aapt-get instead of apt-get. But that also meant that the previous step executed correctly.

Modify the Dockerfile and make the correction:

Dockerfile

# install basic apps
RUN apt-get install -qy nano
Now run the docker build command again:

docker build -t my_image ~/docker_image
And now you’ll see the following output:

Output
Sending build context to Docker daemon 2.048 kB
Step 1 : FROM debian:latest
---> ddf73f48a05d
Step 2 : RUN apt-get install -qy nano
---> Running in 9679323b942f
Reading package lists...
Building dependency tree...
E: Unable to locate package nano
The command '/bin/sh -c apt-get install -qy nano' returned a non-zero code: 100
With the typo corrected, the process moved a little faster, since Docker cached the first step rather than redownloading the base image. But as you can see from the output, we have a new error.

The Debian distribution we’ve used as the foundation for our image couldn’t find the text editor nano, even though we know it is available on the Debian package repositories. The base image comes with cached metadata, such as repositories and lists of available packages. You may occasionally experience some cache issues when the live repositories you’re pulling data from have changed.

To fix this, modify the Dockerfile to do a cleanup and update of the sources before you install any new packages. Open the configuration file again:

nano ~/docker_image/Dockerfile
Add the following highlighted line to the file, above the command to install nano:

~/docker_image/Dockerfile
# base image
FROM debian:latest

# clean and update sources
RUN apt-get clean && apt-get update

# install basic apps
RUN apt-get install -qy nano
Save the file and run the docker build command again:

docker build -t my_image ~/docker_image
This time the process completes successfully.

Output
Sending build context to Docker daemon 2.048 kB
Step 1 : FROM debian:latest
 ---> a24c3183e910
Step 2 : RUN apt-get install -qy nano
 ---> Running in 2237d254f172
Reading package lists...
Building dependency tree...
Reading state information...
Suggested packages:
  spell
The following NEW packages will be installed:
  nano
...

 ---> 64ff1d3d71d6
Removing intermediate container 2237d254f172
Successfully built 64ff1d3d71d6
Let’s see what happens when we add Python 3 and the PostgreSQL driver to our image. Open the Dockerfile again.

nano ~/docker_image/Dockerfile
And add two new steps to install Python 3 and the Python PostgreSQL driver:

~/docker_image/Dockerfile
# base image
FROM debian:latest

# clean and update sources
RUN apt-get clean && apt-get update

# install basic apps
RUN apt-get install -qy nano

# install Python and modules
RUN apt-get install -qy python3
RUN apt-get install -qy python3-psycopg2
Save the file, exit the editor, and build the image again:

docker build -t my_image ~/docker_image
As you can see from the output, the packages install correctly. The process also completes much more quickly because the previous steps were cached.

Output
Sending build context to Docker daemon 2.048 kB
Step 1 : FROM debian:latest
 ---> ddf73f48a05d
Step 2 : RUN apt-get clean && apt-get update
 ---> Using cache
 ---> 2c5013476fbf
Step 3 : RUN apt-get install -qy nano
 ---> Using cache
 ---> 4b77ac535cca
Step 4 : RUN apt-get install -qy python3
 ---> Running in 93f2d795fefc
Reading package lists...
Building dependency tree...
Reading state information...
The following extra packages will be installed:
  krb5-locales libgmp10 libgnutls-deb0-28 libgssapi-krb5-2 libhogweed2
  libk5crypto3 libkeyutils1 libkrb5-3 libkrb5support0 libldap-2.4-2 libnettle4
  libp11-kit0 libpq5 libsasl2-2 libsasl2-modules libsasl2-modules-db
  libtasn1-6
Suggested packages:
  gnutls-bin krb5-doc krb5-user libsasl2-modules-otp libsasl2-modules-ldap
  libsasl2-modules-sql libsasl2-modules-gssapi-mit
  libsasl2-modules-gssapi-heimdal python-psycopg2-doc
The following NEW packages will be installed:
  krb5-locales libgmp10 libgnutls-deb0-28 libgssapi-krb5-2 libhogweed2
  libk5crypto3 libkeyutils1 libkrb5-3 libkrb5support0 libldap-2.4-2 libnettle4
  libp11-kit0 libpq5 libsasl2-2 libsasl2-modules libsasl2-modules-db
  libtasn1-6 python3-psycopg2
0 upgraded, 18 newly installed, 0 to remove and 0 not upgraded.
Need to get 5416 kB of archives.
After this operation, 10.4 MB of additional disk space will be used.

...

Processing triggers for libc-bin (2.19-18+deb8u6) ...
 ---> 978e0fa7afa7
Removing intermediate container d7d4376c9f0d
Successfully built 978e0fa7afa7
Note: Docker caches the build process, so you may run into a situation where you run an update in the build, Docker caches this update, and some time later your base distribution updates its sources again, leaving you with outdated sources, despite doing a cleanup and update in your Dockerfile. If you run into issues installing or updating packages inside the container, run apt-get clean && apt-get update inside of the container.

Pay close attention to the Docker output to identify where the typos are, and run updates at build time and inside the container to make sure you’re not being hindered by cached package lists.

Syntax errors and caching problems are the most common issues you may encounter when building an image in Docker. Now let’s look at problems that may arise when running containers from those images.

Step 2 — Resolving Container Naming Issues
As you launch more containers, you will eventually come across name collisions. A naming collision is where you try to create a container that has the same name as a container that already exists on your system. Let’s explore how to properly deal with naming, renaming, and deleting containers in order to avoid collisions.

Let’s launch a container from the image we built on the previous section. We will run an interactive bash interpreter inside this container to test things out. Execute the following command:

docker run -ti my_image bash
When the container starts, you’ll see a root prompt waiting for instructions:


Now that you have a running container, let’s look at what kinds of problems you might run into.

When you run a container the way you just did, without explicitly setting a name, Docker assigns a random name to the container. You can see all of the running containers and their corresponding names by running the docker ps command on the Docker host, outside of the running container.

Open a new terminal on the Docker host and run the following command:

docker ps
This command outputs the list of running containers with their names as show in the following example:

Output
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
80a0ca58d6ec        my_image            "bash"              22 seconds ago      Up 28 seconds                           loving_brahmagupta
The name loving_brahmagupta in the preceding output is the name that Docker automatically assigned to the container in the preceding example; yours will have a different name. Letting Docker assign a name to your container is fine in very simple cases, but can present significant problems; when we deploy we need to name containers consistently so we can reference them and automate them easily.

To specify a name for a container we can either use the --name argument when we launch the container, or we can rename a running container to something more descriptive.

Run the following command from the Docker host’s terminal:

docker rename your_container_name python_box
Then list your containers:

docker ps
You’ll see the python_box container in the output, confirming that you successfully renamed the container:

Output
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
80a0ca58d6ec        my_image            "bash"              24 minutes ago      Up 24 minutes                           python_box
To close the container, type exit at the prompt in the terminal containing the running container:

exit
If that’s not an option, you can kill the container from another terminal on the Docker host with the following command:

docker kill python_box
When you kill the container this way, Docker returns the name of the container that was just killed:

Output
python_box
To make sure python_box doesn’t exist anymore, list all of the running containers again:

docker ps
As expected, the container is no longer listed:

Output
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
Now you might think you could launch another container named python_box, but let’s see what happens when we try.

We’ll use the --name argument this time for setting the container’s name:

docker run --name python_box -ti my_image bash
Output
docker: Error response from daemon: Conflict. The name "/python_box" is already in use by container 80a0ca58d6ecc80b305463aff2a68c4cbe36f7bda15e680651830fc5f9dda772. You have to remove (or rename) that container to be able to reuse that name..
See 'docker run --help'.
When you build an image and reuse the name of an existing image, the existing image will be overwritten, as you’ve seen already. Containers are a little more complicated because you can’t overwrite a container that already exists.

Docker says python_box already exists even though we just killed it and it’s not even listed with docker ps. It’s not running, but it’s still available in case you want to start it up again. We stopped it, but we didn’t remove it. The docker ps command only shows running containers, not all containers.

To list all of the Docker containers, running and otherwise, pass the -a flag (alias for --all) to docker ps:

docker ps -a
Now our python_box container appears in the output:

Output
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS                        PORTS               NAMES
80a0ca58d6ec        my_image            "bash"              12 minutes ago      Exited (137) 6 minutes ago                       python_box
The container exists with an Exited (137) status, which is why we ran into the naming problem when we tried to create a new container with the same name.

When you want to completely remove a container, you use the docker rm command. Execute this command in your terminal:

docker rm python_box
Once again, Docker outputs the name of the container that was just removed:

Output
python_box
Warning: This command will fail and output an error message if the container is still running, so make sure you stop or kill it first.

Let’s create a new container named python_box now that we removed the previous one:

docker run --name python_box -ti my_image bash
The process completes and we are once again presented with a root shell:


Now let’s kill and remove the container so we avoid problems in the future. From another Terminal session on the Docker host, kill the container and remove it with the following command:

docker kill python_box && docker rm python_box
We chained two commands together, so the output shows the container name twice. The first output verifies we’ve killed the container, and the other confirms that we’ve removed it.

Output
python_box
python_box
Keep docker ps -a in mind when experiencing issues with names and make sure that your containers are stopped and removed before you try to recreate them with the same name.

Naming containers makes it easier for you to manage your infrastructure. Names also make it easy to communicate between containers, as you’ll see next.

Step 3 — Resolving Container Communication Issues
Docker makes it easy to instantiate several containers so you can run different or even redundant services in each one. If a service fails or gets compromised, you can just replace it with a new one while keeping the rest of the infrastructure intact. But you may run into issues making those containers communicate with each other.

Let’s create two containers that communicate so we can explore potential communication issues. We’ll create one container running Python using our existing image, and another container running an instance of PostgreSQL. We’ll use the official PostgreSQL image available from Docker Hub for that container.

Let’s create the PostgreSQL container first. We’ll give this container a name by using the --name flag so that we can identify it easily when linking it with other containers. We’ll call it postgres_box.

Previously, when we launched a container, it ran in the foreground, taking over our terminal. We want to start the PostgreSQL database container in the background, which we can do with the --detach flag.

Finally, instead of running bash, we’ll run the postgres command which will start the PostgreSQL database server inside of the container.

Execute the following command to launch the container:

docker run --name postgres_box --detach postgres
Docker will download the image from Docker Hub and create the container. It’ll then return the full ID of the container running in the background:

Output
Unable to find image 'postgres:latest' locally
latest: Pulling from library/postgres
6a5a5368e0c2: Already exists
193f770cec44: Pull complete
...
484ac0d6f901: Pull complete
Digest: sha256:924650288891ce2e603c4bbe8491e7fa28d43a3fc792e302222a938ff4e6a349
Status: Downloaded newer image for postgres:latest
f6609b9e96cc874be0852e400381db76a19ebfa4bd94fe326477b70b8f0aff65
List the containers to make sure this new container is running:

docker ps
The output confirms that the postgres_box container is running in the background, exposing port 5432, the PostgreSQL database port:

Output
CONTAINER ID        IMAGE               COMMAND                  CREATED                  STATUS              PORTS               NAMES
7a230b56cd64        postgres_box            "/docker-entrypoint.s"   Less than a second ago   Up 2 seconds        5432/tcp            postgres
Now let’s launch the Python container. In order for the programs running inside of the Python container to “see” services in the postgres_box container, we need to manually link our Python container to the postgres_box container by using the --link argument. To create the link, we specify the name of the container, followed by the name of the link. We’ll use the link name to refer to the postgres_box container from inside the Python container.

Issue the following command to start the Python container:

docker run --name python_box --link postgres_box:postgres -ti my_image bash
Now let’s try to connect to PostgreSQL from inside the python_box container.

We previously installed nano inside of the python_box container so let’s use it to create a simple Python script to test the connection to PostgreSQL. In the terminal for the python_box container, execute this command:

nano pg_test.py
Then add the following Python script to the file:

pg_test.py
"""Test PostgreSQL connection."""
import psycopg2

conn = psycopg2.connect(user='postgres')
print(conn)
Save the file and exit the editor. Let’s see what happens when we try to connect to the database from our script. Execute the script in your container:

python3 pg_test.py
The output we see indicates there’s an issue connecting to the database:

Output
Traceback (most recent call last):
  File "pg_test.py", line 5, in <module>
    conn = psycopg2.connect(database="test", user="postgres", password="secret")
  File "/usr/lib/python3/dist-packages/psycopg2/__init__.py", line 164, in connect
    conn = _connect(dsn, connection_factory=connection_factory, async=async)
psycopg2.OperationalError: could not connect to server: No such file or directory
    Is the server running locally and accepting
    connections on Unix domain socket "/var/run/postgresql/.s.PGSQL.5432"?
We’ve ensured the postgres_box container is running and we’ve linked it to the python_box container, so then what happened? Well, we never specified the database host when we tried to connect, so Python tries to connect to a database running locally, and that won’t work because the service isn’t running locally, it is running in a different container just as if it was on a different computer.

You can access the linked container using the name you set up when you created the link. In our case, we use postgres to reference the postgres_box container that’s running our database server. You can verify this by viewing the /etc/hosts file within the python_box container:

cat /etc/hosts
You will see all of the available hosts with their names and IP addresses. Our postgres server is clearly visible.

Output
127.0.0.1       localhost
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
172.17.0.2      postgres f6609b9e96cc postgres_box
172.17.0.3      3053f74c8c13
So let’s modify our Python script and add the hostname. Open the file.

nano pg_test.py
Then specify the host in the connection string:

/pg_test.py
"""Test PostgreSQL connection."""
import psycopg2

conn = psycopg2.connect(host='postgres', user='postgres')
print(conn)
Save the file and then run the script again.

python3 pg_test.py
This time the script completes without any errors:

Output
<connection object at 0x7f64caec69d8; dsn: 'user=postgres host=7a230b56cd64', closed: 0>
Keep container names in mind when you’re trying to connect to services in other containers, and edit your application credentials to reference the linked names of those containers.

Conclusion
We just covered the most common issues you may encounter when working with Docker containers, from building images to deploying a network of containers.

Docker has a --debug flag which is intended mainly for Docker developers. However, if want to know more about Docker internals, try running Docker commands in debug mode for more verbose output:

docker -D [command] [arguments]
While containers in software have existed for some time, Docker itself has existed for only three years and can be quite complex. Take your time to get familiar with the terms and the ecosystem, and you’ll see how some concepts that were a bit foreign at first will soon make a lot of sense.













