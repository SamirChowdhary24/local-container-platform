# Dockloom

**Build. Deploy. Balance.**

Dockloom is a lightweight, CLI-based platform for deploying and managing multiple instances of containerized applications on a single Linux host.

It combines Docker container management and Nginx load balancing behind an interactive command-line interface, making local application deployment easier to understand and operate.

> **Project status:** Early development. Dockloom currently supports deploying a built-in demo application, managing its containers, and distributing traffic between running replicas.

## Table of Contents

- [Problem Statement](#problem-statement)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Current Implementation](#current-implementation)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Load Balancing](#load-balancing)
- [Testing](#testing)
- [Limitations](#limitations)
- [Roadmap](#roadmap)

## Problem Statement

Running multiple instances of an application locally involves manually creating containers, assigning ports, tracking container states, and configuring a reverse proxy.

Dockloom aims to bring these operations together through a Python-based controller and a simple CLI.

The goal is not to replace production orchestration platforms such as Kubernetes, but to build a lightweight tool that demonstrates and automates core container orchestration concepts.

## Features

- **Multi-replica deployment:** Deploy multiple instances of a containerized application.
- **Container lifecycle management:** List, start, stop, and remove managed containers.
- **Port assignment:** Assign different host ports to application replicas.
- **Load balancing:** Distribute HTTP requests across running replicas using Nginx.
- **Single application endpoint:** Access the service through a shared endpoint.
- **Container identification:** Identify which replica handles a request.
- **Interactive CLI:** Navigate operations using a numbered menu.
- **Terminal styling:** Display formatted tables, panels, and status messages using Rich.
- **Automated testing:** Validate controller behavior and Nginx configuration logic using pytest.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Controller and CLI implementation |
| Docker Engine | Container runtime |
| Docker SDK for Python | Programmatic container management |
| FastAPI | Built-in demonstration application |
| Nginx | Reverse proxy and load balancer |
| Rich | CLI formatting and terminal styling |
| Pytest | Automated testing |
| Git and GitHub | Version control and collaboration |

## Architecture

```text
                   User
                    |
                    v
              Dockloom CLI
                    |
                    v
            Python Controller
                    |
                    v
               Docker Engine
                    |
           +--------+--------+
           |        |        |
           v        v        v
        Replica  Replica  Replica
           1        2        3
           |        |        |
           +--------+--------+
                    |
                    v
             Nginx Load Balancer
                    |
                    v
          http://localhost:8080
```

Dockloom uses a Python controller to communicate with Docker Engine. Each replica runs in its own container and is mapped to a different host port.

Nginx acts as a reverse proxy, distributing requests across the configured running replicas.

## Current Implementation

Dockloom currently provides a CLI for managing containers running the built-in demonstration application.

The implemented operations include:

1. Deploy multiple replicas of the demo application.
2. List managed containers and their states.
3. Start a stopped container.
4. Stop a running container.
5. Remove a container.
6. Exit the CLI.

The controller uses the Docker SDK for Python to manage container operations.

### Demonstration Application

The built-in application uses FastAPI and exposes two endpoints:

| Endpoint | Description |
|---|---|
| `/` | Returns a greeting and container identity |
| `/health` | Returns a basic application health response |

The container identity makes it possible to observe which replica handles a request.

The `/health` endpoint is provided by the demo application. Automated health monitoring through Dockloom's CLI is a planned feature.

## Requirements

Before running Dockloom, ensure your Linux environment has:

- Python 3.12 or a compatible Python version.
- Docker Engine installed and running.
- Permission to communicate with Docker Engine.
- Nginx installed and configured for Dockloom.
- Git installed.

The demonstration application's Docker image uses Python 3.12. The Dockloom controller runs separately in your local Python environment.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/SamirChowdhary24/local-container-platform.git
cd local-container-platform
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Build the Demonstration Image

```bash
docker build -t local-container-app:1.0 .
```

### 5. Verify Docker Access

```bash
docker info
```

If Docker access fails, ensure Docker Engine is running and your user has the necessary permissions.

### 6. Configure Nginx

Dockloom generates an Nginx upstream configuration and installs it at:

```text
/etc/nginx/local-container-platform-upstreams.conf
```

The Nginx server configuration must include the appropriate upstream file and expose the application through port `8080`.

**Important:** If Nginx is already serving other applications on your machine, review the existing configuration before making changes. Dockloom should not overwrite unrelated site configurations.

## Usage

Run Dockloom from the repository root:

```bash
python -m controller.cli
```

The CLI provides the following menu:

```text
1. Deploy application
2. List containers
3. Start container
4. Stop container
5. Remove container
6. Exit
```

Select an option by entering its corresponding number.

### Deploy Replicas

Choose **Deploy application** and enter the requested replica count and starting host port.

For example, deploying three replicas starting at port `8011` assigns these ports:

| Replica | Host Port |
|---|---:|
| `lcp-app-1` | 8011 |
| `lcp-app-2` | 8012 |
| `lcp-app-3` | 8013 |

The ports shown are illustrative. Actual assignments depend on the deployment configuration and available ports.

Once deployment and Nginx synchronization succeed, access the application through:

```text
http://localhost:8080
```

Individual replicas can also be accessed directly through their assigned host ports.

## Load Balancing

Nginx is used as the reverse proxy and load balancer for the application replicas.

Instead of requiring users to access each container separately, Dockloom exposes a shared endpoint:

```text
http://localhost:8080
```

The controller updates the Nginx upstream configuration based on the running replicas.

When a container is stopped or started through Dockloom, the platform attempts to synchronize Nginx with the updated set of running replicas.

This demonstrates a fundamental container orchestration concept: managing application instances and routing traffic to the instances that are currently available.

## Testing

Run the automated test suite from the repository root:

```bash
pytest -q
```

The tests cover core Docker controller behavior and Nginx upstream configuration.

## Limitations

Dockloom is under active development. The current version has the following limitations:

- Deployment uses the built-in demonstration image.
- Deployment from arbitrary GitHub repositories is not yet implemented.
- Applications without a Dockerfile are not automatically containerized.
- Application health monitoring is not yet integrated into the CLI.
- Automatic recovery of failed containers is not yet implemented.
- The platform is intended for local development and learning, not as a hardened production orchestration system.

## Roadmap

- [x] Docker container lifecycle management
- [x] Multi-replica deployment
- [x] Nginx load balancing
- [x] Interactive CLI with Rich formatting
- [ ] Deploy applications from GitHub repositories containing a Dockerfile
- [ ] Improve deployment validation and error handling
- [ ] Add application health monitoring
- [ ] Implement automatic recovery of failed containers
- [ ] Expand documentation and demonstration examples
- [ ] Evaluate alternative load-balancing solutions if required

## Project Goal

Dockloom aims to make local container deployment and management simpler through a small, understandable CLI tool.

The long-term goal is to provide a reusable platform where developers can deploy applications, manage replicas, and observe load balancing without manually coordinating every operation.