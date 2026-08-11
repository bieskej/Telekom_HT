# PDF fontovi (DejaVu Sans)

Za ispravan prikaz hrvatskih znakova (č, ć, đ, š, ž) u računima i ugovorima koriste se TrueType fontovi iz [DejaVu Fonts](https://dejavu-fonts.github.io/) (licenca: Bitstream Vera / Arev / DejaVu).

Datoteke u ovom direktoriju:

- `DejaVuSans.ttf`
- `DejaVuSans-Bold.ttf`
- `DejaVuSans-Oblique.ttf`

Registracija: `app/services/pdf_fonts.py`.

Ako fontovi nedostaju, preuzmite release zip i kopirajte iz podmape `ttf/`:

```powershell
curl.exe -L -o dejavu.zip https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip
# raspakiraj i kopiraj DejaVuSans.ttf, DejaVuSans-Bold.ttf, DejaVuSans-Oblique.ttf ovdje
```
