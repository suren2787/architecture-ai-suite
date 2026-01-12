# ADR-007: Mandatory PII Data Residency in Hong Kong Region

**Status:** Accepted (Mandatory)
**Date:** Sept 1, 2025
**Architect:** [Your Name]

**Context:**
The Hong Kong Personal Data (Privacy) Ordinance (PDPO) requires stringent controls over customer PII. To ensure compliance and minimize legal risk, we must guarantee PII never leaves the local HK jurisdiction.

**Decision:**
All databases (RDS, DynamoDB, S3) containing customer Personal Identifiable Information (PII) must be deployed exclusively within the **AWS `ap-east-1` (Hong Kong)** region. Cross-region replication of PII data is explicitly forbidden.

**Consequences:**
*   **Positive:** Ensures full regulatory compliance with HK privacy laws.
*   **Negative:** Latency for services in other regions (e.g., Singapore, Tokyo) when querying HK data might be slightly higher. Requires engineers to be mindful of multi-region data architecture.

**Compliance:**
This is a mandatory control aligned with SEC-POL-002, section 3.0 Data Protection.
