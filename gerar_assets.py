#!/usr/bin/env python3
"""
Gera os assets SVG animados do README de perfil (tema escuro e claro) e o preview.html.

Uso:  python gerar_assets.py
Para evoluir: edite os dicionários PROJETOS, STACK, PAPEIS e TERMINAL abaixo e rode de novo.
GitHub exibe SVGs como imagem: animações SMIL/CSS funcionam, JavaScript e fontes externas não.
"""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"

SANS = "'Segoe UI',system-ui,-apple-system,Helvetica,Arial,sans-serif"
MONO = "'Cascadia Code',Consolas,'SF Mono',Menlo,monospace"

THEMES = {
    "dark": dict(bg="#0B1426", surface="#101F38", surface2="#0D1A31", border="#1E3A66",
                 text="#E8F1FD", muted="#9DBCE8", grid="#15284A", accent="#2379E8",
                 accent2="#5DB7FF", orb=".50", purple="#7C5CFF", teal="#2DD4BF"),
    "light": dict(bg="#F5F8FF", surface="#FFFFFF", surface2="#EEF4FF", border="#D6E4F7",
                  text="#0F1E3A", muted="#475569", grid="#E2EBF9", accent="#136ED6",
                  accent2="#2379E8", orb=".22", purple="#7C5CFF", teal="#14B8A6"),
}

# ───────────────────────────── conteúdo editável ─────────────────────────────

PAPEIS = [
    "apps mobile com Flutter",
    "PWAs com Next.js",
    "APIs REST em Python e Java",
    "integrações com IA via MCP",
]

TERMINAL = [
    ("cmd", "whoami"),
    ("out", "Jefferson Silva — Desenvolvedor Full Stack · São Paulo, BR"),
    ("cmd", "cat formacao.txt"),
    ("ok", "Técnico em Desenvolvimento de Sistemas"),
    ("out", "ADS — Análise e Desenvolvimento de Sistemas (em andamento)"),
    ("cmd", "ls projetos/ --destaques"),
    ("hi", "chega-junto · agenda-jeff · apiclassroom · slides-nspaz"),
    ("cmd", "echo $FOCO"),
    ("out", "IA aplicada · Cloud & DevOps · Mobile"),
]

PROJETOS = [
    dict(slug="chega-junto", nome="Chega Junto", cat="MOBILE + IA", glyph="+",
         desc=["Preparação para consultas e exames, com relatos",
               "organizados por IA sob revisão humana."],
         tags=["Flutter", "FastAPI", "IA", "Android"], dark="#2DD4BF", light="#0D9488"),
    dict(slug="agenda-jeff", nome="Agenda Jeff", cat="PWA", glyph="✓",
         desc=["Hábitos, agenda, estudos e projetos em um só lugar,",
               "com modo offline, Web Push e API/MCP."],
         tags=["Next.js", "TypeScript", "Supabase", "PWA"], dark="#5DB7FF", light="#136ED6"),
    dict(slug="apiclassroom", nome="APIClassroom", cat="INTEGRAÇÃO + IA", glyph="{ }",
         desc=["Google Classroom e Drive consultados pelo ChatGPT",
               "via MCP, com OAuth e acesso somente leitura."],
         tags=["Python", "FastAPI", "MCP", "Auth0"], dark="#FBBF24", light="#B45309"),
    dict(slug="slides-nspaz", nome="Slides NSPAZ", cat="AUTOMAÇÃO", glyph="▶",
         desc=["Gera apresentações litúrgicas em PowerPoint",
               "automaticamente a partir de uma interface web."],
         tags=["Python", "Flask", "PowerPoint"], dark="#F472B6", light="#DB2777"),
]

# Ícones baixados de skillicons.dev (ids em https://skillicons.dev) e guardados em .icon-cache/
# Cada linha da lista = uma linha de painéis no card.
STACK = [
    [("LINGUAGENS", [("ts", "TypeScript"), ("js", "JavaScript"), ("python", "Python"), ("java", "Java"),
                     ("php", "PHP"), ("dart", "Dart"), ("kotlin", "Kotlin"), ("c", "C")]),
     ("MOBILE", [("flutter", "Flutter"), ("androidstudio", "Android")])],
    [("FRONTEND", [("react", "React"), ("nextjs", "Next.js"), ("tailwind", "Tailwind"), ("html", "HTML"),
                   ("css", "CSS"), ("figma", "Figma")]),
     ("BACKEND", [("nodejs", "Node.js"), ("fastapi", "FastAPI"), ("flask", "Flask"), ("spring", "Spring")])],
    [("DADOS", [("supabase", "Supabase"), ("postgres", "PostgreSQL"), ("mysql", "MySQL"), ("firebase", "Firebase")]),
     ("DEVOPS & NUVEM", [("docker", "Docker"), ("githubactions", "Actions"), ("aws", "AWS"),
                         ("vercel", "Vercel"), ("git", "Git")])],
]

# ───────────────────────────── utilitários ─────────────────────────────

def e(s: str) -> str:
    return escape(s, quote=True)


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{e(label)}" xml:space="preserve" style="white-space:pre">\n{body}\n</svg>\n')


def anim_vals(points):
    """points: lista de (keyTime, valor) -> (values, keyTimes) com keyTimes não decrescentes."""
    pts = sorted(points, key=lambda p: p[0])
    kt = ";".join(f"{max(0, min(1, k)):.4f}" for k, _ in pts)
    vals = ";".join(str(v) for _, v in pts)
    return vals, kt


