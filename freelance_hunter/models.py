"""Modèles de données pour les profils freelance et les missions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"


class ContractType(str, Enum):
    FIXED_PRICE = "forfait"
    DAILY_RATE = "tjm"
    HOURLY = "horaire"
    MONTHLY = "mensuel"


class RemotePolicy(str, Enum):
    FULL_REMOTE = "full_remote"
    HYBRID = "hybride"
    ON_SITE = "sur_site"
    FLEXIBLE = "flexible"


@dataclass
class FreelanceProfile:
    """Profil du freelance cherchant des missions."""

    name: str
    title: str  # ex: "Développeur Full Stack", "Designer UX/UI"
    skills: list[str] = field(default_factory=list)
    experience_years: int = 0
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    daily_rate_min: int = 0  # TJM minimum en euros
    daily_rate_max: int = 0  # TJM maximum en euros
    location: str = ""
    remote_preference: RemotePolicy = RemotePolicy.FULL_REMOTE
    languages: list[str] = field(default_factory=lambda: ["Français"])
    bio: str = ""
    portfolio_url: str = ""
    linkedin_url: str = ""
    certifications: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)  # secteurs préférés
    availability: str = "immédiate"

    def summary(self) -> str:
        skills_str = ", ".join(self.skills[:5])
        return (
            f"{self.name} — {self.title} | {self.experience_level.value} "
            f"({self.experience_years} ans) | Compétences: {skills_str} | "
            f"TJM: {self.daily_rate_min}-{self.daily_rate_max}€"
        )


@dataclass
class Mission:
    """Représente une mission/offre freelance trouvée."""

    title: str
    company: str = ""
    description: str = ""
    skills_required: list[str] = field(default_factory=list)
    contract_type: ContractType = ContractType.DAILY_RATE
    budget_min: int = 0
    budget_max: int = 0
    duration: str = ""  # ex: "3 mois", "6 mois renouvelable"
    location: str = ""
    remote_policy: RemotePolicy = RemotePolicy.FLEXIBLE
    experience_required: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    url: str = ""
    source: str = ""  # plateforme d'origine
    posted_date: str = ""
    start_date: str = ""
    contact_email: str = ""
    contact_name: str = ""
    industry: str = ""
    match_score: float = 0.0  # score de matching 0-100

    def summary(self) -> str:
        budget = ""
        if self.budget_min and self.budget_max:
            budget = f"{self.budget_min}-{self.budget_max}€/j"
        elif self.budget_max:
            budget = f"≤{self.budget_max}€/j"
        skills = ", ".join(self.skills_required[:5])
        return (
            f"[{self.source}] {self.title} @ {self.company} | "
            f"{budget} | {self.remote_policy.value} | {skills}"
        )


@dataclass
class ApplicationPackage:
    """Package complet de candidature généré pour une mission."""

    mission: Mission
    profile: FreelanceProfile
    cover_letter: str = ""
    proposal: str = ""
    cv_summary: str = ""
    email_subject: str = ""
    email_body: str = ""
    follow_up_email: str = ""
    linkedin_message: str = ""
    elevator_pitch: str = ""
    negotiation_tips: list[str] = field(default_factory=list)
    interview_prep: list[str] = field(default_factory=list)
