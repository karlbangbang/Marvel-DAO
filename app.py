"""Application web FreelanceHunter — Flask."""

from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    session,
)

from freelance_hunter.generators.application import ApplicationGenerator
from freelance_hunter.generators.exporter import Exporter
from freelance_hunter.matcher import rank_missions
from freelance_hunter.models import (
    ContractType,
    ExperienceLevel,
    FreelanceProfile,
    Mission,
    RemotePolicy,
)
from freelance_hunter.scrapers import (
    FreelanceComScraper,
    FreelanceInfoScraper,
    IndeedFreelanceScraper,
    LinkedInScraper,
    MaltScraper,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "freelance-hunter-dev-key")

# Stockage en mémoire pour la session (simplifié)
_store: dict = {"profile": None, "missions": [], "packages": []}


# ── Routes pages ──────────────────────────────────────────────


@app.route("/")
def index():
    return render_template("index.html")


# ── API endpoints ─────────────────────────────────────────────


@app.route("/api/search", methods=["POST"])
def api_search():
    """Reçoit le profil, lance la recherche, retourne les missions classées."""
    data = request.json
    profile = _build_profile(data)
    _store["profile"] = profile

    scrapers = [
        MaltScraper(),
        FreelanceComScraper(),
        FreelanceInfoScraper(),
        IndeedFreelanceScraper(),
        LinkedInScraper(),
    ]

    all_missions = []
    platform_results = []

    for scraper in scrapers:
        try:
            missions = scraper.search(profile, max_results=6)
            all_missions.extend(missions)
            platform_results.append(
                {"platform": scraper.PLATFORM_NAME, "count": len(missions), "ok": True}
            )
        except Exception as e:
            platform_results.append(
                {"platform": scraper.PLATFORM_NAME, "count": 0, "ok": False, "error": str(e)}
            )

    ranked = rank_missions(profile, all_missions)
    _store["missions"] = ranked

    missions_data = []
    for i, m in enumerate(ranked):
        missions_data.append({
            "index": i,
            "title": m.title,
            "company": m.company,
            "description": m.description,
            "skills": m.skills_required,
            "budget_min": m.budget_min,
            "budget_max": m.budget_max,
            "duration": m.duration,
            "location": m.location,
            "remote": m.remote_policy.value,
            "source": m.source,
            "url": m.url,
            "score": m.match_score,
        })

    return jsonify({
        "platforms": platform_results,
        "missions": missions_data,
        "total": len(ranked),
    })


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Génère la candidature pour une mission donnée."""
    data = request.json
    mission_index = data.get("mission_index", 0)

    profile = _store.get("profile")
    missions = _store.get("missions", [])

    if not profile or mission_index >= len(missions):
        return jsonify({"error": "Profil ou mission introuvable"}), 400

    mission = missions[mission_index]
    generator = ApplicationGenerator()
    package = generator.generate(profile, mission)

    result = {
        "mission_title": mission.title,
        "company": mission.company,
        "score": mission.match_score,
        "documents": {
            "cover_letter": package.cover_letter,
            "proposal": package.proposal,
            "cv_summary": package.cv_summary,
            "email_subject": package.email_subject,
            "email_body": package.email_body,
            "follow_up_email": package.follow_up_email,
            "linkedin_message": package.linkedin_message,
            "elevator_pitch": package.elevator_pitch,
            "negotiation_tips": package.negotiation_tips,
            "interview_prep": package.interview_prep,
        },
    }

    return jsonify(result)


@app.route("/api/generate-all", methods=["POST"])
def api_generate_all():
    """Génère les candidatures pour les N meilleures missions et retourne un ZIP."""
    data = request.json
    count = min(data.get("count", 5), len(_store.get("missions", [])))

    profile = _store.get("profile")
    missions = _store.get("missions", [])

    if not profile or not missions:
        return jsonify({"error": "Lancez d'abord une recherche"}), 400

    generator = ApplicationGenerator()
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, mission in enumerate(missions[:count], 1):
            package = generator.generate(profile, mission)
            folder = f"{i:02d}_{_safe(mission.title)}"

            files = {
                "01_lettre_motivation.txt": package.cover_letter,
                "02_proposition_commerciale.txt": package.proposal,
                "03_resume_cv.txt": package.cv_summary,
                "04_email_candidature.txt": f"Objet : {package.email_subject}\n\n{package.email_body}",
                "05_email_relance.txt": package.follow_up_email,
                "06_message_linkedin.txt": package.linkedin_message,
                "07_elevator_pitch.txt": package.elevator_pitch,
                "08_conseils_negociation.txt": "\n".join(
                    f"{j}. {tip}" for j, tip in enumerate(package.negotiation_tips, 1)
                ),
                "09_preparation_entretien.txt": "\n".join(
                    f"{j}. {item}" for j, item in enumerate(package.interview_prep, 1)
                ),
                "10_fiche_mission.txt": _mission_card(mission, profile),
            }

            for filename, content in files.items():
                zf.writestr(f"{folder}/{filename}", content)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="candidatures_freelance.zip",
    )


# ── Helpers ───────────────────────────────────────────────────


def _build_profile(data: dict) -> FreelanceProfile:
    skills = [s.strip() for s in data.get("skills", "").split(",") if s.strip()]
    languages = [l.strip() for l in data.get("languages", "Français").split(",") if l.strip()]
    industries = [i.strip() for i in data.get("industries", "").split(",") if i.strip()]
    certifications = [c.strip() for c in data.get("certifications", "").split(",") if c.strip()]

    return FreelanceProfile(
        name=data.get("name", ""),
        title=data.get("title", ""),
        skills=skills,
        experience_years=int(data.get("experience_years", 0)),
        experience_level=ExperienceLevel(data.get("experience_level", "intermediate")),
        daily_rate_min=int(data.get("daily_rate_min", 0)),
        daily_rate_max=int(data.get("daily_rate_max", 0)),
        location=data.get("location", ""),
        remote_preference=RemotePolicy(data.get("remote_preference", "full_remote")),
        languages=languages,
        bio=data.get("bio", ""),
        portfolio_url=data.get("portfolio_url", ""),
        linkedin_url=data.get("linkedin_url", ""),
        certifications=certifications,
        industries=industries,
        availability=data.get("availability", "immédiate"),
    )


def _safe(name: str) -> str:
    return "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()[:60]


def _mission_card(m: Mission, p: FreelanceProfile) -> str:
    return (
        f"FICHE MISSION\n{'=' * 40}\n\n"
        f"Titre      : {m.title}\n"
        f"Entreprise : {m.company}\n"
        f"Source     : {m.source}\n"
        f"Budget     : {m.budget_min}-{m.budget_max} EUR/jour\n"
        f"Durée      : {m.duration}\n"
        f"Remote     : {m.remote_policy.value}\n"
        f"Score      : {m.match_score}%\n\n"
        f"Description :\n{m.description}\n\n"
        f"Compétences : {', '.join(m.skills_required)}\n"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