def janela_opacity(a, b, eps=0.015, end_hold=False):
    """Opacidade 0 -> 1 em [a, b] dentro de um ciclo 0..1."""
    pts = [(0, 0 if a > 0 else 1)]
    if a > 0:
        pts += [(a, 0), (a + eps, 1)]
    if b < 1:
        pts += [(b - eps, 1), (b, 0), (1, 0)]
    else:
        pts += [(1 - eps, 1), (1, 0 if end_hold else 1)]
    return anim_vals(pts)


def pill(x, y, text, t, color=None, h=30, size=13, fill=None, stroke=None, text_fill=None):
    w = len(text) * size * 0.58 + (40 if color else 26)
    out = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" '
           f'fill="{fill or t["surface2"]}" stroke="{stroke or t["border"]}"/>')
    tx = x + 13
    if color:
        out += f'<circle cx="{x + 17:.1f}" cy="{y + h/2}" r="{h*0.16:.1f}" fill="{color}"/>'
        tx = x + 28
    out += (f'<text x="{tx:.1f}" y="{y + h/2 + size*0.36:.1f}" font-family="{SANS}" font-size="{size}" '
            f'fill="{text_fill or t["text"]}">{e(text)}</text>')
    return out, w

# ───────────────────────────── HERO ─────────────────────────────

