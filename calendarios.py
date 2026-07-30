#!/usr/bin/env python3
"""
Genera un archivo .ics por division, dentro de la carpeta cal/.

Por que archivos reales y no JavaScript: iOS Safari bloquea las descargas
tipo data: y las de Blob las manda a Archivos en vez de al calendario.
Un .ics servido por el servidor con Content-Type text/calendar hace que
Safari abra directo la hoja de "Anadir al calendario". Es lo unico que
funciona igual en iPhone, Android y computadora.

Lee los datos del propio index.html, asi que nunca se desincroniza.

Uso:  python3 calendarios.py
"""

import json, os, re, unicodedata
from datetime import datetime, timedelta

ANIO, MES = 2026, 8
DUR = 90                      # minutos que dura el turno
ANTES = 45                    # aviso: llegar 45 min antes
SEDE = "Cancha Collazo"
OUT = "cal"


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def leer_turnos(path="index.html"):
    m = re.search(r"^var S=(\[.*?\]);\s*$", open(path, encoding="utf-8").read(), re.S | re.M)
    if not m:
        raise SystemExit("No encontre 'var S=[...]' en index.html")
    return json.loads(m.group(1))


def fold(line):
    """RFC 5545: las lineas no deben pasar de 75 octetos."""
    b = line.encode("utf-8")
    if len(b) <= 73:
        return [line]
    out, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > 73:
            out.append(cur); cur = " " + ch
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def hhmm(mins):
    h, m = divmod(mins, 60)
    ap = "pm" if h >= 12 else "am"
    h = h % 12 or 12
    return f"{h}:{m:02d}{ap}"


def ics_de(division, turnos, stamp):
    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         "PRODID:-//Club Voleibol Vaqueros//Try-Outs 2026-27//ES",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         f"X-WR-CALNAME:Try-outs {division} - Vaqueros",
         "X-WR-TIMEZONE:America/Puerto_Rico"]
    for t in turnos:
        ini = datetime(ANIO, MES, t["dia"], t["min"] // 60, t["min"] % 60)
        fin = ini + timedelta(minutes=DUR)
        desc = (f"Try-out {division} - Club Voleibol Vaqueros 2026-27.\n"
                f"Llega entre 30 y 45 minutos antes (a las {hhmm(t['min'] - ANTES)}).\n"
                "Carpa 1 si ya estas inscrito; Carpa 2 si no.\n"
                "Coloca tu numero al frente de la camisa.\n"
                "Un (1) acompanante por participante.")
        L += ["BEGIN:VEVENT",
              f"UID:cvvb-{t['id']}-{slug(division)}@vaqueros",
              f"DTSTAMP:{stamp}",
              # Hora local flotante: cae a la hora de cancha sin importar
              # la zona horaria del telefono.
              f"DTSTART:{ini:%Y%m%dT%H%M%S}",
              f"DTEND:{fin:%Y%m%dT%H%M%S}",
              f"SUMMARY:Try-out {esc(division)} - Vaqueros",
              f"LOCATION:{esc(SEDE)}",
              f"DESCRIPTION:{esc(desc)}",
              "BEGIN:VALARM", "TRIGGER:-PT3H", "ACTION:DISPLAY",
              f"DESCRIPTION:Try-out {esc(division)} hoy a las {t['h']}",
              "END:VALARM", "END:VEVENT"]
    L.append("END:VCALENDAR")
    salida = []
    for line in L:
        salida += fold(line)
    return "\r\n".join(salida) + "\r\n"


def main():
    turnos = leer_turnos()
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    porDiv = {}
    for t in turnos:
        for d in t["divs"]:
            porDiv.setdefault(d, []).append(t)
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".ics"):
            os.remove(os.path.join(OUT, f))
    total = 0
    for d in sorted(porDiv):
        lst = sorted(porDiv[d], key=lambda t: (t["dia"], t["min"]))
        ruta = os.path.join(OUT, slug(d) + ".ics")
        open(ruta, "w", encoding="utf-8", newline="").write(ics_de(d, lst, stamp))
        total += len(lst)
        print(f"  {slug(d) + '.ics':34} {len(lst)} fecha(s)")
    print(f"{len(porDiv)} archivos, {total} eventos, en {OUT}/")


if __name__ == "__main__":
    main()
