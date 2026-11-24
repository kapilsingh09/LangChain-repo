# Cloie Tea

## GitHub repository storage

Configure `.env` with a GitHub token and MongoDB connection:

```env
GITHUB_TOKEN=your_github_token
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=cloie_tea
```

`MONGODB_URI` defaults to the local MongoDB instance, and the database defaults
to `cloie_tea`. Repositories are stored in the `github_repositories` collection,
keyed by GitHub's repository ID so repeated collection runs update existing
records rather than duplicating them.

Start the API with `uvicorn main:app --reload` from this project directory.
Use `POST /github/repos/collect` to collect and store repositories. Remove one
stored repository with `DELETE /github/repos/{source_id}`.