def hero(t):
    W, H = 1200, 430
    n = len(PAPEIS)
    dur = n * 3.2
    size = 24
    cw = size * 0.6
    prefix = "> eu construo "
    x0 = 64 + len(prefix) * cw
    y_role = 282

    defs = f'''<defs>
 <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{t['grid']}" stroke-width="1"/></pattern>
 <radialGradient id="fade" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
 <mask id="gm"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
 <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
 <linearGradient id="name" x1="0" x2="1"><stop stop-color="{t['accent2']}"/><stop offset=".5" stop-color="{t['purple']}"/><stop offset="1" stop-color="{t['teal']}"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="-0.4 0;0.4 0;-0.4 0" dur="8s" repeatCount="indefinite"/></linearGradient>
 <linearGradient id="spread" gradientUnits="userSpaceOnUse" x1="0" x2="{W}"><stop stop-color="{t['accent']}"/><stop offset=".5" stop-color="{t['purple']}"/><stop offset="1" stop-color="{t['teal']}"/></linearGradient>
 <clipPath id="card"><rect width="{W}" height="{H}" rx="24"/></clipPath>
'''
    roles_svg = ""
    cursor_pts = []
    for i, r in enumerate(PAPEIS):
        a, b = i / n, (i + 1) / n
        typed = a + (b - a) * 0.38
        wfull = len(r) * cw + 4
        defs += (f' <clipPath id="r{i}"><rect x="{x0}" y="{y_role - 30}" width="0" height="42">'
                 f'<animate attributeName="width" values="0;0;{wfull:.0f};{wfull:.0f};0;0" '
                 f'keyTimes="0;{a:.4f};{typed:.4f};{b - 0.03:.4f};{b - 0.005:.4f};1" dur="{dur}s" repeatCount="indefinite"/>'
                 f'</rect></clipPath>\n')
        roles_svg += (f'<text x="{x0}" y="{y_role}" font-family="{MONO}" font-size="{size}" font-weight="600" '
                      f'fill="{t["text"]}" clip-path="url(#r{i})">{e(r)}</text>\n')
        cursor_pts += [(a, x0), (typed, x0 + wfull), (b - 0.03, x0 + wfull), (b - 0.005, x0)]
    cursor_pts = [(0, x0)] + [p for p in cursor_pts if p[0] > 0] + [(1, x0)]
    cv, ck = anim_vals(cursor_pts)
    defs += "</defs>"

    chips, cx = "", 64
    for c in ["Full Stack", "Mobile", "IA aplicada", "Cloud & DevOps", "70+ repositórios"]:
        p, w = pill(cx, 326, c, t, h=34, size=14)
        chips += p
        cx += w + 10

    # janela de código flutuante
    code = [
        [("const ", "#C792EA"), ("jeff", t["accent2"]), (" = {", t["text"])],
        [("  foco", t["teal"]), (": ", t["text"]), ('"produto"', "#F2B66D"), (",", t["text"])],
        [("  stack", t["teal"]), (": [", t["text"]), ('"TS"', "#F2B66D"), (", ", t["text"]), ('"Py"', "#F2B66D"), (", ", t["text"]), ('"Dart"', "#F2B66D"), ("],", t["text"])],
        [("  mobile", t["teal"]), (": ", t["text"]), ("true", "#FF7AA2"), (",", t["text"])],
        [("  ia", t["teal"]), (": ", t["text"]), ('"mcp + llm"', "#F2B66D"), (",", t["text"])],
        [("  deploy", t["teal"]), (": ", t["text"]), ("() => ", "#C792EA"), ('"vercel"', "#F2B66D")],
        [("};", t["text"])],
    ]
    code_svg = ""
    for i, segs in enumerate(code):
        a = 0.05 + i * 0.07
        ov, ok = anim_vals([(0, 0), (a, 0), (a + 0.04, 1), (0.92, 1), (0.97, 0), (1, 0)])
        indent = len(segs[0][0]) - len(segs[0][0].lstrip(" "))
        segs = [(segs[0][0].lstrip(" "), segs[0][1])] + segs[1:]
        tsp = "".join(f'<tspan fill="{c}">{e(s)}</tspan>' for s, c in segs)
        code_svg += (f'<text x="{796 + indent * 9}" y="{150 + i * 28}" font-family="{MONO}" font-size="15" opacity="0">'
                     f'<animate attributeName="opacity" values="{ov}" keyTimes="{ok}" dur="9s" repeatCount="indefinite"/>{tsp}</text>\n')
        code_svg += f'<text x="772" y="{150 + i * 28}" font-family="{MONO}" font-size="13" fill="{t["muted"]}" opacity=".45">{i + 1}</text>'

    body = f'''{defs}
<g clip-path="url(#card)">
 <rect width="{W}" height="{H}" fill="{t['bg']}"/>
 <g opacity="{t['orb']}" filter="url(#blur)">
  <circle cx="980" cy="90" r="170" fill="{t['accent']}"><animate attributeName="cx" values="980;880;980" dur="14s" repeatCount="indefinite"/><animate attributeName="cy" values="90;170;90" dur="11s" repeatCount="indefinite"/></circle>
  <circle cx="260" cy="420" r="150" fill="{t['purple']}"><animate attributeName="cx" values="260;400;260" dur="16s" repeatCount="indefinite"/></circle>
  <circle cx="700" cy="380" r="120" fill="{t['teal']}"><animate attributeName="cy" values="380;300;380" dur="12s" repeatCount="indefinite"/></circle>
 </g>
 <rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="24" fill="none" stroke="{t['border']}"/>

<g font-family="{SANS}">
 <circle cx="70" cy="74" r="5" fill="#22C55E"><animate attributeName="r" values="5;8;5" dur="2s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;.35;1" dur="2s" repeatCount="indefinite"/></circle>
 <text x="86" y="79" font-size="13" letter-spacing="3" fill="{t['muted']}">ONLINE · SÃO PAULO, BRASIL</text>
 <text x="64" y="140" font-size="24" fill="{t['muted']}">Olá, eu sou</text>
 <text x="60" y="222" font-size="76" font-weight="800" fill="{t['text']}" letter-spacing="-1.5">Jefferson <tspan fill="url(#name)">Silva</tspan></text>
</g>
<text x="64" y="{y_role}" font-family="{MONO}" font-size="{size}" fill="{t['accent2']}">{e(prefix)}</text>
{roles_svg}
<rect y="{y_role - 22}" width="3" height="28" fill="{t['accent2']}"><animate attributeName="x" values="{cv}" keyTimes="{ck}" dur="{dur}s" repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>
{chips}

<g>
 <animateTransform attributeName="transform" type="translate" values="0 0;0 -10;0 0" dur="6s" repeatCount="indefinite"/>
 <rect x="752" y="76" width="390" height="262" rx="14" fill="{t['surface']}" stroke="{t['border']}"/>
 <rect x="752" y="76" width="390" height="38" rx="14" fill="{t['surface2']}"/><rect x="752" y="100" width="390" height="14" fill="{t['surface2']}"/>
 <circle cx="776" cy="95" r="5" fill="#EF6C75"/><circle cx="794" cy="95" r="5" fill="#E8BE62"/><circle cx="812" cy="95" r="5" fill="#63C997"/>
 <text x="947" y="100" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t['muted']}">jeff.config.ts</text>
 {code_svg}
</g>
<g>
 <animateTransform attributeName="transform" type="translate" values="0 0;0 8;0 0" dur="5s" repeatCount="indefinite"/>
 <rect x="968" y="312" width="186" height="40" rx="20" fill="{t['surface']}" stroke="#22C55E" stroke-opacity=".6"/>
 <circle cx="990" cy="332" r="9" fill="#22C55E" opacity=".18"/><text x="990" y="337" text-anchor="middle" font-family="{SANS}" font-size="13" font-weight="700" fill="#22C55E">✓</text>
 <text x="1008" y="337" font-family="{MONO}" font-size="13" fill="{t['text']}">build passing</text>
</g>
<g>
 <animateTransform attributeName="transform" type="translate" values="0 0;0 -7;0 0" dur="7s" repeatCount="indefinite"/>
 <rect x="1040" y="44" width="134" height="36" rx="18" fill="{t['surface']}" stroke="{t['accent']}" stroke-opacity=".7"/>
 <text x="1107" y="67" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{t['accent2']}">deploy → prod</text>
</g>
<rect x="64" y="396" width="1072" height="3" rx="1.5" fill="url(#spread)"><animate attributeName="opacity" values=".35;1;.35" dur="3s" repeatCount="indefinite"/></rect>'''
    return svg(W, H, body, "Jefferson Silva — Desenvolvedor Full Stack. Eu construo apps mobile, PWAs, APIs e integrações com IA.")

# ───────────────────────────── TERMINAL ─────────────────────────────

