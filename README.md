# Local Container Platform

A lightweight container management platform for deploying and managing multiple application containers on a single Linux host.

## Initial Scope

- Deploy multiple application containers on a single machine
- Manage container lifecycle through a Python controller
- Distribute HTTP requests using Nginx
- Display container status and basic information

## Technology Stack

- Python
- Docker Engine
- Docker SDK for Python
- FastAPI
- Nginx
- Git and GitHub
- Pytest

## Current Implementation

The first working part of the platform focuses on container lifecycle management.

The platform currently provides a command-line interface that allows the user to:

- Deploy a new application container
- List containers managed by the platform
- Start a stopped container
- Stop a running container
- Remove a stopped container

The Python controller communicates with Docker Engine through the Docker SDK for Python. The containers run a small FastAPI application that exposes a basic endpoint and a health endpoint.

Each deployed container uses the same application image but can be mapped to a different host port. The application also returns its container hostname, which can later be used to demonstrate request distribution through Nginx.

## Validation and Testing

Input validation was added to the CLI for:

- Empty container names
- Invalid container name prefixes
- Non-numeric ports
- Ports outside the supported range of 1024–65535

The CLI also handles attempts to start, stop, or remove containers that do not exist.

The controller has unit tests using mocked Docker clients. The current test suite contains five tests covering:

- Container listing
- Container deployment
- Container start
- Container stop
- Container removal

All five tests are currently passing.

The lifecycle operations were also tested with real Docker containers on the Linux host.

## Learnings

During the first implementation, I learned how a custom controller can interact with Docker Engine instead of relying directly on Docker CLI commands.

The Docker SDK provides Python methods for creating, starting, stopping, listing and removing containers. Separating these operations into a controller class also made the code easier to test using mocked Docker clients.

Another important learning was the need for input validation at the CLI level. Invalid names and ports can be rejected before making a request to Docker, while Docker-related errors such as a missing container are handled separately.

The project also helped me understand the difference between unit testing and testing with real Docker containers. The unit tests verify the controller logic using mocks, while manual testing verifies that the complete flow works with the actual Docker Engine.

## Next Steps

The next major feature is Nginx-based load balancing. The goal is to place Nginx in front of multiple FastAPI containers and distribute incoming HTTP requests between the running application instances.

Future improvements may include health monitoring, automatic recovery, autoscaling and a web-based interface.