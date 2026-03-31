"""Générateur de liens de recherche directs vers les plateformes freelance.

Ces plateformes n'ont pas d'API publique gratuite.
On génère des liens de recherche réels que l'utilisateur peut ouvrir directement.
"""

from __future__ import annotations

from urllib.parse import quote_plus

from freelance_hunter.models import (
    ContractType,
    FreelanceProfile,
    Mission,
    RemotePolicy,
)


def generate_search_links(profile: FreelanceProfile) -> list[Mission]:
    """Génère des liens de recherche directs vers les grandes plateformes."""
    missions = []

    # Construire les termes de recherche
    search_terms = _build_search_terms(profile)

    # ── Malt ──
    for term in search_terms[:2]:
        missions.append(Mission(
            title=f"Malt : {term}",
            company="malt.fr",
            description=f"Recherche « {term} » sur Malt — plateforme freelance #1 en France.",
            skills_required=profile.skills[:5],
            source="Malt",
            url=f"https://www.malt.fr/s?q={quote_plus(term)}",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FLEXIBLE,
        ))

    # ── Free-Work (ex Freelance.com) ──
    for term in search_terms[:2]:
        missions.append(Mission(
            title=f"Free-Work : {term}",
            company="free-work.com",
            description=f"Offres freelance « {term} » sur Free-Work (ex Freelance.com).",
            skills_required=profile.skills[:5],
            source="Free-Work",
            url=f"https://www.free-work.com/fr/tech-it/jobs?query={quote_plus(term)}&contracts=contractor",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FLEXIBLE,
        ))

    # ── LinkedIn Jobs ──
    for term in search_terms[:2]:
        params = f"keywords={quote_plus(term)}&location=France&f_JT=C%2CT&f_WT=2"
        missions.append(Mission(
            title=f"LinkedIn : {term}",
            company="linkedin.com",
            description=f"Offres LinkedIn pour « {term} » — filtré contrat/freelance, remote.",
            skills_required=profile.skills[:5],
            source="LinkedIn",
            url=f"https://www.linkedin.com/jobs/search?{params}",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FULL_REMOTE,
        ))

    # ── Indeed France ──
    for term in search_terms[:2]:
        params = f"q={quote_plus(term + ' freelance')}&l=France&jt=contract"
        missions.append(Mission(
            title=f"Indeed : {term}",
            company="indeed.fr",
            description=f"Recherche Indeed France pour « {term} freelance » — filtre contrat.",
            skills_required=profile.skills[:5],
            source="Indeed",
            url=f"https://fr.indeed.com/jobs?{params}",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FLEXIBLE,
        ))

    # ── Freelance-info.fr ──
    for term in search_terms[:2]:
        missions.append(Mission(
            title=f"Freelance-info : {term}",
            company="freelance-info.fr",
            description=f"Missions freelance « {term} » sur Freelance-info.fr.",
            skills_required=profile.skills[:5],
            source="Freelance-info",
            url=f"https://www.freelance-info.fr/missions-freelances?query={quote_plus(term)}",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FLEXIBLE,
        ))

    # ── Talent.com ──
    for term in search_terms[:1]:
        missions.append(Mission(
            title=f"Talent.com : {term}",
            company="talent.com",
            description=f"Offres « {term} » sur Talent.com — agrégateur d'offres freelance.",
            skills_required=profile.skills[:5],
            source="Talent.com",
            url=f"https://fr.talent.com/jobs?q={quote_plus(term + ' freelance')}&l=France",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FLEXIBLE,
        ))

    # ── Upwork ──
    for term in search_terms[:1]:
        missions.append(Mission(
            title=f"Upwork : {term}",
            company="upwork.com",
            description=f"Missions freelance « {term} » sur Upwork — plateforme internationale.",
            skills_required=profile.skills[:5],
            source="Upwork",
            url=f"https://www.upwork.com/nx/search/jobs/?q={quote_plus(term)}&sort=recency",
            contract_type=ContractType.DAILY_RATE,
            remote_policy=RemotePolicy.FULL_REMOTE,
        ))

    return missions


def _build_search_terms(profile: FreelanceProfile) -> list[str]:
    """Construit des termes de recherche pertinents."""
    terms = []
    if profile.title:
        terms.append(profile.title)
    # Combinaisons de skills pertinentes
    if len(profile.skills) >= 2:
        terms.append(f"{profile.skills[0]} {profile.skills[1]}")
    for skill in profile.skills[:3]:
        terms.append(skill)
    return terms