def terminal(t):
    W = 1200
    line_h = 34
    top = 92
    H = top + len(TERMINAL) * line_h + 50
    size = 18
    cw = size * 0.6
    # linha do tempo (segundos)
    tl, now = [], 0.6
    for kind, txt in TERMINAL:
        if kind == "cmd":
            d = max(0.5, len(txt) * 0.06)
            tl.append((now, now + d)); now += d + 0.35
        else:
            tl.append((now, now)); now += 0.25
    total = now + 4.0
    defs, body = "<defs>", ""
    colors = {"out": t["muted"], "ok": "#22C55E", "hi": t["accent2"]}
    for i, ((kind, txt), (s, f)) in enumerate(zip(TERMINAL, tl)):
        y = top + i * line_h
        a, b = s / total, f / total
        end = (total - 0.6) / total
        if kind == "cmd":
            w = len(txt) * cw + 4
            defs += (f'<clipPath id="c{i}"><rect x="96" y="{y - 22}" width="0" height="32">'
                     f'<animate attributeName="width" values="0;0;{w:.0f};{w:.0f};0" keyTimes="0;{a:.4f};{b:.4f};{end:.4f};1" '
                     f'dur="{total:.1f}s" repeatCount="indefinite"/></rect></clipPath>')
            ov, ok = anim_vals([(0, 0), (a, 0), (a + 0.002, 1), (end, 1), (end + 0.01, 0), (1, 0)])
            body += (f'<text x="64" y="{y}" font-family="{MONO}" font-size="{size}" fill="{t["accent2"]}" opacity="0">'
                     f'<animate attributeName="opacity" values="{ov}" keyTimes="{ok}" dur="{total:.1f}s" repeatCount="indefinite"/>❯</text>')
            body += (f'<text x="96" y="{y}" font-family="{MONO}" font-size="{size}" fill="{t["text"]}" '
                     f'clip-path="url(#c{i})">{e(txt)}</text>')
        else:
            ov, ok = anim_vals([(0, 0), (a, 0), (a + 0.01, 1), (end, 1), (end + 0.01, 0), (1, 0)])
            pre = "✓ " if kind == "ok" else "  "
            body += (f'<text x="96" y="{y}" font-family="{MONO}" font-size="{size}" fill="{colors[kind]}" opacity="0">'
                     f'<animate attributeName="opacity" values="{ov}" keyTimes="{ok}" dur="{total:.1f}s" repeatCount="indefinite"/>{e(pre + txt)}</text>')
    defs += "</defs>"
    cursor_y = top + len(TERMINAL) * line_h
    fa = now / total
    fv, fk = anim_vals([(0, 0), (fa, 0), (fa + 0.01, 1), ((total - 0.6) / total, 1), ((total - 0.6) / total + 0.01, 0), (1, 0)])
    frame = f'''{defs}
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="{t['surface']}" stroke="{t['border']}"/>
<path d="M1 46V18A17 17 0 0 1 18 1H1182A17 17 0 0 1 1199 18V46Z" fill="{t['surface2']}"/>
<line x1="0" y1="46" x2="{W}" y2="46" stroke="{t['border']}"/>
<circle cx="30" cy="24" r="6" fill="#EF6C75"/><circle cx="52" cy="24" r="6" fill="#E8BE62"/><circle cx="74" cy="24" r="6" fill="#63C997"/>
<text x="{W/2}" y="29" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{t['muted']}">jeff@github: ~/perfil — zsh</text>
{body}
<g opacity="0"><animate attributeName="opacity" values="{fv}" keyTimes="{fk}" dur="{total:.1f}s" repeatCount="indefinite"/>
<text x="64" y="{cursor_y}" font-family="{MONO}" font-size="{size}" fill="{t['accent2']}">❯</text>
<rect x="96" y="{cursor_y - 16}" width="11" height="20" fill="{t['accent2']}"><animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect></g>'''
    return svg(W, H, frame, "Terminal: Jefferson Silva, Desenvolvedor Full Stack. Técnico em Desenvolvimento de Sistemas, cursando ADS. Foco em IA aplicada, Cloud e Mobile.")

# ───────────────────────────── CARDS ─────────────────────────────

def card(t, p, idx, theme):
    W, H = 600, 290
    ac = p[theme]
    per = 2 * (W - 2 + H - 2)
    tags, tx = "", 36
    for tag in p["tags"]:
        s, w = pill(tx, 206, tag, t, h=30, size=13, fill=ac + "1F", stroke=ac + "66")
        tags += s
        tx += w + 8
    desc = "".join(f'<text x="36" y="{148 + i * 26}" font-family="{SANS}" font-size="17" fill="{t["muted"]}">{e(l)}</text>'
                   for i, l in enumerate(p["desc"]))
    gsize = 22 if len(p["glyph"]) < 3 else 17
    body = f'''<defs><radialGradient id="g" cx="88%" cy="12%" r="70%"><stop stop-color="{ac}" stop-opacity=".28"/><stop offset="1" stop-color="{ac}" stop-opacity="0"/></radialGradient></defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="url(#g)"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="none" stroke="{ac}" stroke-width="2.5" stroke-linecap="round" stroke-dasharray="140 {per - 140}">
 <animate attributeName="stroke-dashoffset" values="0;-{per}" dur="7s" repeatCount="indefinite"/></rect>
<text x="36" y="54" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{ac}">{idx:02d} · {e(p['cat'])}</text>
<text x="34" y="104" font-family="{SANS}" font-size="36" font-weight="800" letter-spacing="-.5" fill="{t['text']}">{e(p['nome'])}</text>
{desc}
{tags}
<g transform="translate(528 66)">
 <circle r="40" fill="none" stroke="{ac}" stroke-opacity=".45" stroke-dasharray="4 7"><animateTransform attributeName="transform" type="rotate" values="0;360" dur="18s" repeatCount="indefinite"/></circle>
 <circle r="28" fill="{ac}" fill-opacity=".14" stroke="{ac}" stroke-opacity=".5"/>
 <g><animateTransform attributeName="transform" type="rotate" values="0;360" dur="5s" repeatCount="indefinite"/><circle cx="40" r="4.5" fill="{ac}"/></g>
 <text y="{gsize * 0.36:.1f}" text-anchor="middle" font-family="{MONO}" font-size="{gsize}" font-weight="700" fill="{ac}">{e(p['glyph'])}</text>
</g>
<line x1="36" y1="252" x2="{W - 36}" y2="252" stroke="{t['border']}" stroke-dasharray="2 6"/>
<text x="36" y="276" font-family="{MONO}" font-size="12" fill="{t['muted']}">github.com/jeffsilva03</text>
<text x="{W - 36}" y="276" text-anchor="end" font-family="{SANS}" font-size="14" font-weight="600" fill="{ac}">ver repositório
 <tspan font-size="16">↗<animate attributeName="dy" values="0;-3;0" dur="1.6s" repeatCount="indefinite"/></tspan></text>'''
    return svg(W, H, body, f"{p['nome']} — {' '.join(p['desc'])} Stack: {', '.join(p['tags'])}.")

