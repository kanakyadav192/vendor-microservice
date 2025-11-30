from typing import Optional, List
from datetime import datetime
from sqlmodel import select
from .models import Vendor, VendorMetric, VendorScore
from sqlalchemy.orm import Session
from .scoring import compute_score

# --- Vendor operations --------------------------------
def create_vendor(session: Session, name: str, category: str) -> Vendor:
    v = Vendor(name=name, category=category)
    session.add(v)
    session.commit()
    session.refresh(v)
    return v

def get_vendor(session: Session, vendor_id: int) -> Optional[Vendor]:
    return session.get(Vendor, vendor_id)

def list_vendors(session: Session, limit: int = 100) -> List[Vendor]:
    stmt = select(Vendor).limit(limit)
    return session.exec(stmt).all()

# --- Metric operations --------------------------------
def add_metric(session: Session, vendor_id: int, metric_data: dict) -> VendorMetric:
    """
    metric_data should include keys:
      - timestamp (datetime)
      - on_time_delivery_rate (float)
      - complaint_count (int)
      - missing_documents (bool)
      - compliance_score (float)
      - raw_payload (optional)
    """
    m = VendorMetric(vendor_id=vendor_id, **metric_data)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m

def latest_metric_for_vendor(session: Session, vendor_id: int) -> Optional[VendorMetric]:
    stmt = select(VendorMetric).where(VendorMetric.vendor_id == vendor_id).order_by(VendorMetric.timestamp.desc(), VendorMetric.id.desc())
    return session.exec(stmt).first()

# --- Scoring operations --------------------------------
def compute_and_store_score_for_vendor(session: Session, vendor_id: int) -> Optional[VendorScore]:
    vendor = get_vendor(session, vendor_id)
    if not vendor:
        return None

    latest = latest_metric_for_vendor(session, vendor_id)
    if not latest:
        return None

    score_value = compute_score(
        on_time_delivery_rate=latest.on_time_delivery_rate,
        complaint_count=latest.complaint_count,
        missing_documents=latest.missing_documents,
        compliance_score=latest.compliance_score,
        category=vendor.category
    )

    vs = VendorScore(vendor_id=vendor_id, score=score_value, calculated_at=datetime.utcnow())
    session.add(vs)
    session.commit()
    session.refresh(vs)
    return vs

def list_scores_for_vendor(session: Session, vendor_id: int, limit: int = 20, offset: int = 0):
    stmt = select(VendorScore).where(VendorScore.vendor_id == vendor_id).order_by(VendorScore.calculated_at.desc()).limit(limit).offset(offset)
    return session.exec(stmt).all()
