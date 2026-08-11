_WEIGHTS = (7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2)


def normaliziraj_jmbg(jmbg: str) -> str:
    """Trim i samo znamenke, max 13."""
    return "".join(c for c in (jmbg or "").strip() if c.isdigit())[:13]


def validiraj_jmbg(jmbg: str) -> bool:
    if not jmbg or len(jmbg) != 13 or not jmbg.isdigit():
        return False
    total = sum(int(jmbg[i]) * _WEIGHTS[i] for i in range(12))
    remainder = total % 11
    kontrolna = 11 - remainder
    if kontrolna in (10, 11):
        kontrolna = 0
    return kontrolna == int(jmbg[12])