# ───────────────────────────── CARD DE STACK ─────────────────────────────

ICON_CACHE = ROOT / ".icon-cache"


def icon_svg(slug, theme, x, y, size, pfx):
    """Baixa (uma vez) o ícone do skillicons.dev e devolve como <svg> aninhado, com ids prefixados."""
    import re, urllib.request
    ICON_CACHE.mkdir(exist_ok=True)
    f = ICON_CACHE / f"{slug}-{theme}.svg"
    if not f.exists():
        req = urllib.request.Request(f"https://skillicons.dev/icons?i={slug}&theme={theme}",
                                     headers={"User-Agent": "Mozilla/5.0"})
        f.write_bytes(urllib.request.urlopen(req, timeout=20).read())
    raw = f.read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^>]*\?>", "", raw).strip()
    raw = re.sub(r'\bid="([^"]+)"', rf'id="{pfx}\1"', raw)
    raw = re.sub(r"url\(#([^)]+)\)", rf"url(#{pfx}\1)", raw)
    raw = re.sub(r'href="#([^"]+)"', rf'href="#{pfx}\1"', raw)
    m = re.match(r"<svg\b([^>]*)>", raw)
    attrs = re.sub(r'\s(width|height|x|y)="[^"]*"', "", m.group(1))
    return f'<svg x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}"{attrs}>' + raw[m.end():]


def stack_card(t, theme):
    W, PAD, GAP, SLOT, ICON = 1200, 24, 16, 100, 54
    PH = 176  # altura do painel
    inner = W - 2 * PAD
    out, y, k = "", PAD + 8, 0
    for row in STACK:
        base = [len(items) * SLOT + 40 for _, items in row]
        extra = (inner - sum(base) - GAP * (len(row) - 1)) / len(row)
        x = PAD
        for (title, items), bw in zip(row, base):
            pw = bw + extra
            out += (f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="{PH}" rx="16" fill="{t["surface2"]}" stroke="{t["border"]}"/>'
                    f'<circle cx="{x + 22:.1f}" cy="{y + 28}" r="4" fill="{t["accent2"]}"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" begin="{k * 0.2:.1f}s" repeatCount="indefinite"/></circle>'
                    f'<text x="{x + 34:.1f}" y="{y + 33}" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{t["accent2"]}">{e(title)}</text>'
                    f'<text x="{x + pw - 20:.1f}" y="{y + 33}" text-anchor="end" font-family="{MONO}" font-size="12" fill="{t["muted"]}">{len(items):02d}</text>')
            ix = x + (pw - len(items) * SLOT) / 2
            for slug, label in items:
                cx = ix + SLOT / 2
                d = 0.15 + k * 0.07
                ic = icon_svg(slug, theme, cx - ICON / 2, y + 58, ICON, f"i{k}_")
                out += (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{d:.2f}s" dur=".5s" fill="freeze"/>'
                        f'<animateTransform attributeName="transform" type="translate" from="0 14" to="0 0" begin="{d:.2f}s" dur=".5s" fill="freeze"/>'
                        f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 -4;0 0" dur="3.2s" begin="{d + 0.6 + (k % 5) * 0.3:.2f}s" repeatCount="indefinite"/>{ic}</g>'
                        f'<text x="{cx:.1f}" y="{y + 142}" text-anchor="middle" font-family="{SANS}" font-size="13" fill="{t["text"]}">{e(label)}</text></g>')
                ix += SLOT
                k += 1
            x += pw + GAP
        y += PH + GAP
    H = y - GAP + PAD + 8
    total = sum(len(i) for row in STACK for _, i in row)
    body = (f'<defs><linearGradient id="top" x1="0" x2="1"><stop stop-color="{t["accent"]}"/><stop offset=".5" stop-color="{t["purple"]}"/><stop offset="1" stop-color="{t["teal"]}"/></linearGradient></defs>'
            f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="{t["surface"]}" stroke="{t["border"]}"/>'
            f'<rect x="40" y="0" width="{W - 80}" height="3" rx="1.5" fill="url(#top)"><animate attributeName="opacity" values=".4;1;.4" dur="3s" repeatCount="indefinite"/></rect>'
            + out)
    names = ", ".join(l for row in STACK for _, items in row for _, l in items)
    return svg(W, H, body, f"Stack ({total} tecnologias): {names}")

# ───────────────────────────── RODAPÉ (estilo do portfólio) ─────────────────────────────

