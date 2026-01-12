"""
Generate a sample audit report for demonstration purposes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from reviewer import run_audit

# Sample e-commerce design
sample_design = """
# E-Commerce Platform Solution Design

## Overview
This document outlines the architecture for our new e-commerce platform serving the Hong Kong market.

## System Architecture

### Frontend
- React-based SPA (Single Page Application)
- Hosted on CloudFront CDN for global distribution
- Mobile-first responsive design

### Backend Services
- **Order Service**: Handles order processing and fulfillment
- **Payment Service**: Integrates with Stripe and PayPal
- **Inventory Service**: Real-time stock management
- **User Service**: Authentication and profile management

### Data Storage
- **Primary Database**: AWS RDS PostgreSQL (us-east-1)
- **Cache Layer**: Redis ElastiCache
- **Object Storage**: S3 for product images and documents

## Authentication & Authorization
- JWT-based authentication
- OAuth 2.0 for social login (Google, Facebook)
- Session timeout: 30 minutes of inactivity
- Password requirements: 12+ characters, complexity enforced

## Security Measures
- HTTPS encryption for all traffic
- API rate limiting: 1000 requests/hour per user
- Input validation on all endpoints
- SQL injection prevention via parameterized queries

## Data Privacy
- Customer data encrypted at rest (AES-256)
- PII data is masked in logs
- Regular security audits quarterly

## Monitoring
- CloudWatch for metrics and logs
- PagerDuty integration for alerts
- SLA: 99.5% uptime

## Deployment
- Docker containers on ECS Fargate
- Blue-green deployment strategy
- CI/CD via GitHub Actions
"""

print("Running audit on sample e-commerce design...")
print("=" * 80)

result = run_audit(sample_design)

# Write to file
output_file = os.path.join(os.path.dirname(__file__), 'samples', 'sample_audit_report.md')
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Sample Solution Design Audit Report\n\n")
    f.write("## Input Design Document\n\n")
    f.write("**Title:** E-Commerce Platform for Hong Kong Market\n\n")
    f.write("**Date:** January 12, 2026\n\n")
    f.write("---\n\n")
    f.write("## Audit Results\n\n")
    f.write(result)
    f.write("\n\n---\n\n")
    f.write("## How to Read This Report\n\n")
    f.write("- **✅ Compliant**: Feature meets all architecture standards and ADRs\n")
    f.write("- **⚠️ Partial**: Feature exists but needs improvements or clarifications\n")
    f.write("- **❌ Non-Compliant**: Feature violates standards or is missing critical requirements\n\n")
    f.write("**Required Actions**: Specific steps needed to achieve full compliance\n")

print(f"\nAudit report saved to: {output_file}")
print("\n" + "=" * 80)
print("AUDIT RESULTS:")
print("=" * 80)
print(result)
