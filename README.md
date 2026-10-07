# Local Container Platform

A lightweight platform for deploying and managing multiple instances of a containerized application on a single Linux host.

The project focuses on simplifying the process of running multiple application replicas and exposing them through a single load-balanced endpoint.

## Problem

Running multiple instances of a containerized application locally involves manually creating containers, assigning ports, tracking their state, and configuring a reverse proxy.

This project aims to bring these operations together through a Python-based controller.

The goal is not to replace production orchestration platforms such as Kubernetes, but to build a lightweight system that demonstrates and automates some of the core concepts behind container orchestration.

## Initial Scope

- Deploy multiple application instances using Docker containers
- Manage container lifecycle through a Python controller
- Assign ports to application replicas
- Distribute HTTP requests between replicas using Nginx
- Provide a single endpoint for accessing the deployed service
- Display basic container information and status

## Technology Stack

- Python
- Docker Engine
- Docker SDK for Python
- FastAPI
- Nginx
- Pytest
- Git and GitHub

## Current Implementation

The platform currently provides a command-line interface for managing application containers.

The controller supports:

- Deploying an application container
- Deploying multiple application replicas
- Listing managed containers
- Starting a stopped container
- Stopping a running container
- Removing a stopped container

The Python controller communicates with Docker Engine through the Docker SDK for Python.

The containers run a small FastAPI application with a basic application endpoint and a health endpoint.

Each replica uses the same application image while being mapped to a different host port. The application also returns its container identity, making it possible to observe which replica handles a request.

## Load Balancing

Nginx is used as the reverse proxy and load balancer for the application replicas.

The current setup exposes the service through:

```text
http://localhost:8080