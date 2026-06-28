#!/usr/bin/env python3
"""Audit image references on alexandreinteriors.com against files in public/images/."""

import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_IMAGES = REPO_ROOT / "public" / "images"
MANIFEST = REPO_IMAGES / "manifest.json"
SITE = "https://www.alexandreinteriors.com"

SEED_URLS = [
    f"{SITE}/",
    f"{SITE}/about",
    f"{SITE}/services",
    f"{SITE}/portfolio",
    f"{SITE}/russell-square-flat",
    f"{SITE}/portfolio/hoxton",
    f"{SITE}/inspiration",
    f"{SITE}/blog",
    f"{SITE}/press",
    f"{SITE}/contact-us",
]

PAGE_HOSTS = {"www.alexandreinteriors.com", "alexandreinteriors.com"}
USER_AGENT = "Mozilla/5.0 (compatible; AlexandreInteriorsImageAudit/1.0)"
DELAY = 0.35

IMAGE_PATH_RE = re.compile(r"/images/[^\s\"'<>\\)]+\.(?:jpe?g|png|webp|gif|ico|svg)", re.I)


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.add(attrs["href"])
        for key in ("src", "data-src", "data-image", "srcset", "data-srcset", "content"):
            if key in attrs and attrs[key]:
                self._scan(attrs[key])
        if tag == "source" and "srcset" in attrs:
            self._scan(attrs["srcset"])
        style = attrs.get("style", "")
        if "url(" in style:
            for match in re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", style):
                self._scan(match)

    def _scan(self, value):
        for part in re.split(r"[\s,]+", value):
            part = part.strip()
            if part:
                self.links.add(part.split()[0] if part.startswith("http") else part)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def normalize_page_url(url, base):
    url = url.strip()
    if not url or url.startswith(("#", "mailto:", "tel:")):
        return None
    if url.startswith("//"):
        url = "https:" + url
    absolute = urllib.parse.urljoin(base, url)
    parsed = urllib.parse.urlparse(absolute)
    if parsed.scheme not in ("http", "https") or parsed.netloc not in PAGE_HOSTS:
        return None
    return urllib.parse.urlunparse(parsed._replace(fragment="", query=""))


def collect_image_paths(html):
    paths = set()
    for match in IMAGE_PATH_RE.findall(html):
        path = match.split("?")[0]
        paths.add(path)
    return paths


def local_path_for_url_path(path):
    if not path.startswith("/images/"):
        return None
    return REPO_ROOT / "public" / path.lstrip("/")


def main():
    queue = list(SEED_URLS)
    seen_pages = set()
    referenced_paths = set()
    manifest = {"site": SITE, "pages": [], "images": [], "missing": [], "errors": []}

    while queue:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            html = fetch(page)
            manifest["pages"].append(page)
            referenced_paths.update(collect_image_paths(html))

            parser = LinkExtractor()
            parser.feed(html)
            for link in parser.links:
                normalized = normalize_page_url(link, page)
                if normalized and normalized not in seen_pages and normalized not in queue:
                    if normalized.startswith(f"{SITE}/"):
                        queue.append(normalized)

            print(f"PAGE {len(seen_pages):02d} {page} (+{len(referenced_paths)} images total)")
            time.sleep(DELAY)
        except Exception as exc:
            manifest["errors"].append({"url": page, "error": str(exc)})
            print(f"ERROR page {page}: {exc}")

    for path in sorted(referenced_paths):
        local = local_path_for_url_path(path)
        entry = {"path": path.lstrip("/"), "url": f"{SITE}{path}"}
        if local and local.exists():
            entry["status"] = "ok"
            entry["bytes"] = local.stat().st_size
        else:
            entry["status"] = "missing"
            manifest["missing"].append(entry)
        manifest["images"].append(entry)

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        f"\nDone. Pages: {len(seen_pages)}, Referenced images: {len(referenced_paths)}, "
        f"Missing: {len(manifest['missing'])}"
    )


if __name__ == "__main__":
    main()
