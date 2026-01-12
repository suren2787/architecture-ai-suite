Title: Digital Bank SEC-POL-002: Cloud & Data Security Controls
Version: 2.0
Date: Jan 2026
Owner: Chief Information Security Officer (CISO)
1.0 Purpose
This policy ensures the Confidentiality, Integrity, and Availability of all customer data within our AWS environment.
2.0 Access Control & Identity Management
Principle of Least Privilege: AWS IAM policies must grant only the minimum permissions necessary for a role to function.
Multi-Factor Authentication (MFA): MFA is mandatory for all access to the AWS management console and critical infrastructure.
Secrets Management: AWS Secrets Manager must be used for all API keys, database passwords, and credentials.
3.0 Data Protection
Encryption at Rest: All sensitive data stored in Amazon S3, RDS, and EBS volumes must be encrypted by default.
Network Segmentation: Critical banking systems must reside within private Amazon VPCs, with strict security group controls.
Monitoring: Amazon GuardDuty must be enabled across all accounts to monitor for malicious activity.