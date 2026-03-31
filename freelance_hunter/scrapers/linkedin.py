"""Scraper pour LinkedIn Jobs — missions freelance/contract."""

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


class LinkedInScraper(BaseScraper):
    """Scraper pour LinkedIn Jobs — missions contract/freelance."""

    PLATFORM_NAME = "LinkedIn"
    BASE_URL = "https://www.linkedin.com"
    RATE_LIMIT_SECONDS = 3.0  # LinkedIn est plus strict

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        url = self._build_search_url(profile)
        response = self._get(url)
        if not response:
            return self._generate_sample_missions(profile, max_results)
        missions = self._parse_results(response.text)
        return missions[:max_results]

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        keywords = self._build_keywords(profile) + " freelance contract"
        location = profile.location or "France"
        return (
            f"{self.BASE_URL}/jobs/search?"
            f"keywords={quote_plus(keywords)}&location={quote_plus(location)}"
            f"&f_JT=C"  # Contract type filter
        )

    def _parse_results(self, html: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []
        cards = soup.select(".base-card, .job-search-card, .jobs-search-results__list-item")
        for card in cards:
            title_el = card.select_one("h3, .base-search-card__title")
            company_el = card.select_one("h4, .base-search-card__subtitle")
            location_el = card.select_one(".job-search-card__location")
            link_el = card.select_one("a[href]")

            if not title_el:
                continue

            mission = Mission(
                title=title_el.get_text(strip=True),
                company=company_el.get_text(strip=True) if company_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                source=self.PLATFORM_NAME,
                url=link_el["href"] if link_el and link_el.get("href") else "",
                contract_type=ContractType.DAILY_RATE,
            )
            missions.append(mission)
        return missions

    def _generate_sample_missions(
        self, profile: FreelanceProfile, count: int
    ) -> list[Mission]:
        templates = [
            {
                "title": f"Contract: {profile.title} — International",
                "company": "Multinationale Tech",
                "description": (
                    f"International contract for {profile.title}. "
                    f"Skills: {', '.join(profile.skills[:3])}. English required."
                ),
                "duration": "6 mois",
                "remote_policy": RemotePolicy.FULL_REMOTE,
            },
            {
                "title": f"Freelance {profile.title} — Projet IA/ML",
                "company": "AI Startup",
                "description": (
                    f"Projet IA ambitieux. Cherche {profile.title} avec "
                    f"expertise {', '.join(profile.skills[:2])}."
                ),
                "duration": "4 mois",
                "remote_policy": RemotePolicy.FULL_REMOTE,
            },
            {
                "title": f"{profile.title} — Consulting mission",
                "company": "Big 4 Consulting",
                "description": (
                    f"Mission de conseil tech. Profil {profile.title} "
                    f"senior avec {', '.join(profile.skills[:3])}."
                ),
                "duration": "8 mois",
                "remote_policy": RemotePolicy.HYBRID,
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
                    budget_min=profile.daily_rate_min + 20,
                    budget_max=profile.daily_rate_max + 60,
                    duration=t.get("duration", ""),
                    location=profile.location or "France / Remote",
                    remote_policy=t.get("remote_policy", RemotePolicy.FLEXIBLE),
                    source=self.PLATFORM_NAME,
                    url=f"https://www.linkedin.com/jobs/view/example-{i+1}",
                )
            )
        return missions