# Paleta e fontes do portfólio (portfolio/assets/css/enhance.css)
FOOT = {
    "dark": dict(bg="#111827", border="#FFFFFF17", text="#F3F1F8", text2="#C3BFD0", muted="#9591A6",
                 accent="#B46CFF", dot="#FFFFFF1F", glow=".35"),
    "light": dict(bg="#FFFFFF", border="#140C2817", text="#15111F", text2="#4A4558", muted="#6F6A80",
                  accent="#8A1FE0", dot="#1E0A3C21", glow=".18"),
}
BRAND, BRAND2, BRAND3 = "#9423EC", "#C77DFF", "#5B2BFF"
FOOT_CTA = ("Vamos criar algo", "memorável", " juntos.")
FOOT_BTN = "Começar um projeto"
FOOT_LINKS = ["Portfólio", "Projetos", "LinkedIn", "GitHub", "E-mail"]
FOOT_WORD = "JEFF SILVA"
FONT_CACHE = ROOT / ".font-cache"


def _get(url, binary=False):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"})
    data = urllib.request.urlopen(req, timeout=20).read()
    return data if binary else data.decode("utf-8")


def embedded_fonts(text_display, text_mono):
    """Baixa do Google Fonts só os caracteres usados e embute em base64 (SVG em <img> não carrega fontes externas)."""
    import base64, hashlib, re, urllib.parse
    FONT_CACHE.mkdir(exist_ok=True)
    reqs = [("Bricolage+Grotesque:opsz,wght@96,400;96,700;96,800", text_display),
            ("Geist+Mono:wght@400;500", text_mono)]
    css_all = ""
    for fam, txt in reqs:
        chars = "".join(sorted(set(txt + " ")))
        key = hashlib.md5((fam + chars).encode()).hexdigest()[:12]
        f = FONT_CACHE / f"{key}.css"
        if not f.exists():
            css = _get(f"https://fonts.googleapis.com/css2?family={fam}&text={urllib.parse.quote(chars)}")
            for url in set(re.findall(r"url\((https://[^)]+)\)", css)):
                b64 = base64.b64encode(_get(url, binary=True)).decode()
                css = css.replace(url, f"data:font/woff2;base64,{b64}")
            f.write_text(css, encoding="utf-8")
        css_all += f.read_text(encoding="utf-8")
    return css_all


def github_path():
    import re
    FONT_CACHE.mkdir(exist_ok=True)
    f = FONT_CACHE / "github.svg"
    if not f.exists():
        f.write_text(_get("https://cdn.jsdelivr.net/npm/simple-icons@13.0.0/icons/github.svg"), encoding="utf-8")
    return re.search(r'd="([^"]+)"', f.read_text(encoding="utf-8")).group(1)


