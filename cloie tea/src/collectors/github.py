import asyncio
import base64
from datetime import datetime, timedelta, timezone

import httpx

from src.config.config import GITHUB_TOKEN


# =====================================
# CONFIGURATION
# =====================================

BASE_URL = "https://api.github.com"

MAX_RESULTS = 50
MIN_STARS = 100
DAYS_BACK = 7
README_MAX_CHARS = 12000
MAX_CONCURRENT_REQUESTS = 5
TOTAL_REPOS_TO_FETCH = 5

QUERIES = [
    "AI",
    "machine-learning",
    "deep-learning",
    "LLM",
    "AI agents",
    "generative-ai",
    "computer-vision",
    "natural-language-processing",
    "RAG",
    "MLOps",
]

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


# =====================================
# FETCH README
# =====================================

async def fetch_readme(client, full_name):

    url = f"{BASE_URL}/repos/{full_name}/readme"

    response = await client.get(url)

    if response.status_code == 404:
        return None

    response.raise_for_status()

    data = response.json()

    if data.get("encoding") != "base64":
        return None

    content = base64.b64decode(
        data["content"]
    ).decode("utf-8", errors="replace")

    return content[:README_MAX_CHARS]


# =====================================
# COLLECT GITHUB REPOSITORIES
# =====================================

async def collect_github_repos():

    date = (
        datetime.now(timezone.utc)
        - timedelta(days=DAYS_BACK)
    ).strftime("%Y-%m-%d")

    repositories = {}

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=30
    ) as client:

        # Search repositories
        for category in QUERIES:

            query = (
                f"{category} pushed:>={date} "
                f"stars:>={MIN_STARS}"
            )

            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": TOTAL_REPOS_TO_FETCH,
            }

            response = await client.get(
                f"{BASE_URL}/search/repositories",
                params=params
            )

            response.raise_for_status()

            data = response.json()

            for repo in data.get("items", []):

                repo_id = repo["id"]

                repositories[repo_id] = {
                    "source": "github",
                    "source_id": str(repo_id),
                    "name": repo["full_name"],
                    "title": repo["name"],
                    "description": repo["description"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "language": repo["language"],
                    "topics": repo["topics"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "pushed_at": repo["pushed_at"],
                    "collected_at": datetime.now(
                        timezone.utc
                    ),
                }

            print(
                f"Collected {len(data.get('items', []))} "
                f"repositories for {category}"
            )

            await asyncio.sleep(1)

    # Apply minimum stars and maximum result limit
    repos = sorted(
        repositories.values(),
        key=lambda repo: repo["stars"],
        reverse=True
    )

    repos = [
        repo for repo in repos
        if repo["stars"] >= MIN_STARS
    ][:MAX_RESULTS]

    print(f"\nSelected {len(repos)} repositories")

    # Fetch READMEs concurrently
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=30
    ) as client:

        async def process_repo(repo):

            async with semaphore:

                try:
                    readme = await fetch_readme(
                        client,
                        repo["name"]
                    )

                    repo["readme"] = readme

                    print(
                        f"README fetched: {repo['name']}"
                        if readme
                        else f"README missing: {repo['name']}"
                    )

                except httpx.HTTPError as error:
                    repo["readme"] = None
                    repo["readme_error"] = str(error)

                return repo

        repos = await asyncio.gather(
            *(process_repo(repo) for repo in repos)
        )

    return [repo for repo in repos if repo.get("readme")]


# =====================================
# MAIN
# =====================================

async def main():

    repos = await collect_github_repos()

    readme_count = sum(
        bool(repo.get("readme"))
        for repo in repos
    )

    print("\n========== RESULTS ==========")
    print(f"Total repositories: {len(repos)}")
    print(f"READMEs fetched: {readme_count}")

    for repo in repos[:5]:

        print("\nRepository:", repo["name"])
        print("Stars:", repo["stars"])
        print("Language:", repo["language"])
        print("Description:", repo["description"])
        print("URL:", repo["url"])

        if repo.get("readme"):
            print("\nREADME preview:")
            print(repo["readme"][:300])


if __name__ == "__main__":
    asyncio.run(main())