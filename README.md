Vendor Score Microservice
Overview

The Vendor Score Microservice allows businesses to register vendors, submit performance metrics, compute numeric scores, and retrieve vendor details.
This project demonstrates backend engineering skills: API design, database modeling, validation, scoring logic, migrations, testing, and documentation.

Features

Register vendors

Submit performance metrics

Compute vendor score based on weighted factors

Get vendor details with the latest score

Get vendor score history

Recompute all vendor scores (admin endpoint)

Input validation for all requests

Auto-generated API Docs with Swagger

Tech Stack

Framework: FastAPI

Language: Python 3.12

Database: SQLite (local), PostgreSQL (optional)

ORM: SQLModel

Migrations: Alembic

Testing: Pytest

Server: Uvicorn

API Endpoints
1. Register a Vendor

POST /vendors

Request Body

{
  "name": "Acme",
  "category": "supplier"
}


Response

{
  "id": 10,
  "name": "Acme",
  "category": "supplier",
  "created_at": "2025-11-26T07:17:13.564277"
}

2. Submit Vendor Metrics

POST /vendors/{vendor_id}/metrics

Request Body

{
  "timestamp": "2025-11-24T10:00:00Z",
  "on_time_delivery_rate": 92.5,
  "complaint_count": 1,
  "missing_documents": false,
  "compliance_score": 85.0
}


Response

{
  "metric_id": 2,
  "vendor_id": 10,
  "score_snapshot_id": 3,
  "score": 87.34,
  "score_calculated_at": "2025-11-26T07:23:51.544634"
}

3. Get Vendor Details + Latest Score

GET /vendors/{vendor_id}

Response

{
  "id": 10,
  "name": "Acme",
  "category": "supplier",
  "created_at": "2025-11-26T07:17:13.564277",
  "latest_score": 87.34,
  "latest_score_at": "2025-11-26T07:23:51.544634"
}

4. Get Vendor Score History

GET /vendors/{vendor_id}/scores

Response

[
  {
    "id": 3,
    "score": 87.34,
    "calculated_at": "2025-11-26T07:23:51.544634"
  }
]

5. Admin — Recompute All Scores

POST /admin/recompute_scores

Response

{
  "recomputed": 2,
  "snapshots": [
    {
      "vendor_id": 8,
      "score": 87.34,
      "calculated_at": "2025-11-26T07:40:29.509272"
    },
    {
      "vendor_id": 10,
      "score": 87.34,
      "calculated_at": "2025-11-26T07:40:29.511940"
    }
  ]
}

6. Health Check

GET /health

Response

{
  "status": "ok"
}

Installation & Setup
1. Clone the repository
git clone https://github.com/kanakyadav192/vendor-microservice
cd vendor-microservice

2. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3. Install dependencies
pip install -r requirements.txt

4. Run migrations
export PYTHONPATH=$(pwd)
alembic upgrade head

5. Start the server
uvicorn app.main:app --reload

6. Access API docs
http://127.0.0.1:8000/docs

Testing

Run all tests:

pytest -q

Project Structure
vendor-microservice/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── scoring.py
│   ├── database.py
│   └── routes/
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
├── dev.db
├── requirements.txt
├── runtime.txt
└── README.md

Scoring Logic

Vendor score is computed using weighted metrics:

40% – On-time delivery rate

30% – Compliance score

Penalty – Complaint count

Penalty – Missing documents

Scores are stored as VendorScore snapshots linked to metrics.

Deployment Notes

Python version: 3.12.0

Works on Render, Railway, Fly.io, etc.

Status

✔ All migrations applied
✔ All tests passing
✔ All endpoints working

Author

Kanak Yadav
Backend Engineer | Python Developer | FastAPI Enthusiast