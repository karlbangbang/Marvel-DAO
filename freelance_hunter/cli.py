"""Interface CLI interactive pour FreelanceHunter."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from freelance_hunter.models import (
    ContractType,
    ExperienceLevel,
    FreelanceProfile,
    Mission,
    RemotePolicy,
)
from freelance_hunter.matcher import rank_missions
from freelance_hunter.scrapers import (
    MaltScraper,
    FreelanceComScraper,
    IndeedFreelanceScraper,
    LinkedInScraper,
)
from freelance_hunter.generators.application import ApplicationGenerator
from freelance_hunter.generators.exporter import Exporter

console = Console()

BANNER = r"""
  ___              _                       _  _          _
 | __| _ ___ ___| |__ _ _ _  __ ___  | || |_  _ _ _| |_ ___ _ _
 | _| '_/ -_) -_) / _` | ' \/ _/ -_) | __ | || | ' \  _/ -_) '_|
 |_||_| \___\___|_\__,_|_||_\__\___| |_||_|\_,_|_||_\__\___|_|

  Trouvez vos missions freelance & generez vos candidatures
"""


@click.group()
@click.version_option(version="1.0.0")
def main():
    """FreelanceHunter — Outil de recherche de missions freelance."""
    pass


@main.command()
def interactive():
    """Mode interactif complet : profil -> recherche -> candidatures."""
    console.print(Panel(BANNER, style="bold cyan", box=box.DOUBLE))
    console.print()

    # Étape 1 : Créer ou charger le profil
    profile = _get_or_create_profile()
    console.print()
    console.print(Panel(f"[bold green]Profil chargé :[/] {profile.summary()}", box=box.ROUNDED))

    # Étape 2 : Rechercher des missions
    console.print()
    missions = _search_missions(profile)

    if not missions:
        console.print("[bold red]Aucune mission trouvée. Essayez avec un autre profil.[/]")
        return

    # Étape 3 : Afficher les résultats classés
    ranked = rank_missions(profile, missions, min_score=0)
    _display_missions(ranked)

    # Étape 4 : Générer les candidatures
    console.print()
    if Confirm.ask("[bold cyan]Générer les candidatures pour les meilleures missions ?[/]"):
        _generate_applications(profile, ranked)


@main.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="Fichier de profil JSON")
@click.option("--max-results", "-n", default=15, help="Nombre max de résultats")
@click.option("--min-score", "-s", default=30.0, help="Score minimum de matching")
@click.option("--output", "-o", default="output", help="Dossier de sortie")
def search(config: str, max_results: int, min_score: float, output: str):
    """Recherche automatique de missions à partir d'un profil JSON."""
    console.print(Panel(BANNER, style="bold cyan", box=box.DOUBLE))

    if not config:
        console.print("[bold red]Veuillez fournir un fichier de profil avec --config[/]")
        console.print("Exemple : freelance-hunter search --config mon_profil.json")
        console.print("\nUtilisez 'freelance-hunter create-profile' pour en créer un.")
        return

    profile = _load_profile(config)
    console.print(Panel(f"[bold green]Profil :[/] {profile.summary()}", box=box.ROUNDED))

    missions = _search_missions(profile, max_results)
    ranked = rank_missions(profile, missions, min_score)

    if not ranked:
        console.print(f"[bold red]Aucune mission avec un score >= {min_score}%[/]")
        return

    _display_missions(ranked)

    generator = ApplicationGenerator()
    exporter = Exporter(output)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Génération des candidatures...", total=len(ranked))
        for mission in ranked:
            package = generator.generate(profile, mission)
            result_dir = exporter.export(package)
            progress.advance(task)

    console.print(f"\n[bold green]Candidatures exportées dans : {output}/[/]")


@main.command(name="create-profile")
@click.option("--output", "-o", default="mon_profil.json", help="Fichier de sortie")
def create_profile(output: str):
    """Crée un profil freelance en mode interactif."""
    console.print(Panel(BANNER, style="bold cyan", box=box.DOUBLE))
    profile = _create_profile_interactive()
    _save_profile(profile, output)
    console.print(f"\n[bold green]Profil sauvegardé dans : {output}[/]")


@main.command(name="generate")
@click.option("--config", "-c", required=True, type=click.Path(exists=True), help="Profil JSON")
@click.option("--mission-title", "-t", required=True, help="Titre de la mission")
@click.option("--company", default="", help="Nom de l'entreprise")
@click.option("--description", "-d", default="", help="Description de la mission")
@click.option("--skills", "-s", default="", help="Compétences requises (séparées par des virgules)")
@click.option("--budget-max", default=0, type=int, help="Budget max TJM")
@click.option("--output", "-o", default="output", help="Dossier de sortie")
def generate(config, mission_title, company, description, skills, budget_max, output):
    """Génère une candidature pour une mission spécifique."""
    console.print(Panel(BANNER, style="bold cyan", box=box.DOUBLE))

    profile = _load_profile(config)
    mission = Mission(
        title=mission_title,
        company=company,
        description=description,
        skills_required=[s.strip() for s in skills.split(",") if s.strip()],
        budget_max=budget_max,
        source="Manuel",
    )

    generator = ApplicationGenerator()
    exporter = Exporter(output)
    package = generator.generate(profile, mission)
    result_dir = exporter.export(package)

    console.print(f"\n[bold green]Candidature générée dans : {result_dir}[/]")
    _display_package_summary(package)


