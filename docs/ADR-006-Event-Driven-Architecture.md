# ADR-006: Decision to use AWS EventBridge over SQS for Core Events

**Status:** Accepted
**Date:** Aug 15, 2025
**Architect:** [Your Name]

**Context:**
Our microservices architecture requires robust asynchronous communication. We need a routing layer for domain events (e.g., "Customer Created," "Transaction Complete"). We considered Amazon SQS for simplicity, but our DDD approach requires multiple downstream services to react to a single event without tight coupling.

**Decision:**
We will use **Amazon EventBridge** as the core event bus for all major domain events. SQS will be used only for local, point-to-point queues within a single Bounded Context.

**Consequences:**
*   **Positive:** Enables true loose coupling and simplified event fan-out (multiple consumers per event) which aligns perfectly with DDD principles. Improved scalability.
*   **Negative:** EventBridge has higher cost per message than SQS and requires more complex IAM policies for fine-grained access control.

**Compliance:**
This decision supports SEC-POL-002 by requiring strict IAM controls on event bus access.
