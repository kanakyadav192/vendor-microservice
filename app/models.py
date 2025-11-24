from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.types import JSON

class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    metrics: List["VendorMetric"] = Relationship(back_populates="vendor")
    scores: List["VendorScore"] = Relationship(back_populates="vendor")


class VendorMetric(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id")
    timestamp: datetime
    on_time_delivery_rate: float
    complaint_count: int
    missing_documents: bool = False
    compliance_score: float

    # Tell SQLModel/SQLAlchemy to use a JSON column for this field:
    raw_payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    vendor: Optional[Vendor] = Relationship(back_populates="metrics")


class VendorScore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id")
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    score: float

    vendor: Optional[Vendor] = Relationship(back_populates="scores")
