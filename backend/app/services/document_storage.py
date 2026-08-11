from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
INVOICES_DIR = BASE_DIR / "storage" / "invoices"
CONTRACTS_DIR = BASE_DIR / "storage" / "contracts"


def ensure_storage_dirs() -> None:
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)


def racun_path(msisdn_id: int) -> Path:
    return INVOICES_DIR / f"racun_{msisdn_id}.pdf"


def ugovor_path(msisdn_id: int) -> Path:
    return CONTRACTS_DIR / f"ugovor_{msisdn_id}.pdf"


def spremi_racun(msisdn_id: int, pdf_bytes: bytes) -> Path:
    ensure_storage_dirs()
    path = racun_path(msisdn_id)
    path.write_bytes(pdf_bytes)
    return path


def spremi_ugovor(msisdn_id: int, pdf_bytes: bytes) -> Path:
    ensure_storage_dirs()
    path = ugovor_path(msisdn_id)
    path.write_bytes(pdf_bytes)
    return path
