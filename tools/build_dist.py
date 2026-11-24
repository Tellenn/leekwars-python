#!/usr/bin/env python3
"""Assemble le dossier à importer dans Leek Wars (dist/leekwars/).

Copie uniquement ce que le moteur exécute :
    Kepo_solo.py
    libs/__init__.py + libs/*.py

Puis vérifie que le code de l'IA ne dépend d'aucun module local-only
(leekwars_api, pytest, ...) ni d'un module standard hors bac à sable
(os, sys, subprocess, socket, ...).

Usage :
    python3 tools/build_dist.py
"""

import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist", "leekwars")

#: Point d'entrée de l'IA (le moteur exécute ce fichier de l'IA).
ENTRY_POINT = "Kepo_solo.py"

# Modules qui n'existent pas sur Leek Wars (local-only).
FORBIDDEN_IMPORTS = {
    "leekwars_api",
    "pytest",
    "unittest",
    "nose",
    "hypothesis",
    "requests",
    "numpy",
    "pandas",
}

# Modules standard interdits dans le bac à sable Leek Wars (disque/réseau).
FORBIDDEN_STDLIB = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "http",
    "urllib",
    "ssl",
    "multiprocessing",
    "ctypes",
    "importlib",
}

IMPORT_RE = re.compile(
    r"^\s*(?:from\s+([A-Za-z_][\w.]*)\s+import|import\s+([A-Za-z_][\w.]*))",
    re.MULTILINE,
)


def collect_sources():
    sources = [os.path.join(ROOT, ENTRY_POINT)]
    libs_dir = os.path.join(ROOT, "libs")
    for name in sorted(os.listdir(libs_dir)):
        if name.endswith(".py"):
            sources.append(os.path.join(libs_dir, name))
    return sources


def check_imports(sources):
    problems = []
    for path in sources:
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        for match in IMPORT_RE.finditer(content):
            module = match.group(1) or match.group(2)
            root = module.split(".")[0]
            if root in FORBIDDEN_IMPORTS:
                problems.append(
                    "{}: import interdit (local-only) : {}".format(
                        os.path.relpath(path, ROOT), module
                    )
                )
            elif root in FORBIDDEN_STDLIB:
                problems.append(
                    "{}: module standard indisponible sur Leek Wars : {}".format(
                        os.path.relpath(path, ROOT), module
                    )
                )
    return problems


def main():
    sources = collect_sources()
    problems = check_imports(sources)
    if problems:
        print("Imports non autorisés dans le code de l'IA :")
        for problem in problems:
            print("  - " + problem)
        return 1

    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "libs"), exist_ok=True)

    total = 0
    for path in sources:
        relative = os.path.relpath(path, ROOT)
        target = os.path.join(DIST, relative)
        shutil.copy2(path, target)
        size = os.path.getsize(target)
        total += size
        print("  {} ({:>6} o)".format(relative, size))

    print("\n{} fichier(s), {} o au total -> {}".format(
        len(sources), total, os.path.relpath(DIST, ROOT)))
    print("Copie ce dossier dans l'éditeur Leek Wars (racine de l'IA).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
