from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, conint, confloat
from typing import Optional
from datetime import datetime
from sqlmodel import select
from .db import create_db_and_tables, get_session
from .crud import create_vendor, add_metric, get_vendor, compute_and_store_score_for_vendor, list_scores_for_vendor
from .models import VendorScore
from sqlalchemy.orm import Session

app = FastAPI(title="Vendor Score Microservice (Simple)")

class VendorCreateRequest(BaseModel):
    name: str
    category: str

class MetricCreateRequest(BaseModel):
    timestamp: datetime
    on_time_delivery_rate: confloat(ge=0.0, le=100.0)
    complaint_count: conint(ge=0)
    missing_documents: Optional[bool] = False
    compliance_score: confloat(ge=0.0, le=100.0)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/vendors")
def create_vendor_endpoint(payload: VendorCreateRequest, session: Session = Depends(get_session)):
    v = create_vendor(session, payload.name, payload.category)
    return {"id": v.id, "name": v.name, "category": v.category, "created_at": v.created_at.isoformat()}

@app.post("/vendors/{vendor_id}/metrics")
def post_metric(vendor_id: int, payload: MetricCreateRequest, session: Session = Depends(get_session)):
    vendor = get_vendor(session, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    raw_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    ts = raw_payload.get("timestamp")
    try:
        raw_payload["timestamp"] = ts.isoformat()
    except:
        pass

    metric_data = {
        "timestamp": payload.timestamp,
        "on_time_delivery_rate": float(payload.on_time_delivery_rate),
        "complaint_count": int(payload.complaint_count),
        "missing_documents": bool(payload.missing_documents),
        "compliance_score": float(payload.compliance_score),
        "raw_payload": raw_payload
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

@app.get("/vendors/{vendor_id}/scores")
def get_scores_endpoint(vendor_id: int, limit: int = 10, offset: int = 0, session: Session = Depends(get_session)):
    scores = list_scores_for_vendor(session, vendor_id, limit, offset)
    return [{"id": s.id, "score": s.score, "calculated_at": s.calculated_at.isoformat()} for s in scores]

@app.post("/admin/recompute_scores")
def recompute_all(session: Session = Depends(get_session)):
    from .crud import list_vendors
    vendors = list_vendors(session, 1000)
    snapshots = []
    for v in vendors:
        vs = compute_and_store_score_for_vendor(session, v.id)
        if vs:
            snapshots.append({
                "vendor_id": v.id,
                "score": vs.score,
                "calculated_at": vs.calculated_at.isoformat()
            })
    return {"recomputed": len(snapshots), "snapshots": snapshots}
