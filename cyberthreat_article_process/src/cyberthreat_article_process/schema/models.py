from pydantic import BaseModel, Field
from typing import List, Optional


class KnownThreat(BaseModel):
    """Schema for known cybersecurity threats (e.g., CVEs, vulnerabilities)."""
    threat_type: str = Field(..., description="Type of threat (e.g., Vulnerability, Attack Vector).")
    cve_id: Optional[str] = Field(None, description="CVE identifier if applicable.")
    name: Optional[str] = Field(None, description="Name of the threat if not a CVE.")
    description: str = Field(..., description="Detailed explanation of the threat.")
    affected_product: str = Field(..., description="The affected software or product.")
    affected_component: str = Field(..., description="The specific component that is vulnerable.")
    authentication_required: Optional[bool] = Field(
        None, description="Indicates whether authentication is required to exploit the threat."
    )
    privilege_required: Optional[str] = Field(None, description="Privilege level required to exploit the threat.")
    severity: Optional[str] = Field(None, description="Severity rating (e.g., CVSS score).")
    mitre_attck_techniques: Optional[List[str]] = Field(None, description="MITRE ATT&CK techniques involved.")
    references: List[str] = Field(..., description="Sources for the threat information, also link to the page")


class EmergingThreat(BaseModel):
    """Schema for new and potentially unknown threats."""
    threat_type: str = Field(..., description="Type of emerging threat (e.g., Unauthenticated RCE, Zero-Day).")
    description: str = Field(..., description="Detailed explanation of the emerging threat.")
    affected_product: str = Field(..., description="The affected software or product.")
    affected_component: str = Field(..., description="The specific component that is impacted.")
    authentication_required: Optional[bool] = Field(
        None, description="Indicates whether authentication is required to exploit the threat."
    )
    potential_impact: Optional[str] = Field(None, description="Potential impact of the threat.")
    mitigation: Optional[str] = Field(None, description="Recommended mitigations if applicable.")
    references: List[str] = Field(..., description="Sources for the threat information, also link to the page")


class CyberThreatIntel(BaseModel):
    """Top-level schema for structured cybersecurity threat intelligence output."""
    known_threats: List[KnownThreat] = Field(..., description="List of documented cybersecurity threats.")
    emerging_threats: List[EmergingThreat] = Field(..., description="List of emerging, potentially unknown threats.")