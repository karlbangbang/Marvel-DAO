"""Scrapers et APIs pour les plateformes freelance."""

from .base import BaseScraper
from .remotive import RemotiveScraper
from .arbeitnow import ArbeitnowScraper
from .remoteok import RemoteOKScraper
from .search_links import generate_search_links

__all__ = [
    "BaseScraper",
    "RemotiveScraper",
    "ArbeitnowScraper",
    "RemoteOKScraper",
    "generate_search_links",
]
