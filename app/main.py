from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, List
from datetime import datetime
from sqlmodel import select
from .db import create_db_and_tables, get_session
from .crud import create_vendor, add_metric, get_vendor, compute_and_store_score_for_vendor, list_scores_for_vendor
from .models import VendorScore
from sqlalchemy.orm import Session

app = FastAPI(title="Vendor Score Microservice (Simple)")

# --- Pydantic request models kept local so we don't rely on other schema files ---
class VendorCreateRequest(BaseModel):
    name: str = Field(..., example="Acme Supplies")
    category: str = Field(..., example="supplier")  # must match the `category` field used in models

class MetricCreateRequest(BaseModel):
    timestamp: datetime = Field(..., example="2025-11-24T10:00:00Z")
    on_time_delivery_rate: confloat(ge=0.0, le=100.0) = Field(..., example=92.5)
    complaint_count: conint(ge=0) = Field(..., example=1)
    missing_documents: Optional[bool] = Field(False, example=False)
    compliance_score: confloat(ge=0.0, le=100.0) = Field(..., example=85.0)

# --- Startup: ensure tables exist for local/dev usage ---
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Health ---
@app.get("/health")
def health():
    return {"status": "ok"}

# --- Create vendor ---
@app.post("/vendors")
def create_vendor_endpoint(payload: VendorCreateRequest, session: Session = Depends(get_session)):
    v = create_vendor(session, name=payload.name, category=payload.category)
    return {"id": v.id, "name": v.name, "category": v.category, "created_at": v.created_at.isoformat()}

# --- Post metric for a vendor (stores metric + computes score snapshot) ---
@app.post("/vendors/{vendor_id}/metrics")
def post_metric(vendor_id: int, payload: MetricCreateRequest, session: Session = Depends(get_session)):
    vendor = get_vendor(session, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    # Build a JSON-serializable raw_payload from the Pydantic model.
    # Use model_dump() if Pydantic v2 is available; otherwise fall back to dict().
    if hasattr(payload, "model_dump"):
        raw_payload = payload.model_dump()
    else:
        raw_payload = payload.dict()

    # Convert timestamp (datetime) to ISO string so JSON column can store it.
    ts = raw_payload.get("timestamp")
    if ts is not None:
        try:
            # If it's a datetime object, convert to ISO string
            raw_payload["timestamp"] = ts.isoformat()
        except Exception:
            # if already string or cannot convert, leave as-is
            pass

    metric_data = {
        "timestamp": payload.timestamp,
        "on_time_delivery_rate": float(payload.on_time_delivery_rate),
        "complaint_count": int(payload.complaint_count),
        "missing_documents": bool(payload.missing_documents),
        "compliance_score": float(payload.compliance_score),
        "raw_payload": raw_payload,
    }

    m = add_metric(session, vendor_id, metric_data)
    vs = compute_and_store_score_for_vendor(session, vendor_id)

    return {
        "metric_id": m.id,
        "vendor_id": vendor_id,
        "score_snapshot_id": vs.id if vs else None,
        "score": vs.score if vs else None,
        "score_calculated_at": vs.calculated_at.isoformat() if vs else None
    }

    vendor = get_vendor(session, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    metric_data = {
        "timestamp": payload.timestamp,
        "on_time_delivery_rate": float(payload.on_time_delivery_rate),
        "complaint_count": int(payload.complaint_count),
        "missing_documents": bool(payload.missing_documents),
        "compliance_score": float(payload.compliance_score),
        "raw_payload": payload.dict(),
    }

    m = add_metric(session, vendor_id, metric_data)
    vs = compute_and_store_score_for_vendor(session, vendor_id)

    return {
        "metric_id": m.id,
        "vendor_id": vendor_id,
        "score_snapshot_id": vs.id if vs else None,
        "score": vs.score if vs else None,
        "score_calculated_at": vs.calculated_at.isoformat() if vs else None
    }

# --- Get vendor details + latest score ---
@app.get("/vendors/{vendor_id}")
def get_vendor_endpoint(vendor_id: int, session: Session = Depends(get_session)):
    vendor = get_vendor(session, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    stmt = select(VendorScore).where(VendorScore.vendor_id == vendor_id).order_by(VendorScore.calculated_at.desc())
    latest_score = session.exec(stmt).first()

    return {
        "id": vendor.id,
        "name": vendor.name,
        "category": vendor.category,
        "created_at": vendor.created_at.isoformat(),
        "latest_score": latest_score.score if latest_score else None,
        "latest_score_at": latest_score.calculated_at.isoformat() if latest_score else None
    }

# --- Get vendor score history ---
@app.get("/vendors/{vendor_id}/scores")
def get_scores_endpoint(vendor_id: int, limit: Optional[int] = 10, offset: Optional[int] = 0, session: Session = Depends(get_session)):
    scores = list_scores_for_vendor(session, vendor_id, limit=limit, offset=offset)
    return [{"id": s.id, "score": s.score, "calculated_at": s.calculated_at.isoformat()} for s in scores]

# --- Admin: recompute latest score for all vendors (useful for tests/demo) ---
@app.post("/admin/recompute_scores")
def recompute_all(session: Session = Depends(get_session)):
    from .crud import list_vendors
    vendors = list_vendors(session, limit=1000)
    snapshots = []
    for v in vendors:
        vs = compute_and_store_score_for_vendor(session, v.id)
        if vs:
            snapshots.append({"vendor_id": v.id, "score": vs.score, "calculated_at": vs.calculated_at.isoformat()})
    return {"recomputed": len(snapshots), "snapshots": snapshots}
