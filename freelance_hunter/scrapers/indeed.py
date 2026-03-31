"""Scraper pour Indeed France — vraies offres freelance avec liens."""

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
    PLATFORM_NAME = "Indeed"
    BASE_URL = "https://fr.indeed.com"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        for term in self._get_search_terms(profile):
            location = profile.location or "France"
            url = (
                f"{self.BASE_URL}/jobs?"
                f"q={quote_plus(term)}&l={quote_plus(location)}"
                f"&jt=contract&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
            )
            response = self._get(url)
            if response:
                missions = self._parse_results(response.text, url)
                if missions:
                    return missions[:max_results]

        return self._build_real_search_links(profile, max_results)

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        keywords = self._build_keywords(profile) + " freelance"
        location = profile.location or "France"
        return f"{self.BASE_URL}/jobs?q={quote_plus(keywords)}&l={quote_plus(location)}&jt=contract"

    def _get_search_terms(self, profile: FreelanceProfile) -> list[str]:
        terms = [
            f"{profile.title} freelance",
            profile.title,
        ]
        for skill in profile.skills[:3]:
            terms.append(f"{skill} freelance")
        return terms

    def _parse_results(self, html: str, search_url: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []

        cards = soup.select(".job_seen_beacon, .jobsearch-ResultsList > li, .result, .job-card, [data-jk]")
        for card in cards:
            title_el = card.select_one("h2 a, .jobTitle a, [data-jk] a, h2 span")
            company_el = card.select_one(".companyName, [data-testid='company-name'], .company")
            location_el = card.select_one(".companyLocation, [data-testid='text-location']")
            desc_el = card.select_one(".job-snippet, .summary, [class*='snippet']")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            href = ""
            link = title_el if title_el.name == "a" else title_el.find_parent("a")
            if link:
                href = link.get("href", "")
            if not href:
                jk = card.get("data-jk", "")
                if jk:
                    href = f"{self.BASE_URL}/viewjob?jk={jk}"
            if href and not href.startswith("http"):
                href = self.BASE_URL + href

            missions.append(Mission(
                title=title,
                company=company_el.get_text(strip=True) if company_el else "",
                description=desc_el.get_text(strip=True) if desc_el else "",
                location=location_el.get_text(strip=True) if location_el else "",
                source=self.PLATFORM_NAME,
                url=href or search_url,
                contract_type=ContractType.DAILY_RATE,
            ))

        return missions

    def _build_real_search_links(self, profile: FreelanceProfile, count: int) -> list[Mission]:
        queries = [
            (f"{profile.title} freelance", "remote"),
            ("Business Analyst freelance", "remote"),
            ("FP&A analyst freelance", ""),
            ("Power BI freelance", "remote"),
            ("Excel VBA automatisation freelance", ""),
            ("Data Analyst freelance", "remote"),
        ]
        missions = []
        for query, remote_flag in queries[:count]:
            params = f"q={quote_plus(query)}&l=France&jt=contract"
            if remote_flag:
                params += "&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
            real_url = f"{self.BASE_URL}/jobs?{params}"
            missions.append(Mission(
                title=f"Indeed : {query}",
                company="Voir les offres sur Indeed",
                description=f"Recherche Indeed France pour « {query} » — filtre contrat/freelance{', remote' if remote_flag else ''}.",
                skills_required=profile.skills[:5],
                source=self.PLATFORM_NAME,
                url=real_url,
                contract_type=ContractType.DAILY_RATE,
                remote_policy=RemotePolicy.FULL_REMOTE if remote_flag else RemotePolicy.FLEXIBLE,
            ))
        return missions
