from __future__ import annotations

from shared.logger import setup_logger
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from re import IGNORECASE, MULTILINE, findall, search
from typing import Iterable
from urllib.parse import parse_qs, quote, urlparse

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = setup_logger("corsair_profiles_web")

BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "Corsair_Profiles_Collection"
TEMPLATES_DIR: Path = BASE_DIR / "templates"
STATIC_DIR: Path = BASE_DIR / "static"

app = FastAPI(title="Corsair Profiles Gallery")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/profiles", StaticFiles(directory=DATA_DIR), name="profiles")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "%s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


@dataclass(slots=True)
class Profile:
    title: str
    display_title: str
    category: str
    version: str
    folder_name: str
    relative_path: str
    image_url: str | None
    youtube_url: str | None
    youtube_embed_url: str | None
    included_profiles: list[str]
    zip_files: list[str]


def _extract_readme_data(readme_path: Path) -> tuple[str | None, list[str]]:
    if not readme_path.exists():
        return None, []

    content = readme_path.read_text(encoding="utf-8", errors="ignore")
    youtube_match = search(r"\[Watch on YouTube\]\(([^)]+)\)", content, flags=IGNORECASE)
    youtube_url = youtube_match.group(1).strip() if youtube_match else None

    bullet_items = findall(r"^-\s+(.+)$", content, flags=IGNORECASE | MULTILINE)
    clean_items = [item.strip() for item in bullet_items if item.strip() and "Required iCUE" not in item]
    return youtube_url, clean_items


def _image_for_profile(profile_dir: Path, relative_path: Path) -> str | None:
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
    for file_path in sorted(profile_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in image_exts:
            rel_image = (relative_path / file_path.name).as_posix()
            return f"/profiles/{quote(rel_image, safe='/')}"
    return None


def _zip_files_for_profile(profile_dir: Path, relative_path: Path) -> list[str]:
    zip_links: list[str] = []
    for file_path in sorted(profile_dir.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() == ".zip":
            rel_zip = (relative_path / file_path.name).as_posix()
            zip_links.append(f"/profiles/{quote(rel_zip, safe='/')}")
    return zip_links


def _clean_profile_title(title: str) -> str:
    cleaned = search(r"^(.*?)(?:\s+profile)?$", title.strip(), flags=IGNORECASE)
    if not cleaned:
        return title.strip()
    value = cleaned.group(1).strip()
    return value if value else title.strip()


def _to_youtube_embed_url(youtube_url: str | None) -> str | None:
    if not youtube_url:
        return None

    try:
        parsed = urlparse(youtube_url)
    except Exception:
        return None

    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.strip("/")
    video_id = ""

    if host == "youtu.be" and path:
        video_id = path.split("/")[0]
    elif host in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        if path == "watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif path.startswith("shorts/"):
            video_id = path.split("/")[1] if len(path.split("/")) > 1 else ""
        elif path.startswith("embed/"):
            video_id = path.split("/")[1] if len(path.split("/")) > 1 else ""

    if not video_id:
        return None

    return f"https://www.youtube.com/embed/{video_id}?rel=0"


def load_profiles() -> list[Profile]:
    profiles: list[Profile] = []

    if not DATA_DIR.exists():
        return profiles

    for category_dir in sorted(path for path in DATA_DIR.iterdir() if path.is_dir()):
        category_name = category_dir.name
        for version_dir in sorted(path for path in category_dir.iterdir() if path.is_dir()):
            version_name = version_dir.name
            for profile_dir in sorted(path for path in version_dir.iterdir() if path.is_dir()):
                relative_path = profile_dir.relative_to(DATA_DIR)
                youtube_url, included_profiles = _extract_readme_data(profile_dir / "README.md")
                profiles.append(
                    Profile(
                        title=profile_dir.name,
                        display_title=_clean_profile_title(profile_dir.name),
                        category=category_name,
                        version=version_name,
                        folder_name=profile_dir.name,
                        relative_path=relative_path.as_posix(),
                        image_url=_image_for_profile(profile_dir, relative_path),
                        youtube_url=youtube_url,
                        youtube_embed_url=_to_youtube_embed_url(youtube_url),
                        included_profiles=included_profiles[:6],
                        zip_files=_zip_files_for_profile(profile_dir, relative_path),
                    )
                )

    return profiles


def _filter_profiles(
    profiles: Iterable[Profile],
    query: str,
    category: str,
    version: str,
) -> list[Profile]:
    normalized_query = query.strip().lower()
    filtered: list[Profile] = []

    for profile in profiles:
        if category and category != "All" and profile.category != category:
            continue
        if version and version != "All" and profile.version != version:
            continue

        searchable = " ".join(
            [
                profile.title,
                profile.category,
                profile.version,
                " ".join(profile.included_profiles),
            ]
        ).lower()

        if normalized_query and normalized_query not in searchable:
            continue

        filtered.append(profile)

    return filtered


def _template_context(query: str, category: str, version: str) -> dict[str, object]:
    profiles = load_profiles()
    categories = sorted({profile.category for profile in profiles})
    versions = sorted({profile.version for profile in profiles})
    filtered_profiles = _filter_profiles(profiles, query=query, category=category, version=version)

    return {
        "profiles": [asdict(profile) for profile in filtered_profiles],
        "all_count": len(profiles),
        "visible_count": len(filtered_profiles),
        "categories": categories,
        "versions": versions,
        "active_query": query,
        "active_category": category or "All",
        "active_version": version or "All",
    }


@app.on_event("startup")
def on_startup() -> None:
    profile_count = len(load_profiles())
    logger.info("FastAPI started. Profiles folder: %s", DATA_DIR)
    logger.info("Loaded %s profiles", profile_count)


@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    query: str = Query(default=""),
    category: str = Query(default="All"),
    version: str = Query(default="All"),
) -> HTMLResponse:
    context = _template_context(query=query, category=category, version=version)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
    )


@app.get("/partials/profiles", response_class=HTMLResponse)
def profiles_partial(
    request: Request,
    query: str = Query(default=""),
    category: str = Query(default="All"),
    version: str = Query(default="All"),
) -> HTMLResponse:
    context = _template_context(query=query, category=category, version=version)
    return templates.TemplateResponse(
        request=request,
        name="partials/profiles_grid.html",
        context=context,
    )


@app.get("/api/profiles")
def profiles_api(
    query: str = Query(default=""),
    category: str = Query(default="All"),
    version: str = Query(default="All"),
) -> dict[str, object]:
    context = _template_context(query=query, category=category, version=version)
    return context
