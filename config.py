"""
Organization Configuration Module

Load organization-specific settings from config.env
"""

import os
from dotenv import load_dotenv

# Load config.env first, then .env (so .env can override if needed)
load_dotenv('config.env')
load_dotenv('.env', override=True)


def get_org_name():
    """Get organization name from config"""
    return os.getenv('ORGANIZATION_NAME', 'Organization')


def get_org_icon():
    """Get organization icon/emoji from config"""
    return os.getenv('ORGANIZATION_ICON', '🏢')


def get_priority_adrs():
    """Get list of priority ADRs from config"""
    adrs = os.getenv('PRIORITY_ADRS', '')
    return [adr.strip() for adr in adrs.split(',') if adr.strip()]


def get_reranking_keywords():
    """Get list of reranking keywords from config"""
    keywords = os.getenv('RERANKING_KEYWORDS', 'aws,pii,ddd')
    return [kw.strip().lower() for kw in keywords.split(',') if kw.strip()]


def get_audit_aspects():
    """Get list of audit aspects to check"""
    aspects = os.getenv('AUDIT_ASPECTS', 'Data Storage,Authentication,Authorization,PII Handling,Regional Compliance')
    return [aspect.strip() for aspect in aspects.split(',') if aspect.strip()]


def get_audit_custom_instructions():
    """Get custom audit instructions"""
    return os.getenv('AUDIT_CUSTOM_INSTRUCTIONS', '')


def get_confluence_space_key():
    """Get Confluence space key for bulk sync"""
    return os.getenv('CONFLUENCE_SPACE_KEY', '')


def get_confluence_labels():
    """Get list of Confluence labels to filter pages"""
    labels_str = os.getenv('CONFLUENCE_LABELS', '')
    if not labels_str:
        return []
    return [label.strip() for label in labels_str.split(',') if label.strip()]


# Export commonly used values
ORG_NAME = get_org_name()
ORG_ICON = get_org_icon()
PRIORITY_ADRS = get_priority_adrs()
RERANKING_KEYWORDS = get_reranking_keywords()
AUDIT_ASPECTS = get_audit_aspects()
AUDIT_CUSTOM_INSTRUCTIONS = get_audit_custom_instructions()
CONFLUENCE_SPACE_KEY = get_confluence_space_key()
CONFLUENCE_LABELS = get_confluence_labels()
