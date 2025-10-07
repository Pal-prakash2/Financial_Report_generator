# Financial Report Generator

Automate extraction, validation, and delivery of financial data from Indian MCA (AOC-4) XBRL filings for NIFTY 100 companies. The project provides a FastAPI backend, database models, validation flows, and Excel export utilities tailored for the Ind AS taxonomy.

## Features

- **XBRL Parsing**: Convert Ind AS tags into standardized Balance Sheet, Income Statement, and Cash Flow structures.
- **Validation Engine**: Ensure core accounting identities (Assets = Liabilities + Equity) stay within tolerance.
- **REST API**: FastAPI endpoints to register companies and preview XBRL filings.
- **Excel Exports**: Generate analyst-ready workbooks with audit trail hyperlinks.
- **Extensible Services**: Stubs for MCA monitoring and future automation.

## Project Layout

```
app/
	main.py              # FastAPI application factory
	config.py            # Environment configuration
	db/session.py        # SQLAlchemy engine and session helpers
	models/              # ORM models (Company, Filing, FinancialData)
	schemas/             # Pydantic schemas for API & services
	parsers/             # Ind AS XBRL parsing and taxonomy mappings
	services/            # Domain services (XBRL, validation, Excel, MCA)
	api/v1/              # Versioned API routers
	utils/               # Currency/date helpers and constants
main.py                 # Uvicorn entrypoint for local dev
requirements.txt        # Python dependencies
README.md               # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 13+ (for persistent storage)

### Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set up environment variables in a `.env` file as needed (database URL, AWS credentials, etc.). A sample `.env`:

```
DATABASE_URL=postgresql+psycopg2://fdg:fdg@localhost:5432/fdg
ENVIRONMENT=development
```

### Running the API

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Navigate to `http://127.0.0.1:8000/docs` for interactive Swagger docs.

### Uploading an XBRL Filing

1. Register a company via `POST /api/v1/companies`.
2. Upload an MCA XBRL file via `POST /api/v1/companies/{cin}/filings/preview` to receive standardized statements and validation feedback.

### Tests

```powershell
pytest
```

## Next Steps

- Implement persistent storage for parsed statements.
- Integrate official MCA data sources and scheduling.
- Harden validation rules (cash flow reconciliation, disclosure checks).
- Add authentication and role-based access for analysts.

## License

MIT License
