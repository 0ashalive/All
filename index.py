from flask import Flask, Response, jsonify
import requests
import re
from datetime import datetime

app = Flask(__name__)

# =========================================================
# PLAYLISTS
# =========================================================

PLAYLISTS = [
    {"name": "Live Events", "icon": "📺", "url": "https://l3.streamstar18.workers.dev"},
    {"name": "FANCODE", "icon": "🏏", "url": "https://raw.githubusercontent.com/drmlive/fancode-live-events/refs/heads/main/fancode.m3u"},
    {"name": "SONYLIV", "icon": "📺", "url": "https://raw.githubusercontent.com/drmlive/sliv-live-events/refs/heads/main/sonyliv.m3u"},
    {"name": "WILLOW", "icon": "🏏", "url": "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/live_sports.m3u"},
    {"name": "PRIMEVIDEO", "icon": "📺", "url": "https://raw.githubusercontent.com/srhady/willow-event/refs/heads/main/primevideo_sports.m3u"},
    {"name": "AXSPORTS", "icon": "🏏", "url": "https://raw.githubusercontent.com/srhady/axsports/refs/heads/main/playlist.m3u"},
    {"name": "JIO-TV", "icon": "📡", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/jtvplus6.m3u"},
    {"name": "ZEE", "icon": "📺", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/zee.m3u"},
    {"name": "SONY", "icon": "📺", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sony.m3u"},
    {"name": "SUN", "icon": "☀️", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/sun.m3u"},
    {"name": "Jio Hotstar", "icon": "⭐", "url": "https://raw.githubusercontent.com/sportlive18/jio-tv-auto-update-playlist/refs/heads/main/hotstar.m3u"}
]

EPG_URL = "https://www.tsepg.cf/epg.xml.gz"


# =========================================================
# SOURCE CATEGORY OVERRIDE
# =========================================================

SOURCE_CATEGORY_OVERRIDE = {
    "Live Events": "Live Events",
    "FANCODE": "Fancode",
    "SONYLIV": "SonyLIV",
    "Jio Hotstar": "Jio Hotstar",
    "WILLOW": "Willow",
    "PRIMEVIDEO": "Prime Video",
    "AXSPORTS": "AXS",
    "HOTSTAR": "Hotstar",
    "Sports Special": "Sports Special"
}


# =========================================================
# CATEGORY MAP
# =========================================================

CATEGORY_MAP = {
    "Assamese": ["assamese", "asomiya"],
    "Bengali": ["bengali", "bangla", "bn"],
    "Bhojpuri": ["bhojpuri", "bho"],
    "Gujarati": ["gujarati", "guj"],
    "Haryanvi": ["haryanvi"],
    "Kannada": ["kannada", "kn"],
    "Malayalam": ["malayalam", "ml"],
    "Marathi": ["marathi", "mr"],
    "Odia": ["odia", "oriya"],
    "Punjabi": ["punjabi", "pa"],
    "Tamil": ["tamil", "ta"],
    "Telugu": ["telugu", "te"],
    "Urdu": ["urdu"],
    "English": ["english", "en"],
    "French": ["french", "fr"],

    "Sun": [
        "sun tv",
        "surya",
        "sun music",
        "sun news",
        "sun action",
        "sun life"
    ],

    "Zee": [
        "zee",
        "zee tv",
        "zee cinema",
        "zee news",
        "zee marathi",
        "zee bangla"
    ],

    "Sony": [
        "sony",
        "set",
        "sab",
        "sony liv",
        "sony max"
    ],

    "Star": [
        "star",
        "star plus",
        "star sports",
        "star movies",
        "star gold"
    ],

    "Colors": [
        "colors",
        "viacom",
        "mtv"
    ],

    "Discovery": [
        "discovery",
        "dci"
    ],

    "Nat Geo": [
        "nat geo",
        "national geographic"
    ],

    "Cartoon": [
        "cartoon",
        "cn",
        "pogo",
        "nick"
    ],

    "News": [
        "news",
        "ndtv",
        "republic",
        "times now",
        "cnn",
        "bbc"
    ],

    "Cricket": [
        "cricket"
    ],

    "Football": [
        "football",
        "soccer"
    ],

    "Boxing": [
        "boxing"
    ],

    "Baseball": [
        "baseball"
    ],

    "Business": [
        "business",
        "finance",
        "cnbc",
        "bloomberg"
    ],

    "Devotional": [
        "devotional",
        "bhakti",
        "god"
    ],

    "Entertainment": [
        "entertainment",
        "ent",
        "tv",
        "movies",
        "series"
    ],

    "Infotainment": [
        "infotainment",
        "documentary",
        "history",
        "discovery",
        "national geographic"
    ],

    "Knowledge": [
        "knowledge",
        "learning",
        "education"
    ]
}

DEFAULT_CATEGORY = "Other"


# =========================================================
# CATEGORY ORDER
# =========================================================

CATEGORY_ORDER = [
    "Sports Special",
    "Live Events",
    "Fancode",
    "SonyLIV",
    "Willow",
    "Prime Video",
    "AXS",
    "Hotstar",
    "Jio Hotstar"
]


# =========================================================
# FETCH PLAYLIST
# =========================================================

def fetch_playlist(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        return response.text.replace(
            "\r\n",
            "\n"
        ).split("\n")

    except Exception as e:

        print(f"Playlist fetch failed: {url}")
        print(str(e))

        return []


# =========================================================
# CLEAN LINE
# =========================================================

def clean_line(line):
    return line.strip()


# =========================================================
# EXTRACT CHANNEL BLOCKS
# =========================================================

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


# =========================================================
# CHANNEL TITLE
# =========================================================

def get_channel_title(block):

    for line in block:

        if line.startswith("#EXTINF"):

            parts = line.rsplit(",", 1)

            if len(parts) > 1:
                return parts[1].strip()

    return None


# =========================================================
# CATEGORY
# =========================================================

def categorize_channel(title):

    if not title:
        return DEFAULT_CATEGORY

    title_lower = title.lower()

    for category, keywords in CATEGORY_MAP.items():

        for keyword in keywords:

            if keyword in title_lower:
                return category

    return DEFAULT_CATEGORY


# =========================================================
# FIX GROUP TITLE
# =========================================================

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


# =========================================================
# GENERATE M3U
# =========================================================

def generate_playlist():

    all_channels = []

    for playlist in PLAYLISTS:

        name = playlist["name"]
        url = playlist["url"]

        print(f"Processing: {name}")

        lines = fetch_playlist(url)

        if not lines:
            continue

        override_category = SOURCE_CATEGORY_OVERRIDE.get(name)

        for block in extract_channel_blocks(lines):

            if override_category:

                category = override_category

            else:

                title = get_channel_title(block)

                category = categorize_channel(title)

            all_channels.append(
                (category, block)
            )


    # =====================================================
    # GROUP CHANNELS
    # =====================================================

    groups = {}

    for category, block in all_channels:

        if category not in groups:
            groups[category] = []

        groups[category].append(block)


    # =====================================================
    # ORDER CATEGORIES
    # =====================================================

    ordered_categories = []

    for category in CATEGORY_ORDER:

        if category in groups:

            ordered_categories.append(category)


    remaining = sorted(
        category
        for category in groups
        if category not in CATEGORY_ORDER
    )

    ordered_categories.extend(remaining)


    # =====================================================
    # BUILD M3U
    # =====================================================

    output = [
        f'#EXTM3U x-tvg-url="{EPG_URL}"'
    ]

    total_channels = 0

    for category in ordered_categories:

        blocks = groups[category]

        total_channels += len(blocks)

        output.append(
            f"#===== {category} ({len(blocks)} channels) ====="
        )

        for block in blocks:

            fixed_block = fix_channel_block(
                block,
                category
            )

            output.extend(fixed_block)

            output.append("")


    while output and output[-1] == "":
        output.pop()


    return "\n".join(output), total_channels, ordered_categories


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "status": "online",
        "service": "M3U Playlist Generator",
        "playlist": "/playlist.m3u",
        "updated": datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    })


# =========================================================
# M3U ENDPOINT
# =========================================================

@app.route("/playlist.m3u")
def playlist():

    try:

        m3u, total, categories = generate_playlist()

        return Response(
            m3u,
            status=200,
            mimetype="audio/x-mpegurl",
            headers={
                "Content-Disposition":
                    "inline; filename=combined.m3u",
                "Cache-Control":
                    "no-cache, no-store, must-revalidate"
            }
        )

    except Exception as e:

        return Response(
            f"# M3U generation error\n# {str(e)}",
            status=500,
            mimetype="text/plain"
        )


# =========================================================
# VERCEL ENTRY POINT
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
