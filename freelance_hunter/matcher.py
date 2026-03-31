"""Moteur de matching entre profil freelance et missions disponibles."""

from __future__ import annotations

from freelance_hunter.models import FreelanceProfile, Mission, RemotePolicy


def compute_match_score(profile: FreelanceProfile, mission: Mission) -> float:
    """Calcule un score de matching (0-100) entre un profil et une mission."""
    score = 0.0
    weights = {
        "skills": 40.0,
        "budget": 20.0,
        "remote": 15.0,
        "experience": 15.0,
        "location": 10.0,
    }

    # --- Skills match (40 points max) ---
    if profile.skills and mission.skills_required:
        profile_skills = {s.lower().strip() for s in profile.skills}
        mission_skills = {s.lower().strip() for s in mission.skills_required}
        if mission_skills:
            matched = profile_skills & mission_skills
            skill_ratio = len(matched) / len(mission_skills)
            score += weights["skills"] * skill_ratio
    else:
        # Pas d'info skills sur la mission => score neutre
        score += weights["skills"] * 0.5

    # --- Budget match (20 points max) ---
    if mission.budget_max > 0 and profile.daily_rate_min > 0:
        if profile.daily_rate_min <= mission.budget_max:
            if profile.daily_rate_max <= mission.budget_max:
                score += weights["budget"]
            else:
                overlap = mission.budget_max - profile.daily_rate_min
                range_size = profile.daily_rate_max - profile.daily_rate_min
                if range_size > 0:
                    score += weights["budget"] * min(overlap / range_size, 1.0)
        # Si TJM min > budget max => 0 points budget
    else:
        score += weights["budget"] * 0.5

    # --- Remote policy match (15 points max) ---
    remote_compat = _remote_compatibility(profile.remote_preference, mission.remote_policy)
    score += weights["remote"] * remote_compat

    # --- Experience level match (15 points max) ---
    exp_order = {"junior": 0, "intermediate": 1, "senior": 2, "expert": 3}
    profile_exp = exp_order.get(profile.experience_level.value, 1)
    mission_exp = exp_order.get(mission.experience_required.value, 1)
    if profile_exp >= mission_exp:
        score += weights["experience"]
    elif profile_exp == mission_exp - 1:
        score += weights["experience"] * 0.6
    else:
        score += weights["experience"] * 0.2

    # --- Location match (10 points max) ---
    if not mission.location or not profile.location:
        score += weights["location"] * 0.7
    elif profile.location.lower() in mission.location.lower():
        score += weights["location"]
    elif any(
        word in mission.location.lower()
        for word in ["remote", "télétravail", "france"]
    ):
        score += weights["location"] * 0.8
    else:
        score += weights["location"] * 0.3

    return round(min(score, 100.0), 1)


def _remote_compatibility(pref: RemotePolicy, offer: RemotePolicy) -> float:
    """Retourne un score de compatibilité remote (0.0 à 1.0)."""
    if pref == offer:
        return 1.0
    if offer == RemotePolicy.FLEXIBLE:
        return 0.9
    compat = {
        (RemotePolicy.FULL_REMOTE, RemotePolicy.HYBRID): 0.5,
        (RemotePolicy.FULL_REMOTE, RemotePolicy.ON_SITE): 0.0,
        (RemotePolicy.HYBRID, RemotePolicy.FULL_REMOTE): 0.8,
        (RemotePolicy.HYBRID, RemotePolicy.ON_SITE): 0.4,
        (RemotePolicy.ON_SITE, RemotePolicy.FULL_REMOTE): 0.3,
        (RemotePolicy.ON_SITE, RemotePolicy.HYBRID): 0.7,
    }
    return compat.get((pref, offer), 0.5)


def rank_missions(
    profile: FreelanceProfile, missions: list[Mission], min_score: float = 0.0
) -> list[Mission]:
    """Classe les missions par score de matching décroissant."""
    for mission in missions:
        mission.match_score = compute_match_score(profile, mission)

    ranked = sorted(missions, key=lambda m: m.match_score, reverse=True)
    if min_score > 0:
        ranked = [m for m in ranked if m.match_score >= min_score]
    return ranked
