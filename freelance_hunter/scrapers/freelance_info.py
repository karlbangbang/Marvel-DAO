"""Scraper pour Freelance-info.fr — référence des missions IT en France."""

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


class FreelanceInfoScraper(BaseScraper):
    PLATFORM_NAME = "Freelance-info"
    BASE_URL = "https://www.freelance-info.fr"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        for term in self._get_search_terms(profile):
            url = f"{self.BASE_URL}/missions-freelances?query={quote_plus(term)}"
            response = self._get(url)
            if response:
                missions = self._parse_results(response.text)
                if missions:
                    return missions[:max_results]

        return self._build_real_search_links(profile, max_results)

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        return f"{self.BASE_URL}/missions-freelances?query={quote_plus(self._build_keywords(profile))}"

    def _get_search_terms(self, profile: FreelanceProfile) -> list[str]:
        terms = [self._build_keywords(profile), profile.title]
        for skill in profile.skills[:3]:
            terms.append(skill)
        return terms

    def _parse_results(self, html: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []

        cards = soup.select("div.mission-list__item, div[class*='mission'], article, .search-result, tr[class*='mission']")
        for card in cards:
            link = card.select_one("a[href*='mission']")
            title_el = card.select_one("h2, h3, .mission-title, a[class*='title']")
            if not title_el and link:
                title_el = link

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            href = ""
            if link:
                href = link.get("href", "")
                if href and not href.startswith("http"):
                    href = self.BASE_URL + href

            desc_el = card.select_one("p, .mission-description, [class*='desc']")
            location_el = card.select_one("[class*='location'], [class*='lieu']")
            rate_el = card.select_one("[class*='rate'], [class*='tjm'], [class*='price']")

            missions.append(Mission(
                title=title,
                description=desc_el.get_text(strip=True) if desc_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                source=self.PLATFORM_NAME,
                url=href,
                contract_type=ContractType.DAILY_RATE,
            ))

        return missions

    def _build_real_search_links(self, profile: FreelanceProfile, count: int) -> list[Mission]:
        queries = [
            profile.title,
            "Business Analyst",
            "Power BI",
            "FP&A",
            "Excel VBA",
            "Data Analyst",
            "Alteryx",
            "SAP Finance",
        ]
        missions = []
        seen = set()
        for q in queries:
            if len(missions) >= count:
                break
            if q.lower() in seen:
                continue
            seen.add(q.lower())
            real_url = f"{self.BASE_URL}/missions-freelances?query={quote_plus(q)}"
            missions.append(Mission(
                title=f"Missions freelance : {q}",
                company="Voir sur Freelance-info.fr",
                description=f"Offres de missions freelance « {q} » sur Freelance-info.fr — la référence des missions IT en France.",
                skills_required=profile.skills[:5],
                source=self.PLATFORM_NAME,
                url=real_url,
                contract_type=ContractType.DAILY_RATE,
                remote_policy=RemotePolicy.FLEXIBLE,
            ))
        return missions
