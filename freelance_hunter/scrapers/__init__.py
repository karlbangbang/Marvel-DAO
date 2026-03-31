"""Scrapers pour les plateformes freelance."""

from .base import BaseScraper
from .malt import MaltScraper
from .freelance_com import FreelanceComScraper
from .freelance_info import FreelanceInfoScraper
from .indeed import IndeedFreelanceScraper
from .linkedin import LinkedInScraper

__all__ = [
    "BaseScraper",
    "MaltScraper",
    "FreelanceComScraper",
    "FreelanceInfoScraper",
    "IndeedFreelanceScraper",
    "LinkedInScraper",
]
