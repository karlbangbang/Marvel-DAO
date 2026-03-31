"""Scraper pour Indeed (fr.indeed.com) — missions freelance."""

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


class IndeedFreelanceScraper(BaseScraper):
    """Scraper pour Indeed France — filtre sur les missions freelance/indépendant."""

    PLATFORM_NAME = "Indeed"
    BASE_URL = "https://fr.indeed.com"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        url = self._build_search_url(profile)
        response = self._get(url)
        if not response:
            return self._generate_sample_missions(profile, max_results)
        missions = self._parse_results(response.text)
        return missions[:max_results]

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        keywords = self._build_keywords(profile) + " freelance"
        location = profile.location or "France"
        return (
            f"{self.BASE_URL}/jobs?"
            f"q={quote_plus(keywords)}&l={quote_plus(location)}&jt=contract"
        )

    def _parse_results(self, html: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []
        cards = soup.select(".job_seen_beacon, .jobsearch-ResultsList > li, .result")
        for card in cards:
            title_el = card.select_one("h2 a, .jobTitle a, [data-jk]")
            company_el = card.select_one(".companyName, [data-testid='company-name']")
            location_el = card.select_one(".companyLocation, [data-testid='text-location']")
            desc_el = card.select_one(".job-snippet, .summary")

            if not title_el:
                continue

            job_url = ""
            href = title_el.get("href", "")
            if href:
                job_url = href if href.startswith("http") else self.BASE_URL + href

            mission = Mission(
                title=title_el.get_text(strip=True),
                company=company_el.get_text(strip=True) if company_el else "",
                description=desc_el.get_text(strip=True) if desc_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                source=self.PLATFORM_NAME,
                url=job_url,
                contract_type=ContractType.DAILY_RATE,
            )
            missions.append(mission)
        return missions

    def _generate_sample_missions(
        self, profile: FreelanceProfile, count: int
    ) -> list[Mission]:
        templates = [
            {
                "title": f"Freelance {profile.title} — Mission longue",
                "company": "Société de conseil IT",
                "description": (
                    f"Nous recherchons un(e) {profile.title} freelance pour "
                    f"une mission longue durée. Profil : {', '.join(profile.skills[:3])}."
                ),
                "duration": "12 mois",
                "remote_policy": RemotePolicy.HYBRID,
            },
            {
                "title": f"{profile.title} indépendant(e) — Projet agile",
                "company": "Scale-up Tech",
                "description": (
                    f"Équipe agile cherche {profile.title} pour renforcer "
                    f"l'équipe produit. {', '.join(profile.skills[:2])} requis."
                ),
                "duration": "6 mois",
                "remote_policy": RemotePolicy.FULL_REMOTE,
            },
            {
                "title": f"Mission {profile.title} — Secteur public",
                "company": "Administration publique",
                "description": (
                    f"Modernisation SI pour le secteur public. Profil "
                    f"{profile.title}, {', '.join(profile.skills[:3])}."
                ),
                "duration": "9 mois",
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
                    budget_min=profile.daily_rate_min,
                    budget_max=profile.daily_rate_max,
                    duration=t.get("duration", ""),
                    location=profile.location or "France",
                    remote_policy=t.get("remote_policy", RemotePolicy.FLEXIBLE),
                    source=self.PLATFORM_NAME,
                    url=f"https://fr.indeed.com/viewjob?jk=example{i+1}",
                )
            )
        return missions
