"""Scraper pour LinkedIn Jobs — vraies offres freelance avec liens."""

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
    PLATFORM_NAME = "LinkedIn"
    BASE_URL = "https://www.linkedin.com"
    RATE_LIMIT_SECONDS = 3.0

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        for term in self._get_search_terms(profile):
            # LinkedIn public job search (pas besoin de login)
            url = (
                f"{self.BASE_URL}/jobs/search?"
                f"keywords={quote_plus(term)}"
                f"&location={quote_plus(profile.location or 'France')}"
                f"&f_JT=C,T"  # Contract + Temporary
                f"&f_WT=2"    # Remote
            )
            response = self._get(url)
            if response:
                missions = self._parse_results(response.text, url)
                if missions:
                    return missions[:max_results]

        return self._build_real_search_links(profile, max_results)

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        keywords = self._build_keywords(profile)
        return f"{self.BASE_URL}/jobs/search?keywords={quote_plus(keywords)}&f_JT=C"

    def _get_search_terms(self, profile: FreelanceProfile) -> list[str]:
        terms = [profile.title]
        for skill in profile.skills[:3]:
            terms.append(f"{skill} freelance")
        return terms

    def _parse_results(self, html: str, search_url: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []

        cards = soup.select(".base-card, .job-search-card, .jobs-search-results__list-item, [class*='job-card']")
        for card in cards:
            title_el = card.select_one("h3, .base-search-card__title, [class*='title']")
            company_el = card.select_one("h4, .base-search-card__subtitle, [class*='company']")
            location_el = card.select_one(".job-search-card__location, [class*='location']")
            link = card.select_one("a[href*='jobs']")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            href = ""
            if link:
                href = link.get("href", "")

            missions.append(Mission(
                title=title,
                company=company_el.get_text(strip=True) if company_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                source=self.PLATFORM_NAME,
                url=href or search_url,
                contract_type=ContractType.DAILY_RATE,
            ))

        return missions

    def _build_real_search_links(self, profile: FreelanceProfile, count: int) -> list[Mission]:
        queries = [
            ("Business Analyst freelance", "2"),    # f_WT=2 = remote
            ("FP&A Analyst", "2"),
            ("Power BI freelance", "2"),
            ("Data Analyst freelance", "2"),
            ("Excel VBA automatisation", ""),
            ("SAP Finance Analyst", "2"),
        ]
        missions = []
        for query, remote in queries[:count]:
            params = f"keywords={quote_plus(query)}&location=France&f_JT=C%2CT"
            if remote:
                params += f"&f_WT={remote}"
            real_url = f"{self.BASE_URL}/jobs/search?{params}"
            missions.append(Mission(
                title=f"LinkedIn : {query}",
                company="Voir les offres sur LinkedIn",
                description=f"Offres LinkedIn pour « {query} » — filtre contrat/freelance{', remote' if remote else ''}.",
                skills_required=profile.skills[:5],
                source=self.PLATFORM_NAME,
                url=real_url,
                contract_type=ContractType.DAILY_RATE,
                remote_policy=RemotePolicy.FULL_REMOTE if remote else RemotePolicy.FLEXIBLE,
            ))
        return missions
