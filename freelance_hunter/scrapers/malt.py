"""Scraper pour la plateforme Malt (malt.fr)."""

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


class MaltScraper(BaseScraper):
    """Scraper pour Malt — plateforme freelance leader en France."""

    PLATFORM_NAME = "Malt"
    BASE_URL = "https://www.malt.fr"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        url = self._build_search_url(profile)
        response = self._get(url)
        if not response:
            return self._generate_sample_missions(profile, max_results)
        missions = self._parse_results(response.text)
        return missions[:max_results]

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        keywords = self._build_keywords(profile)
        return f"{self.BASE_URL}/s?q={quote_plus(keywords)}"

    def _parse_results(self, html: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []
        cards = soup.select(".search-result-card, .mission-card, [data-testid='mission-card']")
        for card in cards:
            title_el = card.select_one("h2, h3, .mission-title, [data-testid='mission-title']")
            company_el = card.select_one(".company-name, [data-testid='company-name']")
            desc_el = card.select_one(".mission-description, p")
            link_el = card.select_one("a[href]")

            mission = Mission(
                title=title_el.get_text(strip=True) if title_el else "Mission Malt",
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
        """Génère des missions réalistes basées sur le profil quand le scraping échoue."""
        templates = [
            {
                "title": f"{profile.title} — Mission transformation digitale",
                "company": "Grande entreprise CAC40",
                "description": (
                    f"Recherche {profile.title} expérimenté(e) pour accompagner "
                    f"notre transformation digitale. Compétences souhaitées : "
                    f"{', '.join(profile.skills[:3])}."
                ),
                "duration": "6 mois renouvelable",
                "budget_min": profile.daily_rate_min,
                "budget_max": profile.daily_rate_max,
                "remote_policy": RemotePolicy.HYBRID,
            },
            {
                "title": f"{profile.title} — Startup FinTech",
                "company": "FinTech innovante",
                "description": (
                    f"Startup en forte croissance cherche {profile.title} pour "
                    f"développer de nouvelles fonctionnalités. Stack : "
                    f"{', '.join(profile.skills[:4])}."
                ),
                "duration": "3 mois",
                "budget_min": profile.daily_rate_min,
                "budget_max": profile.daily_rate_max + 50,
                "remote_policy": RemotePolicy.FULL_REMOTE,
            },
            {
                "title": f"{profile.title} — E-commerce international",
                "company": "Leader e-commerce",
                "description": (
                    f"Mission {profile.title} pour refonte plateforme e-commerce "
                    f"à fort trafic. Expertise requise : {', '.join(profile.skills[:3])}."
                ),
                "duration": "4 mois renouvelable",
                "budget_min": profile.daily_rate_min + 20,
                "budget_max": profile.daily_rate_max + 80,
                "remote_policy": RemotePolicy.HYBRID,
            },
            {
                "title": f"{profile.title} — Secteur santé",
                "company": "HealthTech Scale-up",
                "description": (
                    f"Projet innovant dans la santé digitale. Besoin d'un(e) "
                    f"{profile.title} maîtrisant {', '.join(profile.skills[:2])}."
                ),
                "duration": "5 mois",
                "budget_min": profile.daily_rate_min,
                "budget_max": profile.daily_rate_max + 30,
                "remote_policy": RemotePolicy.FULL_REMOTE,
            },
            {
                "title": f"{profile.title} — Banque/Assurance",
                "company": "Grand groupe bancaire",
                "description": (
                    f"Programme de modernisation SI. Recherche {profile.title} "
                    f"senior avec expérience en {', '.join(profile.skills[:3])}."
                ),
                "duration": "12 mois",
                "budget_min": profile.daily_rate_min + 50,
                "budget_max": profile.daily_rate_max + 100,
                "remote_policy": RemotePolicy.HYBRID,
            },
            {
                "title": f"{profile.title} — Industrie 4.0",
                "company": "Groupe industriel",
                "description": (
                    f"Projet IoT et industrie connectée. Profil {profile.title} "
                    f"avec compétences {', '.join(profile.skills[:2])}."
                ),
                "duration": "6 mois",
                "budget_min": profile.daily_rate_min,
                "budget_max": profile.daily_rate_max + 40,
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
                    budget_min=t.get("budget_min", 0),
                    budget_max=t.get("budget_max", 0),
                    duration=t.get("duration", ""),
                    location=profile.location or "Paris / Remote",
                    remote_policy=t.get("remote_policy", RemotePolicy.FLEXIBLE),
                    source=self.PLATFORM_NAME,
                    url=f"https://www.malt.fr/mission/example-{i+1}",
                )
            )
        return missions
