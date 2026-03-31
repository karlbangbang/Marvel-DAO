"""API Remotive.com — offres remote gratuites, sans clé API."""

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


class RemotiveScraper(BaseScraper):
    """Remotive.com — API gratuite, pas de clé requise."""

    PLATFORM_NAME = "Remotive"
    BASE_URL = "https://remotive.com"
    API_URL = "https://remotive.com/api/remote-jobs"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        for term in self._get_search_terms(profile):
            response = self._get(self.API_URL, params={
                "search": term,
                "limit": max_results,
            })
            if response:
                try:
                    data = response.json()
                    missions = self._parse_api(data)
                    if missions:
                        return missions[:max_results]
                except Exception as e:
                    logger.warning(f"[{self.PLATFORM_NAME}] Parse error: {e}")

        return []

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        return f"{self.API_URL}?search={self._build_keywords(profile)}"

    def _parse_results(self, html: str) -> list[Mission]:
        return []

    def _get_search_terms(self, profile: FreelanceProfile) -> list[str]:
        terms = [profile.title]
        for skill in profile.skills[:4]:
            terms.append(skill)
        terms.append("analyst")
        terms.append("finance")
        return terms

    def _parse_api(self, data: dict) -> list[Mission]:
        missions = []
        jobs = data.get("jobs", [])
        for job in jobs:
            title = job.get("title", "")
            if not title:
                continue

            # Extraire le salaire si disponible
            salary_min = 0
            salary_max = 0
            salary = job.get("salary", "")

            # Tags comme compétences
            tags = job.get("tags", []) or []

            description = job.get("description", "")
            # Nettoyer le HTML basique
            if "<" in description:
                from bs4 import BeautifulSoup
                description = BeautifulSoup(description, "html.parser").get_text(separator=" ", strip=True)
            # Tronquer
            description = description[:500] if description else ""

            missions.append(Mission(
                title=title,
                company=job.get("company_name", ""),
                description=description,
                skills_required=tags[:10],
                contract_type=ContractType.DAILY_RATE,
                location=job.get("candidate_required_location", "Worldwide"),
                remote_policy=RemotePolicy.FULL_REMOTE,
                source=self.PLATFORM_NAME,
                url=job.get("url", ""),
                posted_date=job.get("publication_date", ""),
                industry=job.get("category", ""),
            ))

        return missions
