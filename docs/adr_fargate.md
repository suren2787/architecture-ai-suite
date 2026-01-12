Title: ADR-005: Decision to use Amazon ECS Fargate for Microservices
Status: Accepted
Date: July 2025
Context: We are adopting a microservices architecture on AWS. We need a container orchestration platform that minimizes operational overhead and allows for rapid scaling.
Decision: We will use Amazon ECS Fargate for all new microservices. We chose Fargate over EC2 because it removes the need to provision or manage underlying server infrastructure ("serverless containers"), aligning with the "pay for value" billing model.
Consequences: This simplifies CI/CD pipelines, improves fault tolerance by automatically managing availability zones, but increases reliance on AWS-native services like AWS Systems Manager for configuration.