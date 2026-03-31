"""Scrapers pour les plateformes freelance."""

from .base import BaseScraper
from .malt import MaltScraper
from .freelance_com import FreelanceComScraper
from .indeed import IndeedFreelanceScraper
from .linkedin import LinkedInScraper

__all__ = [
    "BaseScraper",
    "MaltScraper",
    "FreelanceComScraper",
    "IndeedFreelanceScraper",
    "LinkedInScraper",
]
