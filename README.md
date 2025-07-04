# 🛸 Project42Lit – Fitness Challenge App für Nerds

**Project42** ist eine nerdige Abnehm- und Fitness-Challenge unter Freunden – inspiriert von *Per Anhalter durch die Galaxis* und *Zurück in die Zukunft*.  
Diese App trackt euer Gewicht, zeigt Fortschritte, verteilt Challenges – und wird von Marvin, dem sarkastischen Fitness-Bot, kommentiert.

---

## 🚀 Features

- 🧑‍🚀 Benutzer-Login & Registrierung
- ⚖️ Gewichtstracking (pro Nutzer, mit Verlauf)
- 📊 Öffentliche Fortschrittscharts
- 🤖 Tägliche Fitness-Challenges von Marvin
- ✅ Challenge-Erledigung wird pro Tag gespeichert
- 🔎 Auswahlfilter für Nutzerdiagramme
- 🐳 Docker + PostgreSQL Setup

---

## Example .env File

POSTGRES_DB=project42
POSTGRES_USER=project42_user
POSTGRES_PASSWORD=supersecurepassword
POSTGRES_HOST=db
POSTGRES_PORT=5432

## 📦 Setup (Docker)

```bash
git clone https://github.com/dhuuk42/Project42Lit.git
cd Project42Lit
cp .env.example .env  # passe Variablen bei Bedarf an
docker compose up --build

