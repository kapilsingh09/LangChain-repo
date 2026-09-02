import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure current directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import app

client = TestClient(app)

def test_endpoints():
    print("Testing GET / ...")
    res = client.get("/")
    assert res.status_code == 200, f"Root endpoint failed: {res.text}"
    print(f"Root endpoint OK: {res.json()}")

    print("\nTesting GET /health ...")
    res = client.get("/health")
    assert res.status_code == 200, f"Health endpoint failed: {res.text}"
    print(f"Health endpoint OK: {res.json()}")

    print("\nTesting GET /api/reports ...")
    res = client.get("/api/reports")
    assert res.status_code == 200, f"Reports endpoint failed: {res.text}"
    print(f"Reports list OK ({len(res.json())} reports found)")

    if len(res.json()) > 0:
        first_report = res.json()[0]["filename"]
        print(f"\nTesting GET /api/reports/{first_report} ...")
        res_file = client.get(f"/api/reports/{first_report}")
        assert res_file.status_code == 200, f"Report detail failed: {res_file.text}"
        print(f"Report detail OK! Title: {res_file.json()['metadata']['title']}")

    print("\nAll basic API tests passed successfully!")

if __name__ == "__main__":
    test_endpoints()
