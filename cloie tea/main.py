import string
from fastapi import FastAPI, HTTPException
import uvicorn
from src.collectors.github import collect_github_repos
from src.db import remove_github_repository, upsert_github_repositories

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from cloies-tea!"}

iteam = []
@app.post("/add/{item}")
def add_item(item: str):
    iteam.append(item)
    print(iteam)
    return {"message": f"Item added: {item}"}

@app.get("/items")
def get_items():
    return {"items": iteam}


@app.get("/github/repos")
async def get_github_repos():
    repositories = await collect_github_repos()
    return {"repositories": repositories}


@app.post("/github/repos/collect")
async def collect_and_store_github_repos():
    repositories = await collect_github_repos()
    storage_result = await upsert_github_repositories(repositories)
    return {
        "collected": len(repositories),
        **storage_result,
    }


@app.delete("/github/repos/{source_id}")
async def delete_github_repo(source_id: str):
    deleted = await remove_github_repository(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"deleted": True, "source_id": source_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)