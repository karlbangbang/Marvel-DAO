"""API RemoteOK — offres remote tech, gratuite, sans clé API."""

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


class RemoteOKScraper(BaseScraper):
    """RemoteOK.com — API gratuite, jobs remote tech, pas de clé requise."""

    PLATFORM_NAME = "RemoteOK"
    BASE_URL = "https://remoteok.com"
    API_URL = "https://remoteok.com/api"
    RATE_LIMIT_SECONDS = 3.0  # RemoteOK demande de limiter

    def search(self, profile: FreelanceProfile, max_results: int = 20) -> list[Mission]:
        # RemoteOK API: pas de param search, filtrage côté client
        self.session.headers.update({"Accept": "application/json"})
        response = self._get(self.API_URL)
        if not response:
            return []

        try:
            data = response.json()
            # Le premier élément est un objet meta/legal, on le skip
            jobs = data[1:] if isinstance(data, list) and len(data) > 1 else []
            all_missions = self._parse_api(jobs)
            filtered = self._filter_by_profile(all_missions, profile)
            return filtered[:max_results]
        except Exception as e:
            logger.warning(f"[{self.PLATFORM_NAME}] Parse error: {e}")
            return []

    def _build_search_url(self, profile: FreelanceProfile) -> str:
        return self.API_URL

    def _parse_results(self, html: str) -> list[Mission]:
        return []

    def _parse_api(self, jobs: list[dict]) -> list[Mission]:
        missions = []
        for job in jobs:
            title = job.get("position", "")
            if not title:
                continue

            tags = job.get("tags", []) or []
            description = job.get("description", "")
            if "<" in description:
                from bs4 import BeautifulSoup
                description = BeautifulSoup(description, "html.parser").get_text(separator=" ", strip=True)
            description = description[:500] if description else ""

            # Salary
            salary_min = 0
            salary_max = 0
            try:
                salary_min = int(job.get("salary_min", 0) or 0)
                salary_max = int(job.get("salary_max", 0) or 0)
            except (ValueError, TypeError):
                pass

            # URL
            url = job.get("url", "")
            if not url:
                slug = job.get("slug", "")
                if slug:
                    url = f"{self.BASE_URL}/remote-jobs/{slug}"
                job_id = job.get("id", "")
                if not url and job_id:
                    url = f"{self.BASE_URL}/remote-jobs/{job_id}"

            company_logo = job.get("company_logo", "")

            missions.append(Mission(
                title=title,
                company=job.get("company", ""),
                description=description,
                skills_required=tags[:10],
                contract_type=ContractType.DAILY_RATE,
                location=job.get("location", "Remote"),
                remote_policy=RemotePolicy.FULL_REMOTE,
                source=self.PLATFORM_NAME,
                url=url,
                posted_date=job.get("date", ""),
            ))

        return missions

    def _filter_by_profile(self, missions: list[Mission], profile: FreelanceProfile) -> list[Mission]:
        keywords = set()
        keywords.add(profile.title.lower())
        for skill in profile.skills:
            keywords.add(skill.lower())
        keywords.update(["analyst", "business", "data", "finance", "excel", "power bi", "reporting", "fp&a"])

        scored = []
        for m in missions:
            text = f"{m.title} {m.description} {' '.join(m.skills_required)}".lower()
            hits = sum(1 for kw in keywords if kw in text)
            if hits > 0:
                scored.append((hits, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]
