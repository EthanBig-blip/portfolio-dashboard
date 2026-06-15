# 📊 Portfolio Dashboard

> Dashboard de performance de portefeuille avec données de marché **live**, inspiré de [Ghostfolio](https://github.com/ghostfolio/ghostfolio).

## Stack

| Couche | Techno |
|---|---|
| Backend | Python 3.11 · FastAPI · yfinance · requests |
| Frontend | Vanilla JS · Chart.js 4 · HTML/CSS |
| Données | Yahoo Finance (S&P500, Nasdaq, MSCI, CAC40) · Taux Livret A |
| Deploy | Docker Compose |

## Fonctionnalités

- **KPI Cards** — Valeur totale, YTD, 1 an, Max, Capital investi
- **Graphique valeur totale** — avec courbe capital investi
- **Benchmark comparatif** — Portefeuille vs S&P 500, Nasdaq 100, MSCI World, CAC 40, Livret A
- **Benchmark KPI cards** — avec condition de marché (haussier/baissier/neutre)
- **Performance relative** — % gain vs capital investi
- **Tableau de performance** — par période (jour, semaine, mois, YTD, 1 an, max)
- **Dark / Light mode**
- **Sélecteur de période** — 1J / SEM / MOI / YTD / 1A / 5A / MAX

## Installation

### 1. Avec Docker (recommandé)

```bash
git clone https://github.com/EthanBig-blip/portfolio-dashboard
cd portfolio-dashboard
cp .env.example .env
docker compose up -d
```

Accès : http://localhost:8000

### 2. Manuel

```bash
git clone https://github.com/EthanBig-blip/portfolio-dashboard
cd portfolio-dashboard
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

## Configuration des transactions

Editez `data/transactions.json` :

```json
[
  {
    "date": "2024-01-15",
    "symbol": "BTC-USD",
    "type": "BUY",
    "quantity": 0.05,
    "price": 42000,
    "fee": 2.1,
    "currency": "USD"
  }
]
```

Types supportés : `BUY` | `SELL` | `DEPOSIT` | `WITHDRAW`

## Variables d'environnement

| Variable | Description | Défaut |
|---|---|---|
| `BASE_CURRENCY` | Devise de base | `EUR` |
| `CACHE_TTL` | Durée du cache en secondes | `300` |
| `PORT` | Port du serveur | `8000` |

## Architecture

```
portfolio-dashboard/
├── backend/
│   ├── main.py          # FastAPI app + routes
│   ├── market.py        # Fetch données live (yfinance)
│   ├── portfolio.py     # Calculs PnL, ROAI, performance
│   └── cache.py         # Cache TTL en mémoire
├── frontend/
│   └── index.html       # Dashboard complet (Chart.js)
├── data/
│   └── transactions.json
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## License

MIT
