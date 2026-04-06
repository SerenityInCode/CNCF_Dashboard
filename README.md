# CNCF Maintainers Dashboard

An interactive dashboard for exploring CNCF (Cloud Native Computing Foundation) project maintainers — who they are, which companies they work for, and how they're distributed across projects.

## Overview

The dashboard loads data from `data/project-maintainers.csv` and provides four interactive views:

| Tab | What it shows |
|-----|---------------|
| **Company Overview** | Top 30 companies by maintainer count. When you search a company, a second chart appears showing which projects that company's maintainers are active in. |
| **Project Overview** | Maintainers per project (bar chart) + project count by status (donut chart). |
| **Cross-Project Maintainers** | People who maintain more than one CNCF project — bar chart + searchable table. |
| **Maintainers Table** | Full searchable, sortable table of all maintainers. |

**Sidebar filters** apply across all tabs:
- **Filter by Status** — Graduated / Incubating / Sandbox
- **Filter by Project** — multi-select dropdown (options update based on the selected status)
- **Search Company** — case-insensitive partial match

**KPI cards** at the top always reflect the current filter state:
- Total Maintainers · Unique Companies · Projects · Top Company

## Dataset

`data/project-maintainers.csv` — 2,259 maintainers across 236 projects from 479 companies.

Columns: `Status`, `Project`, `Maintainer`, `Company`, `GitHub`, `OwnersURL`

Project statuses:
- **Graduated** — mature, production ready projects (e.g. Kubernetes, Prometheus, Helm)
- **Incubating** — growing projects with proven adoption (e.g. gRPC, NATS, Notary)
- **Sandbox** — early stage experimental projects

## Requirements

- Python 3.8+

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
python dashboard.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

## Project Structure

```
cncf_dashboard/
├── dashboard.py            
├── data/
│   └── project-maintainers.csv
└── README.md
└── requirements.txt


```
