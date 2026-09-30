# Project Assessment-2

## 1. Finalized Project Title and Description

### Project Title
Local Container Service Platform with Load Balancing

### Description
The project aims to build a lightweight container management platform for deploying and managing multiple application containers on a single Linux machine. The platform will use a custom Python controller to interact with Docker Engine and manage container deployment and lifecycle operations.

For HTTP traffic, Nginx will be used as a load balancer to distribute requests among running application instances. A small FastAPI application will be used as the sample workload so that container deployment and request distribution can be demonstrated clearly.

The project is designed as a lightweight Kubernetes-like platform for a single machine and will not depend on Kubernetes or a cloud platform.

---

## 2. Major Components

### UI
The primary interface will be a command-line interface (CLI) through which the user can deploy containers, manage their lifecycle, and view container status.

### Persistence / Data
No database is required for the initial deliverable. Container state and metadata will be obtained from Docker Engine. Nginx configuration will be generated and maintained by the controller.

### Logic
The main logic will be implemented in Python. The controller will use the Docker SDK for Python to create, start, stop, remove, and inspect containers. It will also manage the Nginx backend configuration required for load balancing.

---

## 3. Architecture

The system will operate on a single Linux host.

```text
                    User / CLI
                        |
                        v
                Python Controller
                   /          \
                  v            v
          Docker SDK         Nginx
              |                 |
              v                 |
          Docker Engine        |
          /    |    \          |
         v     v     v         |
      App 1  App 2  App 3 <----+
         \     |     /
          \    |    /
           HTTP Requests
