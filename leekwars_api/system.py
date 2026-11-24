"""Informations système (`System`).

Le bac à sable du site n'a ni disque ni réseau : `fileRead` et `getLoadout`
renvoient None, `sendNotification` renvoie False. Les compteurs sont des
valeurs statiques réalistes pour un petit combat.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional


class System:
    """Namespace `System` du SDK."""

    operations = 0
    maxOperations = 20_000_000
    instructionsCount = 0
    usedRAM = 0
    maxRAM = 8_192

    #: Horloge figée à l'import (pas d'accès réseau ni fichier).
    _now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    date = _now.strftime("%d/%m/%Y")
    time = _now.strftime("%H:%M:%S")
    timestamp = int(_now.timestamp())

    @staticmethod
    def fileRead(path: str) -> Optional[str]:
        """Lecture d'un fichier de l'IA : indisponible dans le mock."""
        del path
        return None

    @staticmethod
    def getLoadout(path: str) -> Optional[Any]:
        """Loadout écrit en JSON : indisponible dans le mock."""
        del path
        return None

    @staticmethod
    def sendNotification(title: str, message: str = "") -> bool:
        """Notification à l'éleveur : refusée dans le mock."""
        del title, message
        return False


__all__ = ["System"]
