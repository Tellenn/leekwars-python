#!/usr/bin/env python3
"""Rafraîchit le snapshot local de l'encyclopédie Leek Wars (fr).

Source : https://leekwars.com/api/encyclopedia/get/fr/<page>
Écrit les pages dans docs/encyclopedia/<slug>.md.

Usage :
    python3 tools/sync_encyclopedia.py            # pages par défaut
    python3 tools/sync_encyclopedia.py Force Agilité
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://leekwars.com/api/encyclopedia/get/fr/{}"
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "encyclopedia",
)

DEFAULT_PAGES = [
    "Force",
    "Agilité",
    "Résistance",
    "Sagesse",
    "Effets",
    "Vol de vie",
    "Points de Vie",
    "Érosion",
    "Armes",
    "Puces",
]

HEADER = """<!-- Snapshot local de l'encyclopédie Leek Wars (fr) :
     source : https://leekwars.com/api/encyclopedia/get/fr/{page}
     rafraîchissable via `python3 tools/sync_encyclopedia.py` -->

"""


def slugify(title):
    """'Points de Vie' -> 'points_de_vie' (ASCII, minuscules, underscores)."""
    normalized = title.lower()
    normalized = normalized.replace("é", "e").replace("è", "e")
    normalized = normalized.replace("ê", "e").replace("à", "a")
    normalized = normalized.replace("ç", "c").replace("û", "u")
    normalized = normalized.replace("ô", "o")
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def fetch(page):
    url = BASE_URL.format(urllib.parse.quote(page))
    request = urllib.request.Request(url, headers={"User-Agent": "leekwars-python"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv):
    pages = argv[1:] or DEFAULT_PAGES
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = []
    for page in pages:
        try:
            payload = fetch(page)
        except (urllib.error.URLError, json.JSONDecodeError) as error:
            failures.append((page, str(error)))
            print("ECHEC  {} : {}".format(page, error))
            continue
        target = os.path.join(OUT_DIR, slugify(payload["title"]) + ".md")
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(HEADER.format(page=payload["title"]))
            handle.write(payload["content"])
        print("OK     {} -> {}".format(payload["title"], target))
        time.sleep(0.3)
    if failures:
        print("\n{} page(s) en échec.".format(len(failures)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
