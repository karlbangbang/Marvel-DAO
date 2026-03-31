"""Export des candidatures en fichiers texte organisés."""

from __future__ import annotations

import os
from pathlib import Path

from freelance_hunter.models import ApplicationPackage


class Exporter:
    """Exporte les packages de candidature en fichiers organisés."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)

    def export(self, package: ApplicationPackage) -> Path:
        """Exporte un package complet dans un dossier dédié."""
        safe_title = self._safe_filename(package.mission.title)
        mission_dir = self.output_dir / safe_title
        mission_dir.mkdir(parents=True, exist_ok=True)

        files = {
            "01_lettre_motivation.txt": package.cover_letter,
            "02_proposition_commerciale.txt": package.proposal,
            "03_resume_cv.txt": package.cv_summary,
            "04_email_candidature.txt": (
                f"Objet : {package.email_subject}\n\n{package.email_body}"
            ),
            "05_email_relance.txt": package.follow_up_email,
            "06_message_linkedin.txt": package.linkedin_message,
            "07_elevator_pitch.txt": package.elevator_pitch,
            "08_conseils_negociation.txt": self._format_list(
                "CONSEILS DE NÉGOCIATION", package.negotiation_tips
            ),
            "09_preparation_entretien.txt": self._format_list(
                "PRÉPARATION ENTRETIEN", package.interview_prep
            ),
            "10_fiche_mission.txt": self._format_mission_card(package),
        }

        for filename, content in files.items():
            filepath = mission_dir / filename
            filepath.write_text(content, encoding="utf-8")

        return mission_dir

    def _safe_filename(self, name: str) -> str:
        """Crée un nom de fichier safe à partir d'un titre."""
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)
        return safe.strip()[:80]

    def _format_list(self, title: str, items: list[str]) -> str:
        header = f"{'═' * 50}\n  {title}\n{'═' * 50}\n\n"
        body = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(items))
        return header + body + "\n"

    def _format_mission_card(self, pkg: ApplicationPackage) -> str:
        m = pkg.mission
        p = pkg.profile
        return f"""\
{'═' * 50}
  FICHE MISSION
{'═' * 50}

Titre      : {m.title}
Entreprise : {m.company}
Source     : {m.source}
URL        : {m.url}

Budget     : {m.budget_min}-{m.budget_max}€/jour
Durée      : {m.duration}
Lieu       : {m.location}
Remote     : {m.remote_policy.value}
Expérience : {m.experience_required.value}

Compétences requises : {', '.join(m.skills_required)}
Score matching       : {m.match_score}%

──────────────────────────────────────────────
Description :
{m.description}

──────────────────────────────────────────────
Candidat : {p.name} — {p.title}
TJM      : {p.daily_rate_min}-{p.daily_rate_max}€
"""
