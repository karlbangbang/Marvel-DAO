"""Scraper pour Malt (malt.fr) — vraies offres avec liens."""

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
    PLATFORM_NAME = "Malt"
    BASE_URL = "https://www.malt.fr"

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        keywords = self._build_keywords(profile)
        url = f"{self.BASE_URL}/s?q={quote_plus(keywords)}"
        search_url = url

        response = self._get(url)
        if response:
            missions = self._parse_results(response.text, search_url)
            if missions:
                return missions[:max_results]

        # Essai avec des termes plus simples
        for term in self._get_search_terms(profile):
            url = f"{self.BASE_URL}/s?q={quote_plus(term)}"
            response = self._get(url)
            if response:
                missions = self._parse_results(response.text, url)
                if missions:
                    return missions[:max_results]

        # Fallback : retourne des liens de recherche réels cliquables
        return self._build_real_search_links(profile, max_results)

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        return f"{self.BASE_URL}/s?q={quote_plus(self._build_keywords(profile))}"

    def _get_search_terms(self, profile: FreelanceProfile) -> list[str]:
        """Génère plusieurs variantes de recherche."""
        terms = []
        if profile.title:
            terms.append(profile.title)
        for skill in profile.skills[:4]:
            terms.append(f"{skill} freelance")
        terms.append(f"{profile.title} {profile.skills[0]}" if profile.skills else profile.title)
        return terms

    def _parse_results(self, html: str, search_url: str) -> list[Mission]:
        soup = BeautifulSoup(html, "html.parser")
        missions = []

        # Malt utilise différents sélecteurs selon les pages
        selectors = [
            "div[class*='mission']",
            "div[class*='search-result']",
            "div[class*='card']",
            "article",
            "li[class*='result']",
        ]

        cards = []
        for sel in selectors:
            cards = soup.select(sel)
            if cards:
                break

        for card in cards:
            link = card.select_one("a[href]")
            title_el = card.select_one("h2, h3, h4, [class*='title']")

            if not link and not title_el:
                continue

            href = ""
            if link:
                href = link.get("href", "")
                if href and not href.startswith("http"):
                    href = self.BASE_URL + href

            title = ""
            if title_el:
                title = title_el.get_text(strip=True)
            elif link:
                title = link.get_text(strip=True)

            if not title or len(title) < 5:
                continue

            desc_el = card.select_one("p, [class*='desc'], [class*='snippet']")
            company_el = card.select_one("[class*='company'], [class*='author'], [class*='name']")

            missions.append(Mission(
                title=title,
                company=company_el.get_text(strip=True) if company_el else "",
                description=desc_el.get_text(strip=True) if desc_el else "",
                source=self.PLATFORM_NAME,
                url=href or search_url,
                contract_type=ContractType.DAILY_RATE,
            ))

        return missions

    def _build_real_search_links(self, profile: FreelanceProfile, count: int) -> list[Mission]:
        """Construit des missions avec de vrais liens de recherche Malt."""
        search_queries = [
            profile.title,
            f"{profile.skills[0]} freelance" if profile.skills else profile.title,
            f"{profile.skills[1]} {profile.skills[2]}" if len(profile.skills) >= 3 else profile.title,
            "Business Analyst",
            "Power BI freelance",
            "FP&A analyst",
            "Automatisation Excel VBA",
            "Data Analyst Power Query",
        ]

        missions = []
        seen = set()
        for query in search_queries:
            if len(missions) >= count:
                break
            if query.lower() in seen:
                continue
            seen.add(query.lower())

            real_url = f"{self.BASE_URL}/s?q={quote_plus(query)}"
            missions.append(Mission(
                title=f"Recherche Malt : {query}",
                company="Voir les offres sur Malt",
                description=f"Cliquez pour voir les missions freelance correspondant à « {query} » sur Malt.fr. Résultats en temps réel.",
                skills_required=profile.skills[:5],
                source=self.PLATFORM_NAME,
                url=real_url,
                contract_type=ContractType.DAILY_RATE,
                remote_policy=RemotePolicy.FLEXIBLE,
            ))

        return missions
