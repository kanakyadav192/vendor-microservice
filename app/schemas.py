from pydantic import BaseModel, EmailStr
from typing import Optional

class VendorBase(BaseModel):
    name: str
    email: EmailStr
    phone: str

class VendorCreate(VendorBase):
    pass

class Vendor(VendorBase):
    id: int

    class Config:
        orm_mode = True


class MetricsBase(BaseModel):
    quality_score: float
    delivery_score: float
    cost_score: float

class MetricsCreate(MetricsBase):
    vendor_id: int

class Metrics(MetricsBase):
    id: int
    vendor_id: int

    class Config:
        orm_mode = True