# ── Fonctions internes ────────────────────────────────────────


def _get_or_create_profile() -> FreelanceProfile:
    """Charge un profil existant ou en crée un nouveau."""
    config_path = Path("mon_profil.json")
    if config_path.exists():
        if Confirm.ask(f"[cyan]Profil trouvé ({config_path}). Le charger ?[/]", default=True):
            return _load_profile(str(config_path))

    console.print("[bold cyan]Création de votre profil freelance[/]\n")
    profile = _create_profile_interactive()

    if Confirm.ask("[cyan]Sauvegarder ce profil ?[/]", default=True):
        filename = Prompt.ask("Nom du fichier", default="mon_profil.json")
        _save_profile(profile, filename)
        console.print(f"[green]Profil sauvegardé : {filename}[/]")

    return profile


def _create_profile_interactive() -> FreelanceProfile:
    """Crée un profil freelance via prompts interactifs."""
    name = Prompt.ask("[bold]Votre nom complet")
    title = Prompt.ask("[bold]Votre titre", default="Développeur Full Stack")

    skills_input = Prompt.ask(
        "[bold]Vos compétences[/] (séparées par des virgules)",
        default="Python, JavaScript, React, Node.js, SQL"
    )
    skills = [s.strip() for s in skills_input.split(",") if s.strip()]

    years = IntPrompt.ask("[bold]Années d'expérience", default=5)

    level_choices = "/".join(e.value for e in ExperienceLevel)
    level_input = Prompt.ask(
        f"[bold]Niveau ({level_choices})", default="intermediate"
    )
    level = ExperienceLevel(level_input) if level_input in [e.value for e in ExperienceLevel] else ExperienceLevel.INTERMEDIATE

    rate_min = IntPrompt.ask("[bold]TJM minimum (€)", default=400)
    rate_max = IntPrompt.ask("[bold]TJM maximum (€)", default=600)

    location = Prompt.ask("[bold]Localisation", default="Paris")

    remote_choices = "/".join(r.value for r in RemotePolicy)
    remote_input = Prompt.ask(
        f"[bold]Préférence remote ({remote_choices})", default="full_remote"
    )
    remote = RemotePolicy(remote_input) if remote_input in [r.value for r in RemotePolicy] else RemotePolicy.FULL_REMOTE

    languages_input = Prompt.ask("[bold]Langues", default="Français, Anglais")
    languages = [l.strip() for l in languages_input.split(",") if l.strip()]

    bio = Prompt.ask("[bold]Bio courte (optionnel)", default="")

    industries_input = Prompt.ask(
        "[bold]Secteurs préférés (optionnel)", default=""
    )
    industries = [i.strip() for i in industries_input.split(",") if i.strip()]

    availability = Prompt.ask("[bold]Disponibilité", default="immédiate")

    return FreelanceProfile(
        name=name,
        title=title,
        skills=skills,
        experience_years=years,
        experience_level=level,
        daily_rate_min=rate_min,
        daily_rate_max=rate_max,
        location=location,
        remote_preference=remote,
        languages=languages,
        bio=bio,
        industries=industries,
        availability=availability,
    )