def footer(t, theme):
    from datetime import date
    c = FOOT[theme]
    W, H = 1200, 610
    DISPLAY = "'Bricolage Grotesque',system-ui,sans-serif"
    GMONO = "'Geist Mono',ui-monospace,Consolas,monospace"
    left = f"© {date.today().year} Jefferson Silva. Todos os direitos reservados."
    mid, right = "São Paulo · BR", "devjeffsilva.com.br ↗"
    fonts = embedded_fonts("".join(FOOT_CTA) + FOOT_BTN + "".join(FOOT_LINKS) + FOOT_WORD + "in",
                           left + mid + right)

    links, lx = "", 64
    for name in FOOT_LINKS:
        links += f'<text x="{lx:.0f}" y="330" font-family="{DISPLAY}" font-size="18" fill="{c["text2"]}">{e(name)}</text>'
        lx += len(name) * 8.6 + 44

    icons = [
        f'<path d="{github_path()}" fill="{c["text2"]}" transform="translate(-10 -10) scale(.84)"/>',
        f'<text y="7" text-anchor="middle" font-family="{DISPLAY}" font-size="19" font-weight="800" fill="{c["text2"]}">in</text>',
        f'<g fill="none" stroke="{c["text2"]}" stroke-width="1.8" stroke-linejoin="round"><rect x="-10" y="-7" width="20" height="14" rx="2.5"/><path d="M-9 -5.5 0 1.5 9 -5.5"/></g>',
    ]
    social = ""
    for i, ic in enumerate(icons):
        social += (f'<g transform="translate({1004 + i * 56} 323)"><g>'
                   f'<animateTransform attributeName="transform" type="translate" values="0 0;0 -3;0 0" dur="3s" begin="{i * .4:.1f}s" repeatCount="indefinite"/>'
                   f'<circle r="22" fill="none" stroke="{c["border"]}" stroke-width="1.2"/>{ic}</g></g>')

    body = f'''<defs>
<style>{fonts}</style>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="{c['dot']}"/></pattern>
<radialGradient id="glowg"><stop stop-color="{BRAND}" stop-opacity="{c['glow']}"/><stop offset="1" stop-color="{BRAND}" stop-opacity="0"/></radialGradient>
<linearGradient id="em" x1="0" x2="1"><stop stop-color="{BRAND2}"/><stop offset=".6" stop-color="{BRAND}"/><stop offset="1" stop-color="{BRAND3}"/></linearGradient>
<linearGradient id="btn" x1="0" x2="1"><stop stop-color="{BRAND3}"/><stop offset=".45" stop-color="{BRAND}"/><stop offset="1" stop-color="{BRAND2}"/></linearGradient>
<linearGradient id="word" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{c['text']}"/><stop offset=".95" stop-color="{c['text']}" stop-opacity="0"/></linearGradient>
<linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" x2="420"><stop stop-color="{BRAND2}" stop-opacity="0"/><stop offset=".5" stop-color="{BRAND2}" stop-opacity=".9"/><stop offset="1" stop-color="{BRAND2}" stop-opacity="0"/>
 <animateTransform attributeName="gradientTransform" type="translate" values="-500 0;1300 0" dur="6s" repeatCount="indefinite"/></linearGradient>
<linearGradient id="fadev" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff"/><stop offset=".9" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="wm"><rect x="0" y="380" width="{W}" height="160" fill="url(#fadev)"/></mask>
<clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>
<clipPath id="bclip"><rect x="866" y="152" width="270" height="60" rx="30"/></clipPath>
<filter id="bglow" x="-30%" y="-80%" width="160%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>
<g clip-path="url(#card)">
 <rect width="{W}" height="{H}" fill="{c['bg']}"/>
 <rect width="{W}" height="{H}" fill="url(#dots)" opacity=".7"/>
 <circle cx="180" cy="120" r="260" fill="url(#glowg)"><animate attributeName="cx" values="180;320;180" dur="12s" repeatCount="indefinite"/></circle>
 <circle cx="1000" cy="560" r="220" fill="url(#glowg)"><animate attributeName="cy" values="560;470;560" dur="10s" repeatCount="indefinite"/></circle>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="28" fill="none" stroke="{c['border']}"/>

<text x="62" y="128" font-family="{DISPLAY}" font-size="66" font-weight="700" letter-spacing="-2.6" fill="{c['text']}">{e(FOOT_CTA[0])}</text>
<text x="62" y="204" font-family="{DISPLAY}" font-size="66" font-weight="700" letter-spacing="-2.6" fill="{c['text']}"><tspan font-style="italic" font-weight="400" fill="url(#em)">{e(FOOT_CTA[1])}</tspan><tspan dx="14">{e(FOOT_CTA[2].strip())}</tspan></text>

<rect x="886" y="172" width="230" height="40" rx="20" fill="{BRAND}" opacity=".55" filter="url(#bglow)"><animate attributeName="opacity" values=".35;.7;.35" dur="3s" repeatCount="indefinite"/></rect>
<rect x="866" y="152" width="270" height="60" rx="30" fill="{BRAND}"/>
<g clip-path="url(#bclip)"><rect x="866" y="152" width="270" height="60" fill="url(#btn)" opacity="0"><animate attributeName="opacity" values="0;1;0" dur="5s" repeatCount="indefinite"/></rect>
 <rect x="-60" y="140" width="40" height="90" fill="#fff" opacity=".22" transform="skewX(-20)"><animate attributeName="x" values="820;1250;1250" keyTimes="0;.35;1" dur="4.5s" repeatCount="indefinite"/></rect></g>
<rect x="866.5" y="152.5" width="269" height="59" rx="29.5" fill="none" stroke="#fff" stroke-opacity=".2"/>
<text x="900" y="189" font-family="{DISPLAY}" font-size="19" font-weight="700" fill="#fff">{e(FOOT_BTN)}</text>
<g fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><animateTransform attributeName="transform" type="translate" values="0 0;5 0;0 0" dur="1.6s" repeatCount="indefinite"/>
 <path d="M1092 182h20M1105 175l7 7-7 7"/></g>

<line x1="62" y1="272" x2="{W - 62}" y2="272" stroke="{c['border']}"/>
{links}
{social}
<line x1="62" y1="374" x2="{W - 62}" y2="374" stroke="{c['border']}"/>

<g opacity=".16"><text x="{W/2}" y="530" text-anchor="middle" font-family="{DISPLAY}" font-size="200" font-weight="800" textLength="1080" lengthAdjust="spacingAndGlyphs" fill="url(#word)">{e(FOOT_WORD)}</text></g>
<g mask="url(#wm)" opacity=".55"><text x="{W/2}" y="530" text-anchor="middle" font-family="{DISPLAY}" font-size="200" font-weight="800" textLength="1080" lengthAdjust="spacingAndGlyphs" fill="url(#shine)">{e(FOOT_WORD)}</text></g>

<g font-family="{GMONO}" font-size="13" fill="{c['muted']}">
 <text x="62" y="580">{e(left)}</text>
 <circle cx="{W/2 - 62}" cy="575.5" r="4" fill="#22C55E"><animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>
 <text x="{W/2 - 50}" y="580">{e(mid)}</text>
 <text x="{W - 62}" y="580" text-anchor="end" fill="{c['accent']}">{e(right)}</text>
</g>'''
    return svg(W, H, body, "Vamos criar algo memorável juntos. Começar um projeto: devjeffsilva.com.br")

# ───────────────────────────── CARDS DE TRILHA ("Quem é você?") ─────────────────────────────

TRILHAS = [
    dict(slug="recrutador", icon="briefcase-business", titulo="Tá contratando?", sub="O resumo de quem eu sou e o que olhar primeiro",
         dark="#5DB7FF", light="#136ED6"),
    dict(slug="cliente", icon="lightbulb", titulo="Tem um projeto?", sub="O que eu faço e como me chamar",
         dark="#C77DFF", light="#8A1FE0"),
    dict(slug="dev", icon="code-xml", titulo="É dev?", sub="Onde vale a pena fuçar no código",
         dark="#2DD4BF", light="#0D9488"),
    dict(slug="curioso", icon="gamepad-2", titulo="Só passeando?", sub="Tem um jogo escondido no meu portfólio",
         dark="#FBBF24", light="#B45309"),
]


