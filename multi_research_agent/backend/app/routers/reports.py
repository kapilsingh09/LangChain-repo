from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.config import settings
from app.schemas.reports import ReportMetadata, ReportDetailResponse

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("", response_model=List[ReportMetadata], summary="List all generated research reports")
async def list_reports():
    """
    Returns metadata for all generated research reports saved in the storage/reports directory.
    """
    reports = []
    if settings.REPORTS_DIR.exists():
        for file in sorted(settings.REPORTS_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
            stat = file.stat()
            title = file.stem.replace("_report", "").replace("_", " ").title()
            reports.append(
                ReportMetadata(
                    filename=file.name,
                    title=title,
                    file_path=str(file),
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    download_url=f"/reports/{file.name}"
                )
            )
    return reports


@router.get("/{filename}", response_model=ReportDetailResponse, summary="Get report markdown content by filename")
async def get_report(filename: str):
    """
    Fetch the complete Markdown report content and file metadata.
    """
    file_path = settings.REPORTS_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{filename}' not found."
        )

    content = file_path.read_text(encoding="utf-8")
    stat = file_path.stat()
    title = file_path.stem.replace("_report", "").replace("_", " ").title()

    metadata = ReportMetadata(
        filename=file_path.name,
        title=title,
        file_path=str(file_path),
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        download_url=f"/reports/{file_path.name}"
    )

    return ReportDetailResponse(
        filename=filename,
        content=content,
        metadata=metadata
    )


@router.delete("/{filename}", summary="Delete a report file")
async def delete_report(filename: str):
    """
    Deletes a generated report from the storage/reports directory.
    """
    file_path = settings.REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{filename}' does not exist."
        )
    file_path.unlink()
    return {"message": f"Report '{filename}' successfully deleted."}
