# DataPilot: Intelligent ETL Orchestration Platform 🚀

DataPilot is a robust, multi-agent Data Engineering platform leveraging **LangGraph**, **FastAPI**, and **Docker** to autonomously orchestrate complex Extraction, Transformation, and Loading (ETL) pipelines visually via Natural Language English.

## 🧭 Architecture Overview

DataPilot operates through a strict microservices architecture, entirely modularized safely inside an internal Docker network, driven by a powerful React Frontend Dashboard.

### Core Engines:
- **`datapilot-api`**: The intelligent FastAPI Gateway. It translates your natural language requests and uses an internal state-machine of **4 LangGraph AI Agents** (Planner, Validator, Executor, Monitor) to dynamically orchestrate API calls to the lower-level microservices.
- **`datapilot-extractor`**: A dedicated Python microservice handling data ingestion targets.
- **`datapilot-transformer`**: A dedicated Python microservice executing dynamic Pandas manipulations securely.
- **`datapilot-loader`**: A dedicated Python microservice handling DB insertions and structuring.
- **`datapilot-dashboard`**: A beautiful, glassmorphic React/Vite dashboard allowing users to visualize executing DAG workflows dynamically utilizing `ReactFlow`.

## 📦 How to Run

There is no need to manually spin up messy Python virtual environments or `npm install` packages! DataPilot relies entirely on **Docker**.

1. Verify Docker Desktop is running on your machine.
2. Open your terminal at the root of the repository.
3. Run the following command:
```bash
docker-compose -f infra/docker-compose.yml up --build -d
```
All **6 containers** (API Gateway, Extractor, Transformer, Loader, Postgres State Checkpointer, and the React Dashboard) will dynamically link and boot locally! 

Go to **`http://localhost:5173`** to access the Dashboard.

## ☁️ Cloud Infrastructure (AWS)

DataPilot includes production-grade IaC (Infrastructure as Code) templates:
- **`infra/terraform/`**: Fully configured AWS EKS clusters, VPCs, Subnets, Aurora PostgreSQL nodes, and Cognito user pools. *(Note: Requires a raised AWS EC2 vCPU limit for deployment).*
- **`infra/k8s/`**: Resilient HorizontalPodAutoscalers and API Ingress controllers designed for native deployment inside enterprise Kubernetes.
- **`.github/workflows/deploy.yml`**: A robust GH Actions CI pipeline that dynamically builds and pushes the Python services directly to the AWS Elastic Container Registry on merge.

## 🔒 Authentication

The platform utilizes **AWS Cognito** alongside **AWS Amplify** wrapped directly into the React dashboard, providing enterprise-grade JWT generation natively protecting your execution requests!
