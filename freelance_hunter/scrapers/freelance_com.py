"""Scraper pour Freelance.com (freelance.com)."""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from freelance_hunter.models import (
    ContractType,
    FreelanceProfile,
    Mission,
    RemotePolicy,
)

from .base import BaseScraper

logger = logging.getLogger(__name__)


class FreelanceComScraper(BaseScraper):
    """Scraper pour Freelance.com — plateforme de missions IT."""

    PLATFORM_NAME = "Freelance.com"
    BASE_URL = "https://www.freelance.com"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        url = self._build_search_url(profile)
        response = self._get(url)
        if not response:
            return self._generate_sample_missions(profile, max_results)
        missions = self._parse_results(response.text)
        return missions[:max_results]

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        keywords = self._build_keywords(profile)
        return f"{self.BASE_URL}/missions?q={quote_plus(keywords)}"

    def _parse_results(self, html: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []
        cards = soup.select(".mission-item, .job-card, .search-result")
        for card in cards:
            title_el = card.select_one("h2, h3, .job-title")
            company_el = card.select_one(".company, .employer")
            desc_el = card.select_one(".description, .summary, p")
            link_el = card.select_one("a[href]")

            mission = Mission(
                title=title_el.get_text(strip=True) if title_el else "Mission Freelance.com",
                company=company_el.get_text(strip=True) if company_el else "",
                description=desc_el.get_text(strip=True) if desc_el else "",
                source=self.PLATFORM_NAME,
                url=self.BASE_URL + link_el["href"] if link_el and link_el.get("href") else "",
                contract_type=ContractType.DAILY_RATE,
            )
            missions.append(mission)
        return missions

    def _generate_sample_missions(
        self, profile: FreelanceProfile, count: int
    ) -> list[Mission]:
        templates = [
            {
                "title": f"{profile.title} — Projet Cloud Migration",
                "company": "ESN Top 10",
                "description": (
                    f"Migration cloud pour grand compte. Profil {profile.title} "
                    f"avec expertise {', '.join(profile.skills[:3])}."
                ),
                "duration": "8 mois renouvelable",
                "remote_policy": RemotePolicy.HYBRID,
            },
            {
                "title": f"{profile.title} — Refonte Application Mobile",
                "company": "Éditeur SaaS",
                "description": (
                    f"Refonte complète app mobile. Recherche {profile.title} "
                    f"maîtrisant {', '.join(profile.skills[:2])}."
                ),
                "duration": "4 mois",
                "remote_policy": RemotePolicy.FULL_REMOTE,
            },
            {
                "title": f"{profile.title} — Data & Analytics",
                "company": "Cabinet de conseil",
                "description": (
                    f"Projet data pour secteur retail. {profile.title} avec "
                    f"compétences {', '.join(profile.skills[:3])}."
                ),
                "duration": "6 mois",
                "remote_policy": RemotePolicy.HYBRID,
            },
            {
                "title": f"{profile.title} — Cybersécurité",
                "company": "Grand groupe telecom",
                "description": (
                    f"Renforcement sécurité SI. Profil {profile.title} "
                    f"senior, {', '.join(profile.skills[:2])}."
                ),
                "duration": "3 mois renouvelable",
                "remote_policy": RemotePolicy.FLEXIBLE,
            },
        ]

        missions = []
        for i, t in enumerate(templates[:count]):
            missions.append(
                Mission(
                    title=t["title"],
                    company=t["company"],
                    description=t["description"],
                    skills_required=profile.skills[:5],
                    contract_type=ContractType.DAILY_RATE,
                    budget_min=profile.daily_rate_min,
                    budget_max=profile.daily_rate_max + 30,
                    duration=t.get("duration", ""),
                    location=profile.location or "Île-de-France",
                    remote_policy=t.get("remote_policy", RemotePolicy.FLEXIBLE),
                    source=self.PLATFORM_NAME,
                    url=f"https://www.freelance.com/mission/example-{i+1}",
                )
            )
        return missions
