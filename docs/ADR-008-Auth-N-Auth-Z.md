# ADR-008: Decision to use Amazon Cognito with OIDC for Auth-N/Auth-Z

**Status:** Accepted
**Date:** Oct 10, 2025
**Architect:** [Your Name]

**Context:**
We need a secure, scalable, and compliant Identity and Access Management (IAM) solution for both internal staff and digital banking customers. We need robust OIDC (OpenID Connect) support.

**Decision:**
**Amazon Cognito User Pools** will be the default OIDC provider for customer Authentication (Auth-N). **AWS IAM Identity Center** will be used for internal staff access (Auth-Z) to the AWS console and internal tools.

**Consequences:**
*   **Positive:** Provides industry-standard OIDC flows, MFA support, and integration with existing AWS services (API Gateway, Lambda). Aligns with Principle of Least Privilege.
*   **Negative:** Cognito customization can be complex and may require additional Lambda triggers for bespoke business logic.

**Compliance:**
This directly addresses SEC-POL-002, section 2.0 Access Control & Identity Management.
