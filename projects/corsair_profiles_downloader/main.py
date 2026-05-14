import sys
from pathlib import Path
from typing import TypedDict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from shared.logger import setup_logger

BASE_URL: str = "https://lewisgerschwitz.com/corsair.html"
DOMAIN: str = "https://lewisgerschwitz.com"
_HERE: Path = Path(__file__).parent
DOWNLOAD_DIR: Path = _HERE / "Corsair_Profiles_Collection"

log = setup_logger("corsair_downloader", "corsair_downloader.log")


def sanitize_path(name: str) -> str:
    invalid_chars = r'<>:"|?*\/\\'
    for char in invalid_chars:
        name = name.replace(char, "-")
    return name.strip()


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
    )
    retries = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class ReadmeData(TypedDict):
    name: str
    version: str
    category: str
    youtube_url: str
    profiles_list: str


def download_file(session: requests.Session, url: str, folder: Path) -> None:
    if not url:
        return
    file_name: str = url.split("/")[-1]
    local_filename: Path = folder / file_name

    if local_filename.exists():
        log.info("SKIP     %s (already exists)", file_name)
        return

    log.info("DOWNLOAD %s", file_name)
    try:
        with session.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with local_filename.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    file_handle.write(chunk)
        log.debug("OK       %s -> %s", file_name, local_filename)
    except Exception as exc:
        log.error("FAILED   %s | %s", url, exc)


def create_readme(path: Path, data: ReadmeData) -> None:
    readme_content: str = f"""# {data['name']}

## General Information
- Required iCUE version: `{data['version']}`
- Category: {data['category']}

## Video Showcase
[Watch on YouTube]({data['youtube_url']})

## Included Profiles
{data['profiles_list']}

---
Profile created by Lewis Gerschwitz. Organized automatically by this Python script.
"""
    (path / "README.md").write_text(readme_content, encoding="utf-8")


def scrape_corsair() -> None:
    log.info("Connecting to %s", BASE_URL)
    session = build_session()
    response = session.get(BASE_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    sections = soup.find_all(["h1", "h2", "h3"])

    for raw_section in sections:
        if not isinstance(raw_section, Tag):
            continue

        category_name: str = raw_section.get_text(strip=True)
        if not any(
            keyword in category_name
            for keyword in (
                "Latest CORSAIR iCUE Profiles",
                "Creator Profile Picks",
                "Profiles List",
            )
        ):
            continue

        log.info("Section: %s", category_name)

        current = raw_section.find_next_sibling()
        while isinstance(current, Tag) and current.name not in ["h1", "h2", "h3"]:
            if current.name == "div" and "corsairdiv" in current.get("class", []):
                main_link_tag = current.find("a", class_="corsairlink")
                if not isinstance(main_link_tag, Tag):
                    current = current.find_next_sibling()
                    continue

                full_name: str = main_link_tag.get_text(strip=True).replace(" Download", "")
                profile_name: str = full_name.split(" - ")[0]

                version_tag = current.find("p", class_="whitetxt")
                if isinstance(version_tag, Tag):
                    version_text = version_tag.get_text(strip=True).replace("Version:", "").strip()
                else:
                    version_text = "Unknown"
                major_version: str = version_text.split(".")[0] if "." in version_text else "iCUE"

                youtube_tag = current.find(
                    "a",
                    href=lambda href_value: bool(href_value and "youtube.com" in href_value),
                )
                youtube_url: str = (
                    str(youtube_tag.get("href", "Not available"))
                    if isinstance(youtube_tag, Tag)
                    else "Not available"
                )

                profiles_tag = current.find(
                    "p",
                    string=lambda value: bool(value and "Profiles:" in value),
                )
                if isinstance(profiles_tag, Tag):
                    clean_list: str = profiles_tag.get_text(strip=True).replace("Profiles:", "").strip()
                    formatted_list: str = "\n".join(
                        "- " + item.strip().replace("'", "") for item in clean_list.split(",")
                    )
                else:
                    formatted_list = "- Standard profile included"

                profile_path: Path = (
                    DOWNLOAD_DIR
                    / sanitize_path(category_name)
                    / major_version
                    / sanitize_path(profile_name)
                )
                profile_path.mkdir(parents=True, exist_ok=True)

                log.info("Profile: %s (v%s)", profile_name, major_version)

                readme_data: ReadmeData = {
                    "name": full_name,
                    "version": version_text,
                    "category": category_name,
                    "youtube_url": youtube_url,
                    "profiles_list": formatted_list,
                }
                create_readme(profile_path, readme_data)

                img_tag = current.find("img")
                if isinstance(img_tag, Tag):
                    img_src = img_tag.get("src")
                    if isinstance(img_src, str):
                        download_file(session, urljoin(DOMAIN, img_src), profile_path)

                all_links = current.find_all("a", href=True)
                for raw_link in all_links:
                    if not isinstance(raw_link, Tag):
                        continue
                    href_value = raw_link.get("href")
                    if isinstance(href_value, str) and href_value.endswith(".zip"):
                        download_file(session, urljoin(DOMAIN, href_value), profile_path)

            current = current.find_next_sibling()


if __name__ == "__main__":
    scrape_corsair()
    log.info("Finished. Profiles saved to '%s'.", DOWNLOAD_DIR)