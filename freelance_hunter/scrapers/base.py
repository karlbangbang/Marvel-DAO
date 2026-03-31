"""Classe de base pour tous les scrapers de plateformes freelance."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

import requests
from fake_useragent import UserAgent

from freelance_hunter.models import FreelanceProfile, Mission

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Classe abstraite pour scraper les plateformes freelance."""

    PLATFORM_NAME: str = "unknown"
    BASE_URL: str = ""
    RATE_LIMIT_SECONDS: float = 2.0

    def __init__(self):
        self.session = requests.Session()
        try:
            ua = UserAgent()
            self.session.headers.update({"User-Agent": ua.random})
        except Exception:
            self.session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            })
        self._last_request_time = 0.0

    def _rate_limit(self):
        """Respecte un délai minimum entre les requêtes."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.RATE_LIMIT_SECONDS:
            time.sleep(self.RATE_LIMIT_SECONDS - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str, params: Optional[dict] = None) -> Optional[requests.Response]:
        """Effectue une requête GET avec rate limiting et gestion d'erreurs."""
        self._rate_limit()
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"[{self.PLATFORM_NAME}] Erreur requête {url}: {e}")
            return None

    @abstractmethod
    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        """Recherche des missions correspondant au profil donné."""
        ...

    @abstractmethod
    def _build_search_url(self, profile: FreelanceProfile) -> str:
        """Construit l'URL de recherche à partir du profil."""
        ...

    @abstractmethod
    def _parse_results(self, html: str) -> list[Mission]:
        """Parse le HTML des résultats de recherche en liste de missions."""
        ...

    def _build_keywords(self, profile: FreelanceProfile) -> str:
        """Construit une chaîne de mots-clés à partir du profil."""
        keywords = [profile.title] + profile.skills[:3]
        return " ".join(keywords)
