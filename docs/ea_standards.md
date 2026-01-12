Title: Digital Bank EA-STD-001: Principles for Microservices Architecture
Version: 1.2
Date: Jan 2026
Owner: Head of Architecture
1.0 Foundational Principles
This document mandates the use of Domain-Driven Design (DDD) to define service boundaries. Each microservice must align with a specific Bounded Context (BC).
2.0 Technical Stack & Deployment
Cloud Provider: AWS is the mandated cloud provider.
Compute: Amazon ECS or AWS Lambda must be used for all new services.
CI/CD: Utilize AWS CodePipeline and AWS CodeBuild for automated deployment.
Observability: All services must integrate with Amazon CloudWatch and CloudTrail for logging and monitoring.
3.0 Data Management
Database per Service: Each microservice must own its database to ensure loose coupling and fault isolation.
Data Classification: All data must be classified (Public, Confidential, Restricted) and encrypted both at rest (using AWS KMS) and in transit.