def lucide(name):
    """Ícone do Lucide (licença ISC), baixado uma vez e guardado em .icon-cache/."""
    import re
    ICON_CACHE.mkdir(exist_ok=True)
    f = ICON_CACHE / f"lucide-{name}.svg"
    if not f.exists():
        f.write_text(_get(f"https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons/{name}.svg"), encoding="utf-8")
    raw = f.read_text(encoding="utf-8")
    return re.search(r"<svg[^>]*>(.*)</svg>", raw, re.S).group(1).strip()


def trail_card(t, tr, idx, theme):
    W, H = 1200, 104
    ac = tr[theme]
    per = 2 * (W - 2 + H - 2)
    body = f'''<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="{t['surface']}" stroke="{t['border']}" stroke-width="1.5"/>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="18" fill="none" stroke="{ac}" stroke-width="2" stroke-linecap="round" stroke-dasharray="120 {per - 120}" opacity=".9">
 <animate attributeName="stroke-dashoffset" values="0;-{per}" dur="9s" begin="{idx * -2.2:.1f}s" repeatCount="indefinite"/></rect>
<circle cx="62" cy="52" r="26" fill="{ac}" fill-opacity=".14"/>
<g transform="translate(48 38) scale(1.17)" fill="none" stroke="{ac}" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{lucide(tr['icon'])}</g>
<text x="108" y="49" font-family="{SANS}" font-size="25" font-weight="700" fill="{t['text']}">{e(tr['titulo'])}</text>
<text x="108" y="76" font-family="{SANS}" font-size="16" fill="{t['muted']}">{e(tr['sub'])}</text>
<g fill="none" stroke="{ac}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
 <animateTransform attributeName="transform" type="translate" values="0 -2;0 3;0 -2" dur="1.6s" begin="{idx * .25:.2f}s" repeatCount="indefinite"/>
 <path d="M{W - 66} 47l9 9 9-9"/></g>'''
    return svg(W, H, body, f"{tr['titulo']} {tr['sub']}. Clique para abrir.")

# ───────────────────────────── PREVIEW LOCAL ─────────────────────────────

PREVIEW = r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Preview do README</title>
<link id="css-light" rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown-light.min.css">
<link id="css-dark" rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown-dark.min.css" disabled>
<style>
 body{margin:0;background:#fff;transition:background .2s}
 body.dark{background:#0d1117}
 .wrap{max-width:1012px;margin:0 auto;padding:32px 16px}
 .markdown-body{border:1px solid #d0d7de;border-radius:8px;padding:32px}
 body.dark .markdown-body{border-color:#30363d}
 .bar{position:sticky;top:0;z-index:2;display:flex;gap:8px;justify-content:center;padding:10px;background:inherit;font:14px system-ui}
 .bar button{padding:6px 14px;border-radius:999px;border:1px solid #8885;background:transparent;color:inherit;cursor:pointer}
 body.dark .bar{color:#e6edf3}
</style></head>
<body><div class="bar"><span>Preview aproximado do GitHub ·</span><button id="t">Alternar tema claro/escuro</button></div>
<div class="wrap"><article class="markdown-body" id="md"></article></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.2/marked.min.js"></script>
<script>
const README = __README__;
document.getElementById('md').innerHTML = marked.parse(README);
document.querySelectorAll('code.language-mermaid').forEach(c => {
  const d = document.createElement('div'); d.className = 'mermaid'; d.textContent = c.textContent;
  c.parentElement.replaceWith(d);
});
const mm = document.createElement('script');
mm.src = 'https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js';
mm.onload = () => { mermaid.initialize({ startOnLoad: false, theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default' }); mermaid.run(); };
document.head.appendChild(mm);
let dark = matchMedia('(prefers-color-scheme: dark)').matches;
function apply(){
  document.body.classList.toggle('dark', dark);
  document.getElementById('css-dark').disabled = !dark;
  document.getElementById('css-light').disabled = dark;
  document.querySelectorAll('picture').forEach(p => {
    const s = p.querySelector('source[media*="dark"]'), img = p.querySelector('img');
    if (!img.dataset.light) img.dataset.light = img.getAttribute('src');
    p.querySelectorAll('source').forEach(x => x.media = 'not all');
    img.src = dark && s ? s.getAttribute('srcset') : img.dataset.light;
  });
}
document.getElementById('t').onclick = () => { dark = !dark; apply(); };
apply();
</script></body></html>
'''

# ───────────────────────────── main ─────────────────────────────

def main():
    ASSETS.mkdir(exist_ok=True)
    for old in ASSETS.glob("*.svg"):  # remove assets antigos (ex.: cards de projetos retirados)
        old.unlink()
    count = 0
    for theme, t in THEMES.items():
        files = {
            f"hero-{theme}.svg": hero(t),
            f"terminal-{theme}.svg": terminal(t),
            f"stack-{theme}.svg": stack_card(t, theme),
            f"footer-{theme}.svg": footer(t, theme),
        }
        for i, p in enumerate(PROJETOS, 1):
            files[f"card-{p['slug']}-{theme}.svg"] = card(t, p, i, theme)
        for i, tr in enumerate(TRILHAS, 1):
            files[f"trilha-{tr['slug']}-{theme}.svg"] = trail_card(t, tr, i, theme)
        for name, content in files.items():
            (ASSETS / name).write_text(content, encoding="utf-8")
            count += 1
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    (ROOT / "preview.html").write_text(PREVIEW.replace("__README__", json.dumps(readme)), encoding="utf-8")
    print(f"{count} SVGs gerados em {ASSETS} + preview.html")


if __name__ == "__main__":
    main()
