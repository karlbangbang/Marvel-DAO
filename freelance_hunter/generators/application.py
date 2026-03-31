"""Générateur de candidatures complètes pour missions freelance."""

from __future__ import annotations

from jinja2 import Template

from freelance_hunter.models import ApplicationPackage, FreelanceProfile, Mission


class ApplicationGenerator:
    """Génère tout le matériel nécessaire pour candidater à une mission."""

    def generate(self, profile: FreelanceProfile, mission: Mission) -> ApplicationPackage:
        """Génère un package complet de candidature."""
        package = ApplicationPackage(mission=mission, profile=profile)
        package.cover_letter = self._generate_cover_letter(profile, mission)
        package.proposal = self._generate_proposal(profile, mission)
        package.cv_summary = self._generate_cv_summary(profile, mission)
        package.email_subject = self._generate_email_subject(profile, mission)
        package.email_body = self._generate_email_body(profile, mission)
        package.follow_up_email = self._generate_follow_up(profile, mission)
        package.linkedin_message = self._generate_linkedin_message(profile, mission)
        package.elevator_pitch = self._generate_elevator_pitch(profile, mission)
        package.negotiation_tips = self._generate_negotiation_tips(profile, mission)
        package.interview_prep = self._generate_interview_prep(profile, mission)
        return package

    def _generate_cover_letter(self, p: FreelanceProfile, m: Mission) -> str:
        template = Template("""\
Objet : Candidature — {{ mission_title }}

Madame, Monsieur,

Actuellement {{ title }} {{ level }} avec {{ years }} ans d'expérience, \
je me permets de vous proposer ma candidature pour la mission \
« {{ mission_title }} »{% if company %} chez {{ company }}{% endif %}.

Mon expertise en {{ skills_top }} me permet de répondre précisément \
aux besoins exprimés dans votre offre. \
{% if industries %}Ayant travaillé dans les secteurs {{ industries }}, \
je comprends les enjeux spécifiques de votre domaine.{% endif %}

{% if bio %}{{ bio }}{% endif %}

Points forts de ma candidature :
{% for skill in matching_skills %}\
• Maîtrise avancée de {{ skill }}
{% endfor %}\
• Disponibilité : {{ availability }}
• Mode de travail : {{ remote_pref }}
{% if certifications %}\
• Certifications : {{ certifications }}
{% endif %}

Je suis disponible pour un échange à votre convenance afin de \
discuter de cette mission plus en détail.

Cordialement,
{{ name }}
{% if portfolio %}Portfolio : {{ portfolio }}{% endif %}\
{% if linkedin %}LinkedIn : {{ linkedin }}{% endif %}\
""")
        matching = _find_matching_skills(p, m)
        return template.render(
            name=p.name,
            title=p.title,
            level=p.experience_level.value,
            years=p.experience_years,
            mission_title=m.title,
            company=m.company,
            skills_top=", ".join(p.skills[:4]),
            matching_skills=matching[:5],
            industries=", ".join(p.industries[:3]) if p.industries else "",
            bio=p.bio,
            availability=p.availability,
            remote_pref=p.remote_preference.value.replace("_", " "),
            certifications=", ".join(p.certifications) if p.certifications else "",
            portfolio=p.portfolio_url,
            linkedin=p.linkedin_url,
        )

    def _generate_proposal(self, p: FreelanceProfile, m: Mission) -> str:
        template = Template("""\
═══════════════════════════════════════════════
     PROPOSITION COMMERCIALE — {{ mission_title }}
═══════════════════════════════════════════════

1. COMPRÉHENSION DU BESOIN
──────────────────────────
{{ description }}

2. PROFIL PROPOSÉ
──────────────────
• {{ name }} — {{ title }}
• Expérience : {{ years }} ans ({{ level }})
• Compétences clés : {{ skills }}
{% if certifications %}\
• Certifications : {{ certifications }}
{% endif %}

3. APPROCHE PROPOSÉE
─────────────────────
Fort(e) de mon expérience, je propose :
• Phase 1 — Cadrage & analyse (semaine 1-2) : Audit de l'existant, \
définition du périmètre et planification
• Phase 2 — Réalisation (semaines 3+) : Développement itératif avec \
livrables réguliers et revues d'avancement
• Phase 3 — Livraison & transfert : Documentation, formation équipe, \
transition vers la maintenance

4. CONDITIONS COMMERCIALES
───────────────────────────
• TJM proposé : {{ rate_min }}€ - {{ rate_max }}€ / jour
{% if duration %}\
• Durée estimée : {{ duration }}
{% endif %}\
• Mode de travail : {{ remote }}
• Disponibilité : {{ availability }}

5. RÉFÉRENCES
──────────────
Missions similaires réalisées dans des contextes comparables. \
Références disponibles sur demande.

{{ name }}
""")
        return template.render(
            name=p.name,
            title=p.title,
            years=p.experience_years,
            level=p.experience_level.value,
            skills=", ".join(p.skills[:6]),
            certifications=", ".join(p.certifications) if p.certifications else "",
            mission_title=m.title,
            description=m.description or "Mission décrite dans l'offre originale.",
            rate_min=p.daily_rate_min,
            rate_max=p.daily_rate_max,
            duration=m.duration,
            remote=m.remote_policy.value.replace("_", " "),
            availability=p.availability,
        )

    def _generate_cv_summary(self, p: FreelanceProfile, m: Mission) -> str:
        template = Template("""\
┌─────────────────────────────────────────┐
│         RÉSUMÉ PROFESSIONNEL            │
└─────────────────────────────────────────┘

{{ name }}
{{ title }} — {{ level }} ({{ years }} ans d'expérience)

─── COMPÉTENCES CLÉS ─────────────────────
{% for skill in skills %}\
  ▸ {{ skill }}
{% endfor %}

─── PROFIL ────────────────────────────────
{{ bio_or_default }}

─── FORMATION & CERTIFICATIONS ────────────
{% if certifications %}\
{% for cert in certifications %}\
  ✓ {{ cert }}
{% endfor %}\
{% else %}\
  Formation et certifications disponibles sur demande.
{% endif %}

─── SECTEURS D'EXPERTISE ──────────────────
{% if industries %}\
{% for ind in industries %}\
  • {{ ind }}
{% endfor %}\
{% else %}\
  Multi-sectoriel
{% endif %}

─── LANGUES ───────────────────────────────
{% for lang in languages %}\
  • {{ lang }}
{% endfor %}

─── CONTACT ───────────────────────────────
{% if portfolio %}Portfolio : {{ portfolio }}{% endif %}
{% if linkedin %}LinkedIn : {{ linkedin }}{% endif %}
Disponibilité : {{ availability }}
""")
        return template.render(
            name=p.name,
            title=p.title,
            level=p.experience_level.value,
            years=p.experience_years,
            skills=p.skills[:10],
            bio_or_default=p.bio or f"{p.title} passionné(e) avec {p.experience_years} ans d'expérience.",
            certifications=p.certifications,
            industries=p.industries,
            languages=p.languages,
            portfolio=p.portfolio_url,
            linkedin=p.linkedin_url,
            availability=p.availability,
        )

    def _generate_email_subject(self, p: FreelanceProfile, m: Mission) -> str:
        return f"Candidature {p.title} — {m.title}"

    def _generate_email_body(self, p: FreelanceProfile, m: Mission) -> str:
        matching = _find_matching_skills(p, m)
        skills_mention = ", ".join(matching[:3]) if matching else ", ".join(p.skills[:3])
        return f"""\
Bonjour{' ' + m.contact_name if m.contact_name else ''},

Je me permets de vous contacter suite à votre offre « {m.title} ».

{p.title} {p.experience_level.value} avec {p.experience_years} ans d'expérience, \
je maîtrise notamment {skills_mention}, \
compétences directement pertinentes pour cette mission.

Disponible {p.availability.lower()}, je serais ravi(e) d'échanger avec vous \
pour discuter de vos besoins et de ma contribution potentielle.

Vous trouverez en pièce jointe ma proposition détaillée.

Bien cordialement,
{p.name}
{p.portfolio_url or ''}
{p.linkedin_url or ''}
"""

    def _generate_follow_up(self, p: FreelanceProfile, m: Mission) -> str:
        return f"""\
Bonjour{' ' + m.contact_name if m.contact_name else ''},

Je me permets de revenir vers vous concernant ma candidature pour \
la mission « {m.title} » envoyée récemment.

Je reste très intéressé(e) par cette opportunité et disponible \
pour un échange téléphonique ou visio à votre convenance.

N'hésitez pas à me contacter si vous souhaitez des informations \
complémentaires sur mon profil ou mes références.

Bien cordialement,
{p.name}
"""

    def _generate_linkedin_message(self, p: FreelanceProfile, m: Mission) -> str:
        return f"""\
Bonjour,

{p.title} avec {p.experience_years} ans d'expérience, j'ai vu votre offre \
« {m.title} » et elle correspond parfaitement à mon profil.

Compétences clés : {', '.join(p.skills[:3])}
Dispo : {p.availability}

Seriez-vous disponible pour un échange rapide ?

{p.name}
"""

    def _generate_elevator_pitch(self, p: FreelanceProfile, m: Mission) -> str:
        return f"""\
🎯 ELEVATOR PITCH (30 secondes)
────────────────────────────────

"Bonjour, je suis {p.name}, {p.title} {p.experience_level.value} \
avec {p.experience_years} ans d'expérience.

Je suis spécialisé(e) en {', '.join(p.skills[:3])}, et j'ai \
accompagné des entreprises dans des projets similaires à {m.title}.

Ce qui me différencie, c'est ma capacité à livrer rapidement \
des résultats concrets tout en maintenant un haut niveau de qualité.

Je suis disponible {p.availability.lower()} et je serais \
ravi(e) d'en discuter avec vous."
"""

    def _generate_negotiation_tips(self, p: FreelanceProfile, m: Mission) -> list[str]:
        tips = [
            f"TJM cible : {p.daily_rate_max}€/jour — ne descendez pas sous {p.daily_rate_min}€",
            "Mettez en avant la valeur apportée, pas le coût horaire",
            "Proposez un tarif dégressif pour les missions longues (>6 mois)",
        ]
        if m.budget_max > 0 and p.daily_rate_min <= m.budget_max:
            tips.append(
                f"Le budget client ({m.budget_max}€/j max) est dans votre fourchette — "
                f"positionnez-vous à {min(p.daily_rate_max, m.budget_max)}€/j"
            )
        if m.budget_max > 0 and p.daily_rate_min > m.budget_max:
            tips.append(
                f"⚠️ Votre TJM min ({p.daily_rate_min}€) dépasse le budget "
                f"({m.budget_max}€) — préparez des arguments solides ou "
                f"proposez un scope ajusté"
            )
        tips.extend([
            "Négociez aussi les conditions : remote, frais, matériel, congés",
            "Demandez la durée ferme vs renouvelable — préférez un engagement initial long",
            "Proposez une période d'essai courte (2 semaines) pour rassurer le client",
        ])
        return tips

    def _generate_interview_prep(self, p: FreelanceProfile, m: Mission) -> list[str]:
        matching = _find_matching_skills(p, m)
        prep = [
            f"Préparez des exemples concrets d'utilisation de : {', '.join(matching[:3]) if matching else ', '.join(p.skills[:3])}",
            "Ayez 2-3 cas de projets similaires avec résultats chiffrés",
            f"Renseignez-vous sur {m.company} : actualité, stack technique, culture",
            "Préparez des questions pertinentes sur le projet et l'équipe",
            "Ayez votre TJM en tête et vos arguments de valeur prêts",
        ]
        if m.description:
            prep.append(
                f"Relisez la description mission et identifiez les mots-clés : "
                f"« {m.description[:100]}... »"
            )
        prep.extend([
            "Préparez une démonstration ou un portfolio pertinent",
            "Anticipez la question : 'Pourquoi cette mission vous intéresse ?'",
            "Soyez prêt(e) à discuter de votre disponibilité et date de démarrage",
        ])
        return prep


def _find_matching_skills(profile: FreelanceProfile, mission: Mission) -> list[str]:
    """Trouve les compétences en commun entre profil et mission."""
    if not mission.skills_required:
        return profile.skills[:5]
    profile_lower = {s.lower(): s for s in profile.skills}
    matching = []
    for skill in mission.skills_required:
        if skill.lower() in profile_lower:
            matching.append(profile_lower[skill.lower()])
    # Ajouter les compétences du profil non matchées
    remaining = [s for s in profile.skills if s not in matching]
    return matching + remaining[:max(0, 5 - len(matching))]
