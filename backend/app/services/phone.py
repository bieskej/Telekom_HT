def formatiraj_broj(broj: str) -> str:
    """Formatira nacionalni broj u +387 NN NNN NNN (ili varijantu za 9 znamenki)."""
    broj = broj.strip()
    if len(broj) == 8:
        return f"+387 {broj[0:2]} {broj[2:6]} {broj[6:8]}"
    if len(broj) == 9:
        return f"+387 {broj[0:2]} {broj[2:5]} {broj[5:9]}"
    if len(broj) >= 6:
        ndc = broj[:2]
        ostatak = broj[2:]
        sredina_len = len(ostatak) // 2
        return f"+387 {ndc} {ostatak[:sredina_len]} {ostatak[sredina_len:]}"
    return f"+387 {broj}"
