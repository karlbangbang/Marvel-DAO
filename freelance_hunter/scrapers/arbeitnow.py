"""API Arbeitnow — offres Europe, gratuite, sans clé API."""

from __future__ import annotations

import logging

from freelance_hunter.models import (
    ContractType,
    FreelanceProfile,
    Mission,
    RemotePolicy,
)
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ArbeitnowScraper(BaseScraper):
    """Arbeitnow.com — API gratuite, jobs Europe, pas de clé requise."""

    PLATFORM_NAME = "Arbeitnow"
    BASE_URL = "https://www.arbeitnow.com"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        # L'API ne supporte pas de paramètre search, on filtre côté client
        response = self._get(self.API_URL)
        if not response:
            return []

        try:
            data = response.json()
            all_jobs = self._parse_api(data)
            # Filtrer par mots-clés du profil
            filtered = self._filter_by_profile(all_jobs, profile)
            return filtered[:max_results]
        except Exception as e:
            logger.warning(f"[{self.PLATFORM_NAME}] Parse error: {e}")
            return []

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        return self.API_URL

    def _parse_results(self, html: str) -> list[Mission]:
        return []

    def _parse_api(self, data: dict) -> list[Mission]:
        missions = []
        jobs = data.get("data", [])
        for job in jobs:
            title = job.get("title", "")
            if not title:
                continue

            tags = job.get("tags", []) or []
            description = job.get("description", "")
            if "<" in description:
                from bs4 import BeautifulSoup
                description = BeautifulSoup(description, "html.parser").get_text(separator=" ", strip=True)
            description = description[:500] if description else ""

            remote = RemotePolicy.FLEXIBLE
            if job.get("remote", False):
                remote = RemotePolicy.FULL_REMOTE

            missions.append(Mission(
                title=title,
                company=job.get("company_name", ""),
                description=description,
                skills_required=tags[:10],
                contract_type=ContractType.DAILY_RATE,
                location=job.get("location", ""),
                remote_policy=remote,
                source=self.PLATFORM_NAME,
                url=job.get("url", ""),
                posted_date=job.get("created_at", ""),
            ))

        return missions

    def _filter_by_profile(self, missions: list[Mission], profile: FreelanceProfile) -> list[Mission]:
        """Filtre les missions par pertinence avec le profil."""
        keywords = set()
        keywords.add(profile.title.lower())
        for skill in profile.skills:
            keywords.add(skill.lower())
        # Ajout de termes connexes
        keywords.update(["analyst", "business", "data", "finance", "excel", "power bi", "reporting"])

        scored = []
        for m in missions:
            text = f"{m.title} {m.description} {' '.join(m.skills_required)}".lower()
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                scored.append((hits, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]