def _load_profile(filepath: str) -> FreelanceProfile:
    """Charge un profil depuis un fichier JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return FreelanceProfile(
        name=data.get("name", ""),
        title=data.get("title", ""),
        skills=data.get("skills", []),
        experience_years=data.get("experience_years", 0),
        experience_level=ExperienceLevel(data.get("experience_level", "intermediate")),
        daily_rate_min=data.get("daily_rate_min", 0),
        daily_rate_max=data.get("daily_rate_max", 0),
        location=data.get("location", ""),
        remote_preference=RemotePolicy(data.get("remote_preference", "full_remote")),
        languages=data.get("languages", ["Français"]),
        bio=data.get("bio", ""),
        portfolio_url=data.get("portfolio_url", ""),
        linkedin_url=data.get("linkedin_url", ""),
        certifications=data.get("certifications", []),
        industries=data.get("industries", []),
        availability=data.get("availability", "immédiate"),
    )


def _save_profile(profile: FreelanceProfile, filepath: str):
    """Sauvegarde un profil en JSON."""
    data = {
        "name": profile.name,
        "title": profile.title,
        "skills": profile.skills,
        "experience_years": profile.experience_years,
        "experience_level": profile.experience_level.value,
        "daily_rate_min": profile.daily_rate_min,
        "daily_rate_max": profile.daily_rate_max,
        "location": profile.location,
        "remote_preference": profile.remote_preference.value,
        "languages": profile.languages,
        "bio": profile.bio,
        "portfolio_url": profile.portfolio_url,
        "linkedin_url": profile.linkedin_url,
        "certifications": profile.certifications,
        "industries": profile.industries,
        "availability": profile.availability,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _search_missions(
    profile: FreelanceProfile, max_results: int = 15
) -> list[Mission]:
    """Lance la recherche sur toutes les plateformes."""
    scrapers = [
        MaltScraper(),
        FreelanceComScraper(),
        IndeedFreelanceScraper(),
        LinkedInScraper(),
    ]

    all_missions: list[Mission] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for scraper in scrapers:
            task = progress.add_task(
                f"Recherche sur {scraper.PLATFORM_NAME}...", total=None
            )
            try:
                missions = scraper.search(profile, max_results=max_results)
                all_missions.extend(missions)
                progress.update(
                    task,
                    description=f"[green]{scraper.PLATFORM_NAME} : {len(missions)} missions[/]",
                    completed=True,
                )
            except Exception as e:
                progress.update(
                    task,
                    description=f"[red]{scraper.PLATFORM_NAME} : erreur ({e})[/]",
                    completed=True,
                )

    console.print(f"\n[bold]Total : {len(all_missions)} missions trouvées[/]")
    return all_missions


def _display_missions(missions: list[Mission]):
    """Affiche les missions dans un tableau Rich."""
    table = Table(
        title="Missions trouvées (classées par matching)",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Score", style="bold", width=7)
    table.add_column("Plateforme", width=14)
    table.add_column("Titre", style="cyan", min_width=25)
    table.add_column("Entreprise", width=20)
    table.add_column("TJM", width=12)
    table.add_column("Remote", width=12)
    table.add_column("Durée", width=12)

    for i, m in enumerate(missions[:20], 1):
        score_color = "green" if m.match_score >= 70 else "yellow" if m.match_score >= 40 else "red"
        budget = ""
        if m.budget_min and m.budget_max:
            budget = f"{m.budget_min}-{m.budget_max}€"
        elif m.budget_max:
            budget = f"≤{m.budget_max}€"

        table.add_row(
            str(i),
            f"[{score_color}]{m.match_score}%[/]",
            m.source,
            m.title[:40],
            m.company[:20],
            budget,
            m.remote_policy.value.replace("_", " "),
            m.duration,
        )

    console.print(table)


def _generate_applications(profile: FreelanceProfile, missions: list[Mission]):
    """Génère les candidatures pour les missions sélectionnées."""
    top_n_input = Prompt.ask(
        "[cyan]Combien de missions ? (top N)[/]",
        default="5",
    )
    top_n = min(int(top_n_input), len(missions))
    selected = missions[:top_n]

    output_dir = Prompt.ask("[cyan]Dossier de sortie[/]", default="output")
    generator = ApplicationGenerator()
    exporter = Exporter(output_dir)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Génération des candidatures...", total=top_n)
        for mission in selected:
            package = generator.generate(profile, mission)
            result_dir = exporter.export(package)
            progress.advance(task)

    console.print(f"\n[bold green]{'═' * 50}[/]")
    console.print(f"[bold green]  {top_n} candidatures générées dans : {output_dir}/[/]")
    console.print(f"[bold green]{'═' * 50}[/]")

    console.print("\n[bold]Chaque dossier contient :[/]")
    console.print("  1. Lettre de motivation personnalisée")
    console.print("  2. Proposition commerciale détaillée")
    console.print("  3. Résumé CV adapté à la mission")
    console.print("  4. Email de candidature prêt à envoyer")
    console.print("  5. Email de relance")
    console.print("  6. Message LinkedIn")
    console.print("  7. Elevator pitch")
    console.print("  8. Conseils de négociation")
    console.print("  9. Préparation d'entretien")
    console.print("  10. Fiche mission récapitulative")


def _display_package_summary(package: ApplicationPackage):
    """Affiche un résumé du package généré."""
    console.print("\n[bold]Documents générés :[/]")
    docs = [
        ("Lettre de motivation", len(package.cover_letter)),
        ("Proposition commerciale", len(package.proposal)),
        ("Résumé CV", len(package.cv_summary)),
        ("Email candidature", len(package.email_body)),
        ("Email relance", len(package.follow_up_email)),
        ("Message LinkedIn", len(package.linkedin_message)),
        ("Elevator pitch", len(package.elevator_pitch)),
        ("Conseils négociation", len(package.negotiation_tips)),
        ("Préparation entretien", len(package.interview_prep)),
    ]
    for name, size in docs:
        console.print(f"  [green]✓[/] {name}")


if __name__ == "__main__":
    main()
