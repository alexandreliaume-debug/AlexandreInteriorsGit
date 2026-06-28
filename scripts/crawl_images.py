#!/usr/bin/env python3
"""Download all images from alexandreinteriors.com into the Astro repo."""

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO_IMAGES = Path("/Users/alexandreliaume/projects/AlexandreInteriorsGit/public/images")
MANIFEST = REPO_IMAGES / "manifest.json"

SEED_URLS = [
    "https://www.alexandreinteriors.com/",
    "https://www.alexandreinteriors.com/about",
    "https://www.alexandreinteriors.com/services",
    "https://www.alexandreinteriors.com/portfolio",
    "https://www.alexandreinteriors.com/russell-square-flat",
    "https://www.alexandreinteriors.com/portfolio/hoxton",
    "https://www.alexandreinteriors.com/inspiration",
    "https://www.alexandreinteriors.com/blog",
    "https://www.alexandreinteriors.com/press",
    "https://www.alexandreinteriors.com/contact-us",
]

PAGE_HOSTS = {"www.alexandreinteriors.com", "alexandreinteriors.com"}
IMAGE_HOSTS = {
    "images.squarespace-cdn.com",
    "static1.squarespace.com",
    "static.squarespace.com",
}

USER_AGENT = "Mozilla/5.0 (compatible; AlexandreInteriorsImageCrawler/1.0)"
DELAY = 0.35

IMAGE_URL_RE = re.compile(
    r"https?://(?:images\.squarespace-cdn\.com|static1\.squarespace\.com|static\.squarespace\.com)[^\s\"'<>\\)]+",
    re.I,
)


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
            if part and ("http" in part or part.startswith("//")):
                self.links.add(part.split()[0] if part.startswith("http") else part)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def normalize_page_url(url, base):
    url = url.strip()
    if not url or url.startswith(("#", "mailto:", "tel:")):
        return None
    if url.startswith("//"):
        url = "https:" + url
    absolute = urllib.parse.urljoin(base, url)
    parsed = urllib.parse.urlparse(absolute)
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc not in PAGE_HOSTS:
        return None
    clean = parsed._replace(fragment="", query="")
    return urllib.parse.urlunparse(clean)


def normalize_image_url(url, base=""):
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith("http"):
        url = urllib.parse.urljoin(base, url)
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in IMAGE_HOSTS:
        return None
    # Prefer highest quality: strip ?format= query but keep path
    path = parsed.path
    if not re.search(r"\.(jpe?g|png|webp|gif|ico|svg)$", path, re.I):
        return None
    return urllib.parse.urlunparse(parsed._replace(query="", fragment=""))


def repo_path_for_url(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path
    marker = "/content/v1/5950d1166a49632befa5c629/"
    if marker in path:
        rel = path.split(marker, 1)[1]
    else:
        rel = path.lstrip("/")
    parts = rel.split("/")
    if len(parts) >= 2:
        folder, filename = parts[0], "/".join(parts[1:])
    else:
        folder, filename = "misc", rel
    filename = re.sub(r"_[0-9a-f]{8}(?=\.[^.]+$)", "", filename)
    filename = re.sub(r"[^a-zA-Z0-9._-]+", "-", filename).strip("-")
    return REPO_IMAGES / folder / filename


def collect_image_urls(html, base):
    urls = set()
    for match in IMAGE_URL_RE.findall(html):
        normalized = normalize_image_url(match, base)
        if normalized:
            urls.add(normalized)
    for match in re.findall(r'//images\.squarespace-cdn\.com[^"\'\s<>\\]+', html):
        normalized = normalize_image_url("https:" + match, base)
        if normalized:
            urls.add(normalized)
    return urls


def main():
    REPO_IMAGES.mkdir(parents=True, exist_ok=True)
    queue = list(SEED_URLS)
    seen_pages = set()
    image_urls = set()
    manifest = {"pages": [], "images": [], "errors": []}

    while queue:
        page = queue.pop(0)
        if page in seen_pages:
            continue
        seen_pages.add(page)
        try:
            data, _ = fetch(page)
            html = data.decode("utf-8", errors="replace")
            manifest["pages"].append(page)
            image_urls.update(collect_image_urls(html, page))

            parser = LinkExtractor()
            parser.feed(html)
            for link in parser.links:
                normalized = normalize_page_url(link, page)
                if normalized and normalized not in seen_pages and normalized not in queue:
                    if normalized.startswith("https://www.alexandreinteriors.com/"):
                        queue.append(normalized)

            print(f"PAGE {len(seen_pages):02d} {page} (+{len(image_urls)} images total)")
            time.sleep(DELAY)
        except Exception as exc:
            manifest["errors"].append({"url": page, "error": str(exc)})
            print(f"ERROR page {page}: {exc}")

    print(f"\nDownloading {len(image_urls)} images...")
    content_hashes = {}
    downloaded = 0
    skipped = 0

    for i, url in enumerate(sorted(image_urls), 1):
        dest = repo_path_for_url(url)
        try:
            if dest.exists() and dest.stat().st_size > 0:
                skipped += 1
                manifest["images"].append({"url": url, "path": str(dest.relative_to(REPO_IMAGES.parent)), "status": "exists"})
                continue

            data, content_type = fetch(url)
            if len(data) < 200:
                continue

            digest = hashlib.sha256(data).hexdigest()
            if digest in content_hashes:
                manifest["images"].append({
                    "url": url,
                    "path": str(content_hashes[digest].relative_to(REPO_IMAGES.parent)),
                    "status": "duplicate",
                })
                skipped += 1
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            content_hashes[digest] = dest
            downloaded += 1
            manifest["images"].append({
                "url": url,
                "path": str(dest.relative_to(REPO_IMAGES.parent)),
                "bytes": len(data),
                "content_type": content_type,
                "status": "downloaded",
            })
            if i % 10 == 0:
                print(f"  {i}/{len(image_urls)} downloaded={downloaded} skipped={skipped}")
            time.sleep(DELAY / 2)
        except Exception as exc:
            manifest["errors"].append({"url": url, "error": str(exc)})
            print(f"ERROR image {url}: {exc}")

    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. Pages: {len(seen_pages)}, Images: {len(image_urls)}, New: {downloaded}, Skipped: {skipped}")
    print(f"Repo images: {sum(1 for _ in REPO_IMAGES.rglob('*') if _.is_file() and _.name != 'manifest.json')}")


if __name__ == "__main__":
    main()
