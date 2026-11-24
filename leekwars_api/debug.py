"""Journal de combat (`Debug`).

`Debug.log` alimente `fight.logs` ; les autres fonctions (marks, pause...) ne
font rien dans le mock, comme le demande le contrat.
"""

from __future__ import annotations

from typing import Any, Optional

from . import state


class Debug:
    """Namespace `Debug` du SDK."""

    @staticmethod
    def log(value: Any, color: Optional[int] = None) -> None:
        """Écrit `str(value)` dans le journal du combat courant."""
        del color  # la couleur n'a pas de sens hors du rendu du site
        fight = state.get_fight()
        if fight is not None:
            fight.logs.append(str(value))

    @staticmethod
    def mark(cells, color: Optional[int] = None, duration: int = 0) -> bool:
        """Marque des cases (no-op dans le mock)."""
        del cells, color, duration
        return True

    @staticmethod
    def markText(cells, text: Any, color: Optional[int] = None, duration: int = 0) -> bool:
        """Marque des cases avec un texte (no-op dans le mock)."""
        del cells, text, color, duration
        return True

    @staticmethod
    def clearMarks() -> None:
        """Efface les marques (no-op)."""

    @staticmethod
    def show(cell, color: Optional[int] = None) -> bool:
        """Affiche une case (no-op)."""
        del cell, color
        return True

    @staticmethod
    def pause() -> None:
        """Met le combat en pause (no-op)."""


__all__ = ["Debug"]
