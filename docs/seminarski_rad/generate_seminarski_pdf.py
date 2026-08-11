# -*- coding: utf-8 -*-
"""Generira seminarski rad (ReportLab + DejaVu). Pokretanje iz roota repozitorija:
  cd backend && .venv\\Scripts\\python.exe ..\\docs\\seminarski_rad\\generate_seminarski_pdf.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.pdf_fonts import FONT_BOLD, FONT_REGULAR, pdf_set_font

OUT_DIR = Path(__file__).resolve().parent
OUT_PDF = OUT_DIR / "Bosko_Raguz_seminarski_rad_praksa.pdf"
DIAGRAM_DIR = OUT_DIR / "dijagrami"

MARGIN = 2.5 * cm


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            fontName=FONT_BOLD,
            fontSize=16,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName=FONT_REGULAR,
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName=FONT_BOLD,
            fontSize=14,
            leading=20,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName=FONT_BOLD,
            fontSize=12,
            leading=18,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            fontName=FONT_REGULAR,
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName=FONT_REGULAR,
            fontSize=12,
            leading=18,
            leftIndent=18,
            bulletIndent=6,
            spaceAfter=4,
        ),
        "toc": ParagraphStyle(
            "toc",
            fontName=FONT_REGULAR,
            fontSize=12,
            leading=20,
            leftIndent=12,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName=FONT_OBLIQUE if False else FONT_REGULAR,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.grey,
        ),
    }


FONT_OBLIQUE = "DejaVuSans-Oblique"


def _table(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), FONT_REGULAR),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6f0fa")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _draw_diagrams():
    """Jednostavni dijagrami (Pillow → PNG)."""
    from PIL import Image, ImageDraw, ImageFont

    DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    arch = DIAGRAM_DIR / "arhitektura.png"
    flow = DIAGRAM_DIR / "tok_dodjele.png"

    def _font(size=12):
        try:
            return ImageFont.truetype(str(BACKEND / "assets/fonts/DejaVuSans.ttf"), size)
        except OSError:
            return ImageFont.load_default()

    # Arhitektura
    w, h = 900, 320
    img = Image.new("RGB", (w, h), "white")
    dr = ImageDraw.Draw(img)
    f = _font(14)
    fs = _font(11)
    boxes = [
        (40, 100, 260, 180, "React SPA\n(port 5173)", "#0054A6"),
        (320, 100, 540, 180, "FastAPI REST\n(port 8004)", "#0077b6"),
        (600, 100, 820, 180, "PostgreSQL\n(inventar)", "#2d6a4f"),
    ]
    for left, top, right, bottom, label, col in boxes:
        dr.rounded_rectangle([left, top, right, bottom], radius=12, fill=col)
        lines = label.split("\n")
        ty = top + 20
        for line in lines:
            dr.text((left + 16, ty), line, fill="white", font=f)
            ty += 22
    dr.line([(260, 140), (320, 140)], fill="black", width=2)
    dr.line([(540, 140), (600, 140)], fill="black", width=2)
    dr.text((250, 148), "HTTPS /api", fill="black", font=fs)
    dr.text((580, 148), "SQL", fill="black", font=fs)
    dr.text((320, 260), "Slika 1. Tro-slojna arhitektura sustava", fill="#666666", font=fs)
    img.save(arch)

    # Tok dodjele
    w2, h2 = 900, 360
    img2 = Image.new("RGB", (w2, h2), "white")
    dr2 = ImageDraw.Draw(img2)
    steps = [
        "Odabir općine\ni kvalitete",
        "Rezervacija\nbroja (5 min)",
        "Unos kupca\n+ JMBG",
        "Plaćanje\ni potvrda",
        "Broj zauzet\n+ PDF ugovor",
    ]
    x0, y0 = 30, 120
    for i, txt in enumerate(steps):
        x1 = x0 + i * 168
        x2 = x1 + 150
        dr2.rounded_rectangle([x1, y0, x2, y0 + 90], radius=8, fill="#e6f7fc", outline="#0054A6", width=2)
        ty = y0 + 18
        for line in txt.split("\n"):
            dr2.text((x1 + 12, ty), line, fill="black", font=fs)
            ty += 20
        if i < len(steps) - 1:
            dr2.text((x2 + 6, y0 + 35), "→", fill="#0054A6", font=f)
    dr2.text((280, 280), "Slika 2. Tok dodjele broja kupcu", fill="#666666", font=fs)
    img2.save(flow)
    return arch, flow


def build_story():
    from app.services.pdf_fonts import _register_fonts

    _register_fonts()
    s = _styles()
    story = []

    # --- Naslovnica ---
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("SVEUČILIŠTE U MOSTARU", s["subtitle"]))
    story.append(
        Paragraph(
            "FAKULTET STROJARSTVA, RAČUNARSTVA I ELEKTROTEHNIKE",
            s["subtitle"],
        )
    )
    story.append(Spacer(1, 1.5 * cm))
    story.append(
        Paragraph(
            "Razvoj web sustava za upravljanje inventarom<br/>"
            "i automatsku dodjelu fiksnih telefonskih brojeva",
            s["title"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "<i>Seminarski rad na temelju stručne prakse</i>",
            s["subtitle"],
        )
    )
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("Boško Raguž", s["subtitle"]))
    story.append(Spacer(1, 1.5 * cm))
    meta = [
        ["Kolegij:", "Stručna praksa"],
        ["Studij:", "Računarstvo"],
        ["Organizacija prakse:", "Hrvatske telekomunikacije d.d. Mostar (HT Eronet)"],
        ["Voditelj prakse:", "Zlatko Raguž, dipl. ing. el."],
        ["Mentor (nalogodavac):", "Damir Zelenika, dipl. ing. el."],
        ["Broj projekta:", "H104515959"],
        ["Razdoblje prakse:", "12. 04. 2026. – 19. 06. 2026."],
        ["Mostar,", date.today().strftime("%Y.")],
    ]
    t_meta = Table(meta, colWidths=[5 * cm, 9 * cm])
    t_meta.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_REGULAR),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t_meta)
    story.append(PageBreak())

    # --- Sadržaj ---
    story.append(Paragraph("SADRŽAJ", s["h1"]))
    toc_items = [
        "1. Uvod",
        "2. Organizacija i mjesto prakse",
        "3. Opis projektnog zadatka",
        "4. Analiza problema i zahtjevi",
        "5. Korištene tehnologije",
        "6. Projektiranje sustava",
        "7. Implementacija",
        "8. Testiranje i rezultati",
        "9. Zaključak",
        "10. Literatura",
    ]
    for item in toc_items:
        story.append(Paragraph(item, s["toc"]))
    story.append(PageBreak())

    # --- 1 Uvod ---
    story.append(Paragraph("1. Uvod", s["h1"]))
    story.append(
        Paragraph(
            "Stručna praksa predstavlja priliku za primjenu teorijskog znanja stečenog "
            "tijekom studija na stvarnom ili realističnom poslovnom problemu. Tijekom prakse "
            "u Hrvatskim telekomunikacijama d.d. Mostar (HT Eronet) sudjelovao sam u razvoju "
            "web sustava za upravljanje inventarom fiksnih telefonskih brojeva i njihovu "
            "automatiziranu dodjelu korisnicima govorne usluge u nepokretnoj mreži.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Cilj prakse bio je razviti funkcionalni prototip koji prodajnom osoblju omogućuje "
            "brzu pretragu slobodnih brojeva, vremenski ograničenu rezervaciju te dovršetak "
            "dodjele uz validaciju identiteta kupca (JMBG) i izdavanje ugovora u PDF formatu. "
            "Paralelno je implementiran samoposlužni portal za kupce koji mogu pregledati "
            "dodijeljene brojeve povezane s vlastitim JMBG-om.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Cilj ovog seminarskog rada je opisati projektni zadatak, analizu problema, "
            "korištene tehnologije, projektiranje i implementaciju sustava te rezultate testiranja. "
            "Rad se fokusira na proces dodjele brojeva; ostali pomoćni moduli sustava nisu "
            "predmet detaljnog opisa.",
            s["body"],
        )
    )

    # --- 2 Organizacija ---
    story.append(Paragraph("2. Organizacija i mjesto prakse", s["h1"]))
    story.append(
        Paragraph(
            "Praksa je obavljena u Hrvatskim telekomunikacijama d.d. Mostar, operatoru "
            "fiksne telefonije HT Eronet na području Bosne i Hercegovine. Projekt je formalno "
            "evidentiran pod brojem H104515959, s planiranim trajanjem od 45 radnih dana "
            "(360 efektivnih sati), u razdoblju od 12. travnja do 19. lipnja 2026. godine.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Voditelj projekta na strani poslodavca bio je Zlatko Raguž, dipl. ing. el., "
            "a nalog za projekt izdao je Damir Zelenika, dipl. ing. el. Završno izvješće "
            "o projektu potvrđuje da su postavljeni ciljevi projekta ostvareni bez odstupanja "
            "od projektnog zadatka te da će se rezultati primijeniti u poslovnim sustavima "
            "HT Mostara. Projektna dokumentacija čuva se na adresi Kralja Tvrtka 18, Mostar.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Moja uloga u projektnom timu obuhvaćala je sudjelovanje u analizi zahtjeva, "
            "projektiranju arhitekture, implementaciji backend i frontend komponenti za dodjelu "
            "brojeva, izradi korisničkog sučelja te provođenju testiranja.",
            s["body"],
        )
    )

    # --- 3 Projektni zadatak ---
    story.append(Paragraph("3. Opis projektnog zadatka", s["h1"]))
    story.append(
        Paragraph(
            "Prema službenom obrascu „Prilog 1 – Obrazac za projektni zadatak“, naziv "
            "projekta glasi: <b>Izrada programa za dodjeljivanje numeracija korisnicima "
            "govorne usluge u nepokretnoj mreži</b>. Glavni cilj projekta je razvoj programa "
            "koji omogućuje centraliziranu i automatiziranu dodjelu numeracije korisnicima "
            "govorne usluge u fiksnoj mreži.",
            s["body"],
        )
    )
    story.append(Paragraph("Projekt je organiziran u četiri faze:", s["body"]))
    for f in [
        "inicijacija i analiza zahtjeva;",
        "dizajn sustava i arhitektura;",
        "razvoj (programiranje);",
        "testiranje (QA).",
    ]:
        story.append(Paragraph(f"• {f}", s["bullet"]))
    story.append(
        Paragraph(
            "Očekivana korist od projekta jest pružanje prodajnom osoblju automatizirane "
            "dodjele numeracije korisnicima govorne usluge u nepokretnoj mreži radi ubrzanja "
            "procesa aktivacije usluge. Planirani budžet projekta iznosio je 20.000 KM.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "U tehničkom smislu zadatak je realiziran kao web aplikacija s inventarom od "
            "približno 600.000 fiksnih MSISDN brojeva raspoređenih po administrativnoj "
            "hijerarhiji (općina → lokacija → uređaj MSAN/OLT → raspon brojeva). Sustav "
            "podržava pretragu i rezervaciju broja na pet minuta, dodjelu s odabirom kvalitete "
            "broja (silver, gold, platinum, diamond), validaciju JMBG-a algoritmom modul 11, "
            "mehanizam karantene nakon oslobađanja broja te županijski fallback kada u "
            "traženoj općini nema slobodnih brojeva.",
            s["body"],
        )
    )

    # --- 4 Zahtjevi ---
    story.append(Paragraph("4. Analiza problema i zahtjevi", s["h1"]))
    story.append(
        Paragraph(
            "U tradicionalnom poslovnom okruženju dodjela fiksnog broja može uključivati "
            "ručnu provjeru inventara, rizik dvostruke dodjele istog broja te neusklađenost "
            "podataka o kupcu. Problem koji sustav rješava jest potreba za jedinstvenim "
            "izvorom istine o statusu svakog broja (slobodan, zauzet, karantena) i "
            "standardiziranim tokom od pretrage do potpisivanja ugovora.",
            s["body"],
        )
    )
    story.append(Paragraph("Tablica 1. Pregled ključnih funkcionalnih zahtjeva", s["h2"]))
    req_data = [
        ["ID", "Zahtjev", "Prioritet"],
        ["F1", "Pregled inventara i zauzetosti po općinama (dashboard)", "Visok"],
        ["F2", "Pretraga slobodnih brojeva (uključujući wildcard uzorak)", "Visok"],
        ["F3", "Rezervacija broja na 5 minuta tijekom unosa podataka", "Visok"],
        ["F4", "Dodjela broja kupcu uz validaciju JMBG-a (modul 11)", "Visok"],
        ["F5", "Klasifikacija kvalitete broja i odabir pri dodjeli", "Srednji"],
        ["F6", "Karantena oslobođenih brojeva (zadano 60 dana)", "Srednji"],
        ["F7", "Županijski fallback ako u općini nema slobodnih brojeva", "Srednji"],
        ["F8", "Generiranje ugovora u PDF formatu nakon dodjele", "Visok"],
        ["F9", "Portal kupca: pregled brojeva po JMBG-u i preuzimanje ugovora", "Srednji"],
    ]
    story.append(_table(req_data, [1.2 * cm, 11.5 * cm, 2.5 * cm]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "Nefunkcionalni zahtjevi uključuju sigurnu autentifikaciju korisnika (JWT), "
            "razdvajanje uloga (admin, prodaja, kupac), responzivno korisničko sučelje te "
            "mogućnost pokretanja u razvojnom okruženju s proxyjem između frontenda i API-ja.",
            s["body"],
        )
    )

    # --- 5 Tehnologije ---
    story.append(Paragraph("5. Korištene tehnologije", s["h1"]))
    story.append(
        Paragraph(
            "Sustav je razvijen kao monorepo s odvojenim backend i frontend slojem. "
            "Komunikacija se odvija putem REST API-ja u JSON formatu.",
            s["body"],
        )
    )
    story.append(Paragraph("Tablica 2. Pregled korištenih tehnologija", s["h2"]))
    tech_data = [
        ["Sloj", "Tehnologija", "Uloga"],
        ["Backend", "Python 3, FastAPI", "REST API, validacija, poslovna logika"],
        ["Backend", "SQLAlchemy, Alembic", "ORM i migracije baze"],
        ["Backend", "PostgreSQL", "Relacijska baza inventara"],
        ["Backend", "JWT (python-jose), bcrypt", "Autentifikacija i hash lozinki"],
        ["Backend", "ReportLab", "Generiranje PDF ugovora i računa"],
        ["Backend", "APScheduler", "Cron: istek rezervacija i karantena"],
        ["Frontend", "React 19, TypeScript", "Jednostranična aplikacija (SPA)"],
        ["Frontend", "Vite", "Dev server, build, proxy /api → :8004"],
        ["Frontend", "Tailwind CSS, Radix UI", "Stilovi i pristupačne komponente"],
        ["Frontend", "Leaflet, Recharts", "Mapa zauzetosti i grafikoni"],
    ]
    story.append(_table(tech_data, [2.2 * cm, 4.5 * cm, 8.5 * cm]))

    # --- 6 Projektiranje ---
    story.append(PageBreak())
    story.append(Paragraph("6. Projektiranje sustava", s["h1"]))
    story.append(
        Paragraph(
            "Arhitektura sustava slijedi klasični tro-slojni model: klijentska React aplikacija "
            "u pregledniku, serverski FastAPI sloj i PostgreSQL baza podataka. U razvojnom "
            "okruženju Vite poslužitelj prosljeđuje zahtjeve s prefiksa /api na backend "
            "port 8004, čime se izbjegavaju CORS problemi.",
            s["body"],
        )
    )
    arch, flow = _draw_diagrams()
    story.append(Image(str(arch), width=15 * cm, height=5.8 * cm))
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "Konceptualni model podataka u centru ima entitet MSISDN s atributima broj, status, "
            "kvaliteta, JMBG kupca i vezom na raspon, uređaj i općinu. Korisnik sustava "
            "(radnik ili kupac) pohranjen je u tablici radnika s ulogom i opcionalnim JMBG-om "
            "za portal.",
            s["body"],
        )
    )
    story.append(Image(str(flow), width=15 * cm, height=9 * cm))
    story.append(
        Paragraph(
            "Tok dodjele (slika 2) započinje odabirom općine i kvalitete broja. Sustav "
            "automatski rezervira sljedeći slobodan broj na pet minuta. Nakon unosa podataka "
            "kupca i provjere JMBG-a korisnik potvrđuje plaćanje; backend postavlja status "
            "broja na zauzet, generira PDF ugovor i opcionalno šalje obavijest e-poštom.",
            s["body"],
        )
    )

    # --- 7 Implementacija ---
    story.append(Paragraph("7. Implementacija", s["h1"]))
    story.append(Paragraph("7.1. Backend", s["h2"]))
    story.append(
        Paragraph(
            "Poslovna logika dodjele koncentrirana je u modulu msisdn_service. Funkcija "
            "_find_slobodan_ids prvo traži slobodne brojeve u zadanoj općini; ako ih nema, "
            "aktivira se županijski fallback pretraživanjem svih općina iste županije "
            "(iznimka: Brčko i Banja Luka kao jednočlani poolovi). Rezervacija koristi "
            "vremenski žig rezervacije_do; istekle rezervacije čisti pozadinski zadatak.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Ključni API endpointi: POST /rezerviraj-sljedeci (rezervacija po općini i "
            "kvaliteti), GET /msisdn/provjeri-jmbg (provjera kontrolne znamenke i povijesti), "
            "POST /dodijeli-broj (finalna dodjela), GET /statistike i GET /opcine/geojson "
            "(dashboard i mapa). Autentifikacija se provodi JWT tokenom u Authorization headeru.",
            s["body"],
        )
    )
    story.append(Paragraph("7.2. Frontend", s["h2"]))
    story.append(
        Paragraph(
            "Stranica /dodjela nudi dva načina unosa: brza forma (sva polja na jednom ekranu) "
            "i čarobnjak u tri koraka (broj → kupac → plaćanje). Oba pristupa koriste iste "
            "API pozive i zajedničke komponente (PlacanjePolja, DodjelaSuccessModal, "
            "useReservationTimer za odbrojavanje rezervacije). Stranica /brojevi omogućuje "
            "pretragu i wildcard uzorak (npr. *1234 za zadnje četiri znamenke).",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Portal kupca (/portal) odvojen je od staff aplikacije: kupci se registriraju "
            "i prijavljuju zasebnim tokom, a brojevi se prikazuju prema podudarnosti JMBG-a "
            "između zapisa kupca i dodijeljenog MSISDN-a.",
            s["body"],
        )
    )
    story.append(Paragraph("7.3. Validacija JMBG-a i kvaliteta brojeva", s["h2"]))
    story.append(
        Paragraph(
            "JMBG (jedinstveni matični broj građana) sastoji se od 13 znamenki, pri čemu "
            "posljednja predstavlja kontrolnu znamenku izračunatu algoritmom modul 11. "
            "Sustav na frontendu i backendu provjerava format i kontrolnu znamenku prije "
            "dodjele. Endpoint provjeri-jmbg dodatno vraća upozorenja (npr. postojeći "
            "kupac s istim identifikatorom) koja se prikazuju prodavaču prije potvrde.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Kvaliteta broja (silver, gold, platinum, diamond) trajni je atribut MSISDN "
            "određen uzorkom zadnje četiri znamenke broja. Pri dodjeli prodavač filtrira "
            "koji se slobodan broj nudi prema odabranoj kategoriji i pripadajućoj cijeni; "
            "kategorija se ne mijenja u trenutku prodaje.",
            s["body"],
        )
    )
    story.append(Paragraph("7.4. Rezervacija i karantena", s["h2"]))
    story.append(
        Paragraph(
            "Kako bi se spriječila istovremena dodjela istog broja dvama prodavačima, "
            "sustav pri započinjanju dodjele rezervira odabrani MSISDN na pet minuta. "
            "Frontend prikazuje odbrojavanje (hook useReservationTimer); po isteku "
            "rezervacije dodjela se blokira dok se ne rezervira novi broj. Istekle "
            "rezervacije automatski se poništavaju pozadinskim zadatkom (APScheduler).",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Brojevi koji su oslobođeni nakon raskida ugovora ili isteka usluge ulaze u "
            "status karantena (zadano 60 dana) prije ponovne dostupnosti. To sprječava "
            "trenutnu ponovnu dodjelu broja koji je nedavno bio u upotrebi, u skladu s "
            "poslovnim pravilima operatora.",
            s["body"],
        )
    )
    story.append(Paragraph("7.5. Dashboard i pregled inventara", s["h2"]))
    story.append(
        Paragraph(
            "Početna stranica (dashboard) prikazuje ključne pokazatelje: ukupnu "
            "iskorištenost inventara, broj slobodnih i zauzetih MSISDN-ova te heatmap "
            "dodjela po danu i satu. Interaktivna mapa općina bojama označava postotak "
            "zauzetosti (zeleno &lt;50 %, narančasto 50–90 %, crveno ≥90 %). Važno je "
            "napomenuti da mapa koristi aproksimaciju bounding box koordinata općina, a "
            "ne službene katastarske granice.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "<i>[Slika 3 – placeholder: screenshot dashboarda s KPI karticama, mapom općina "
            "i heatmapom dodjela – učitati iz / na lokalnom okruženju.]</i>",
            s["caption"],
        )
    )
    story.append(
        Paragraph(
            "<i>[Slika 4 – placeholder: screenshot stranice /dodjela s rezervacijom broja "
            "i timerom od 5 minuta.]</i>",
            s["caption"],
        )
    )

    # --- 8 Testiranje ---
    story.append(Paragraph("8. Testiranje i rezultati", s["h1"]))
    story.append(
        Paragraph(
            "Backend je pokriven automatiziranim testovima (pytest). U trenutku izrade rada "
            "izvršeno je 202 uspješnih testova (1 preskočen), uključujući testove dodjele "
            "broja, rezervacije, validacije JMBG-a i županijskog fallbacka.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Ručno testiranje u pregledniku Chrome na adresi localhost:5173 obuhvatilo je: "
            "prijavu administratora putem Vite proxyja (/api), pretragu wildcard uzorka *1234, "
            "pregled dashboarda s mapom zauzetosti (općina Crnići s ≥90 % zauzetosti), "
            "učitavanje hijerarhije općina, te portal kupca nakon demo seed podataka "
            "(prijava, pregled brojeva, gumb za preuzimanje ugovora).",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Sustav u cjelini ispunjava projektni zadatak u obliku funkcionalnog demo "
            "prototipa. Završno izvješće o projektu (HT Mostar) potvrđuje ostvarenje "
            "dogovorenih ciljeva bez odstupanja u roku i broju efektivnih sati.",
            s["body"],
        )
    )

    # --- 9 Zaključak ---
    story.append(Paragraph("9. Zaključak", s["h1"]))
    story.append(
        Paragraph(
            "Tijekom stručne prakse u HT Mostaru razvijen je web sustav koji centralizira "
            "inventar fiksnih telefonskih brojeva i automatizira proces dodjele kupcu. "
            "Implementirane su ključne poslovne funkcije: rezervacija, validacija JMBG-a, "
            "kvaliteta brojeva, karantena, županijski fallback, dashboard zauzetosti te "
            "kupčev portal za pregled dodijeljenih brojeva.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Stečeno je praktično iskustvo u full-stack razvoju (FastAPI, React, PostgreSQL), "
            "projektiranju REST API-ja, radu s PDF dokumentima i izradi korisničkog sučelja "
            "prilagođenog operativnim korisnicima telekomunikacijskog operatora.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "Ograničenja prototipa valja istaknuti: mapa općina koristi aproksimaciju "
            "bounding box koordinata, a ne službene administrativne granice; inventar i "
            "zauzetost temelje se na demo seed podacima, a sustav nije integriran s "
            "produkcijskim BSS/OSS okruženjem operatora. Budući rad obuhvaćao bi integraciju "
            "s operativnim sustavima i proširenje sigurnosne i revizijske funkcionalnosti.",
            s["body"],
        )
    )

    # --- 10 Literatura ---
    story.append(Paragraph("10. Literatura", s["h1"]))
    refs = [
        "FastAPI Documentation. https://fastapi.tiangolo.com/ (pristupljeno 2026.).",
        "React Documentation. https://react.dev/ (pristupljeno 2026.).",
        "PostgreSQL Documentation. https://www.postgresql.org/docs/ (pristupljeno 2026.).",
        "SQLAlchemy Documentation. https://docs.sqlalchemy.org/ (pristupljeno 2026.).",
        "ReportLab User Guide. https://www.reportlab.com/docs/reportlab-userguide.pdf (pristupljeno 2026.).",
        "Nielsen, J. (1994). Usability Engineering. Academic Press.",
        "Zakon o jedinstvenom matičnom broju građana (JMBG). Službeni propisi BiH.",
        "Hrvatske telekomunikacije d.d. Mostar: Projektni zadatak br. H104515959 (interni dokument, 2026.).",
    ]
    for i, ref in enumerate(refs, 1):
        story.append(Paragraph(f"[{i}] {ref}", s["body"]))

    story.append(PageBreak())
    story.append(Paragraph("Prilog A — Pregled ključnih API ruta (dodjela)", s["h1"]))
    api_data = [
        ["Metoda", "Ruta", "Opis"],
        ["POST", "/prijava", "Prijava radnika (JWT)"],
        ["GET", "/opcine", "Katalog općina za dodjelu"],
        ["GET", "/kvalitete", "Kategorije i cijene brojeva"],
        ["POST", "/rezerviraj-sljedeci", "Rezervacija sljedećeg slobodnog broja"],
        ["POST", "/rezerviraj/{id}", "Rezervacija određenog MSISDN-a"],
        ["GET", "/msisdn/provjeri-jmbg", "Provjera JMBG-a i upozorenja"],
        ["POST", "/dodijeli-broj", "Finalna dodjela kupcu"],
        ["GET", "/statistike", "KPI za dashboard"],
        ["GET", "/opcine/geojson", "Podaci za mapu zauzetosti"],
        ["GET", "/kupac/moji-brojevi", "Portal: brojevi po JMBG-u"],
    ]
    story.append(_table(api_data, [2 * cm, 5.5 * cm, 8.7 * cm]))
    story.append(
        Paragraph(
            "Prilog B — Izvještaj o izvorima. Podaci o projektu (broj H104515959, datumi, "
            "mentori) preuzeti su OCR-om iz internih obrazaca HT Mostara (Projektni zadatak "
            "i Završno izvješće o projektu). Tehnički opis implementacije temelji se na "
            "izvornom kodu repozitorija Telekom_HT i dokumentaciji README.md te USER_FLOWS.md.",
            s["body"],
        )
    )

    return story


def main():
    pdf_set_font  # ensure fonts import side effect
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="Seminarski rad - Boško Raguž",
        author="Boško Raguž",
    )

    def _footer(canvas, doc_):
        if canvas.getPageNumber() <= 1:
            return
        canvas.saveState()
        pdf_set_font(canvas, "regular", 9)
        canvas.drawCentredString(A4[0] / 2, 1.2 * cm, str(canvas.getPageNumber() - 1))
        canvas.restoreState()

    doc.build(build_story(), onFirstPage=_footer, onLaterPages=_footer)
    print(f"PDF generiran: {OUT_PDF}")
    print(f"Velicina: {OUT_PDF.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
