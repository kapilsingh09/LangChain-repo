import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app

client = TestClient(app)


def test_api():
    print("=" * 60)
    print("Testing FastAPI Modular Backend Endpoints")
    print("=" * 60)

    # 1. Root
    print("\n[1] Testing GET / ...")
    res = client.get("/")
    assert res.status_code == 200, f"Root endpoint failed: {res.text}"
    print(f"[OK] Root response: {res.json()}")

    # 2. Health
    print("\n[2] Testing GET /health ...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health endpoint failed: {res.text}"
    print(f"[OK] Health status: {res.json()['status']}")
    print(f"     Configured services: {res.json()['services']}")

    # 3. Reports
    print("\n[3] Testing GET /api/reports ...")
    res = client.get("/api/reports")
    assert res.status_code == 200, f"Reports endpoint failed: {res.text}"
    reports = res.json()
    print(f"[OK] Found {len(reports)} reports in storage")

    if reports:
        first_report = reports[0]["filename"]
        print(f"\n[4] Testing GET /api/reports/{first_report} ...")
        res_detail = client.get(f"/api/reports/{first_report}")
        assert res_detail.status_code == 200, f"Detail endpoint failed: {res_detail.text}"
        print(f"[OK] Report Title: {res_detail.json()['metadata']['title']}")
        print(f"     File size: {res_detail.json()['metadata']['size_bytes']} bytes")

    print("\n" + "=" * 60)
    print("All modular backend tests PASSED successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
