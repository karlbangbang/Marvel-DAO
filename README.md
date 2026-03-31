# FreelanceHunter

Outil CLI pour trouver des missions freelance adaptées à votre profil et générer automatiquement tout le matériel de candidature.

## Fonctionnalités

### Recherche de missions
- Recherche multi-plateformes : Malt, Freelance.com, Indeed, LinkedIn
- Matching intelligent profil/mission avec score de compatibilité
- Classement par pertinence (compétences, TJM, remote, expérience, localisation)

### Génération de candidatures
Pour chaque mission, génère automatiquement :
1. **Lettre de motivation** personnalisée
2. **Proposition commerciale** détaillée (approche, planning, tarifs)
3. **Résumé CV** adapté à la mission
4. **Email de candidature** prêt à envoyer
5. **Email de relance** pour le suivi
6. **Message LinkedIn** court et percutant
7. **Elevator pitch** de 30 secondes
8. **Conseils de négociation** (TJM, conditions)
9. **Préparation d'entretien** (questions, cas pratiques)
10. **Fiche mission** récapitulative

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Mode interactif (recommandé)
```bash
python -m freelance_hunter.cli interactive
```

### Créer un profil
```bash
python -m freelance_hunter.cli create-profile --output mon_profil.json
```

### Recherche automatique
```bash
python -m freelance_hunter.cli search --config mon_profil.json --max-results 20 --min-score 40
```

### Générer une candidature pour une mission spécifique
```bash
python -m freelance_hunter.cli generate \
  --config mon_profil.json \
  --mission-title "Dev Full Stack React/Node" \
  --company "StartupXYZ" \
  --description "Refonte plateforme e-commerce" \
  --skills "React,Node.js,TypeScript" \
  --budget-max 650
```

## Structure du projet

```
freelance_hunter/
├── __init__.py           # Package principal
├── cli.py                # Interface CLI (Click + Rich)
├── models.py             # Modèles de données (Profil, Mission, Candidature)
├── matcher.py            # Moteur de matching profil/mission
├── scrapers/
│   ├── base.py           # Scraper abstrait
│   ├── malt.py           # Scraper Malt
│   ├── freelance_com.py  # Scraper Freelance.com
│   ├── indeed.py         # Scraper Indeed
│   └── linkedin.py       # Scraper LinkedIn
└── generators/
    ├── application.py    # Générateur de candidatures
    └── exporter.py       # Export en fichiers texte
```

## Exemple de profil (JSON)

Voir `exemple_profil.json` pour un exemple complet.
