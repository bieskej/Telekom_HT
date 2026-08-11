"""Jinja2 renderiranje HTML email predložaka."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_email_template(template_name: str, context: dict) -> str:
    """Renderira predložak (npr. dodjela.html) u HTML string."""
    return _env.get_template(template_name).render(**context)
