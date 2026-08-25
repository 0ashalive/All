from flask import Flask, Response
import requests
import re
from datetime import datetime

app = Flask(__name__)

# আপনার PLAYLISTS, SOURCE_CATEGORY_OVERRIDE,
# CATEGORY_MAP, CATEGORY_ORDER ইত্যাদি এখানে রাখুন


def fetch_playlist(url):
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text.replace("\r\n", "\n").split("\n")
    except Exception as e:
        print(f"Failed: {e}")
        return []


def clean_line(line):
    return line.strip()


def extract_channel_blocks(lines):
    block = []

    for line in lines:
        line = clean_line(line)

        if not line:
            continue

        if line.startswith("#EXTM3U"):
            continue

        if line.startswith("#EXTINF") and block:
            yield block
            block = []

        block.append(line)

    if block:
        yield block


def get_channel_title(block):
    for line in block:
        if line.startswith("#EXTINF"):
            parts = line.rsplit(",", 1)

            if len(parts) > 1:
                return parts[1].strip()

    return None


def categorize_channel(title):
    if not title:
        return DEFAULT_CATEGORY

    title_lower = title.lower()

    for category, keywords in CATEGORY_MAP.items():
        for kw in keywords:
            if kw in title_lower:
                return category

    return DEFAULT_CATEGORY


def fix_channel_block(block, category):
    new_block = []

    for line in block:
        if line.startswith("#EXTINF"):

            if "group-title=" in line:
                line = re.sub(
                    r'group-title="[^"]*"',
                    f'group-title="{category}"',
                    line
                )
            else:
                line = re.sub(
                    r'(#EXTINF:[^,]+)',
                    r'\1 group-title="' + category + '"',
                    line
                )

        new_block.append(line)

    return new_block


def generate_playlist():

    all_channels = []

    for playlist in PLAYLISTS:

        name = playlist["name"]
        url = playlist["url"]

        lines = fetch_playlist(url)

        if not lines:
            continue

        override_cat = SOURCE_CATEGORY_OVERRIDE.get(name)

        for block in extract_channel_blocks(lines):

            if override_cat:
                category = override_cat
            else:
                title = get_channel_title(block)
                category = categorize_channel(title)

            all_channels.append((category, block))


    groups = {}

    for cat, block in all_channels:
        groups.setdefault(cat, []).append(block)


    ordered_cats = []

    for cat in CATEGORY_ORDER:
        if cat in groups:
            ordered_cats.append(cat)

    remaining = sorted(
        [
            cat for cat in groups.keys()
            if cat not in CATEGORY_ORDER
        ]
    )

    ordered_cats.extend(remaining)


    EPG_URL = "https://www.tsepg.cf/epg.xml.gz"

    out_lines = [
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]

    for cat in ordered_cats:

        blocks = groups[cat]

        out_lines.append(
            f"#===== {cat} ({len(blocks)} channels) ====="
        )

        for block in blocks:

            fixed = fix_channel_block(block, cat)

            out_lines.extend(fixed)
            out_lines.append("")


    while out_lines and out_lines[-1] == "":
        out_lines.pop()

    return "\n".join(out_lines)


@app.route("/")
def home():
    return {
        "status": "success",
        "message": "M3U Playlist API is working"
    }


@app.route("/playlist.m3u")
def playlist():

    m3u = generate_playlist()

    return Response(
        m3u,
        mimetype="audio/x-mpegurl",
        headers={
            "Content-Disposition": "inline; filename=combined.m3u"
        }
    )


if __name__ == "__main__":
    app.run()
