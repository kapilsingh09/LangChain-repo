import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Deep Multi-Agent Research FastAPI Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to run server on")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload on code change")

    args = parser.parse_args()

    print(f"Starting Multi-Agent Research Backend on http://localhost:{args.port}")
    print(f"Interactive Swagger Docs: http://localhost:{args.port}/docs")
    print(f"Health Check: http://localhost:{args.port}/health")

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
