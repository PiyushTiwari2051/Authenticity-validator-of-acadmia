"""Certificate issuance schemas and ID generator."""

from datetime import date
import secrets
import string
from typing import Optional, Any
import uuid
from pydantic import BaseModel, Field


def generate_certificate_id() -> str:
    """Generate unguessable certificate ID with >= 80 bits of cryptographic entropy.
    Format: SND-<16 uppercase Crockford-style Base32 characters>.
    """
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    random_chars = "".join(secrets.choice(alphabet) for _ in range(16))
    return f"SND-{random_chars}"


class CredentialResult(BaseModel):
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    division: Optional[str] = Field(default=None, max_length=32)
    percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class CredentialDetails(BaseModel):
    title: str = Field(min_length=2, max_length=128, description="e.g. Bachelor of Technology")
    programme: str = Field(min_length=2, max_length=128, description="e.g. Computer Science and Engineering")
    level: str = Field(default="UG", description="UG, PG, Diploma, PhD")
    result: CredentialResult
    issuedOn: str = Field(description="ISO Date YYYY-MM-DD")
    sessionYears: str = Field(description="e.g. 2022-2026")


class SingleIssueRequest(BaseModel):
    holder_name: str = Field(min_length=2, max_length=255)
    enrolment_no: str = Field(min_length=2, max_length=64)
    credential: CredentialDetails
    supersedes: Optional[str] = None


class CertificateResponse(BaseModel):
    certificate_id: str
    institution_id: uuid.UUID
    key_id: str
    holder_name: str
    credential: dict[str, Any]
    signature: str
    verification_url: str
    status: str
    issued_at: str
