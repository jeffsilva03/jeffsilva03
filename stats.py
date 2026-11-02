#!/usr/bin/env python3
"""
Gera o card de estatísticas do perfil (tema escuro e claro) direto da API GraphQL do GitHub.
Roda no GitHub Actions (workflow profile.yml) e publica no branch "output".

Uso local:  GITHUB_TOKEN=xxx python stats.py [pasta_saida]
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from gerar_assets import THEMES, SANS, MONO, svg, e

LOGIN = os.environ.get("GITHUB_LOGIN", "jeffsilva03")
TOP_N = 6
# Linguagens que não entram no ranking (ex.: "HTML", "CSS"). Deixe vazio para contar todas.
IGNORAR = {"HTML", "CSS", "SCSS", "JavaScript", "Jupyter Notebook"}

QUERY = """
query($login: String!) {
  user(login: $login) {
    publicRepos: repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
    repos: repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) {
      nodes { stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": LOGIN},
    )
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    if "errors" in data:
        raise SystemExit(f"Erro da API: {data['errors']}")
    return data["data"]["user"]


def resumir(u):
    days = [d for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    hoje = datetime.now(timezone.utc).date().isoformat()
    days = [d for d in days if d["date"] <= hoje]

    # sequência atual: se hoje ainda não teve contribuição, conta a partir de ontem
    atual, i = 0, len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0:
        i -= 1
    while i >= 0 and days[i]["contributionCount"] > 0:
        atual += 1
        i -= 1
    maior = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        maior = max(maior, run)

    langs = {}
    for r in u["repos"]["nodes"]:
        for ed in r["languages"]["edges"]:
            n = ed["node"]["name"]
            if n in IGNORAR:
                continue
            c = langs.setdefault(n, {"size": 0, "color": ed["node"]["color"] or "#8B949E"})
            c["size"] += ed["size"]
    total = sum(v["size"] for v in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1]["size"])[:TOP_N]
    top = [(n, v["color"], v["size"] / total * 100) for n, v in top]

    return dict(
        contrib=u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        commits=u["contributionsCollection"]["totalCommitContributions"],
        ativos=sum(1 for d in days if d["contributionCount"] > 0),
        atual=atual, maior=maior,
        repos=u["publicRepos"]["totalCount"],
        nlangs=len(langs),
        top=top,
    )


def fmt(n):
    return f"{n:,}".replace(",", ".")


def card(t, s):
    W, H = 1200, 392
    tiles = [
        ("CONTRIBUIÇÕES", fmt(s["contrib"]), "nos últimos 12 meses"),
        ("COMMITS", fmt(s["commits"]), "nos últimos 12 meses"),
        ("DIAS ATIVOS", fmt(s["ativos"]), "com contribuição no ano"),
        ("SEQUÊNCIA ATUAL", f"{s['atual']} {'dia' if s['atual'] == 1 else 'dias'}", "seguidos contribuindo"),
        ("MAIOR SEQUÊNCIA", f"{s['maior']} {'dia' if s['maior'] == 1 else 'dias'}", "nos últimos 12 meses"),
        ("REPOSITÓRIOS", fmt(s["repos"]), f"públicos · {s['nlangs']} linguagens"),
    ]
    out = ""
    tw, th, gx, gy, x0, y0 = 212, 140, 14, 14, 32, 72
    for i, (lab, val, sub) in enumerate(tiles):
        cx, cy = x0 + (i % 3) * (tw + gx), y0 + (i // 3) * (th + gy)
        d = 0.1 + i * 0.08
        hl = t["accent2"] if lab == "SEQUÊNCIA ATUAL" else t["text"]
        out += (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{d:.2f}s" dur=".5s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" from="0 10" to="0 0" begin="{d:.2f}s" dur=".5s" fill="freeze"/>'
                f'<rect x="{cx}" y="{cy}" width="{tw}" height="{th}" rx="14" fill="{t["surface2"]}" stroke="{t["border"]}"/>'
                f'<text x="{cx + 20}" y="{cy + 34}" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="{t["muted"]}">{e(lab)}</text>'
                f'<text x="{cx + 18}" y="{cy + 86}" font-family="{SANS}" font-size="40" font-weight="800" letter-spacing="-1" fill="{hl}">{e(val)}</text>'
                f'<text x="{cx + 20}" y="{cy + 116}" font-family="{SANS}" font-size="13" fill="{t["muted"]}">{e(sub)}</text></g>')
        if lab == "SEQUÊNCIA ATUAL" and s["atual"] > 0:
            out += (f'<circle cx="{cx + tw - 24}" cy="{cy + 30}" r="5" fill="#22C55E">'
                    f'<animate attributeName="opacity" values="1;.3;1" dur="2s" repeatCount="indefinite"/></circle>')

    # linguagens
    lx, lw = 724, 444
    out += (f'<rect x="{lx - 16}" y="{y0}" width="{lw + 28}" height="{2 * th + gy}" rx="14" fill="{t["surface2"]}" stroke="{t["border"]}"/>'
            f'<text x="{lx + 6}" y="{y0 + 34}" font-family="{MONO}" font-size="12" letter-spacing="1.5" fill="{t["muted"]}">LINGUAGENS MAIS USADAS</text>')
    bx, by, bw = lx + 6, y0 + 52, lw - 12
    acc = 0.0
    soma = sum(p for _, _, p in s["top"]) or 1
    for i, (n, c, p) in enumerate(s["top"]):
        w = bw * p / soma
        out += (f'<rect x="{bx + acc:.1f}" y="{by}" width="0" height="10" fill="{c}">'
                f'<animate attributeName="width" from="0" to="{max(w - 2, 1):.1f}" begin="{0.4 + i * .1:.1f}s" dur=".6s" fill="freeze"/></rect>')
        acc += w
    out += f'<rect x="{bx}" y="{by}" width="{bw}" height="10" rx="5" fill="none" stroke="{t["surface2"]}" stroke-width="3"/>'
    for i, (n, c, p) in enumerate(s["top"]):
        col, row = i % 2, i // 2
        tx, ty = bx + col * (bw / 2), by + 54 + row * 52
        d = 0.6 + i * 0.08
        out += (f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{d:.2f}s" dur=".4s" fill="freeze"/>'
                f'<circle cx="{tx + 6}" cy="{ty - 5}" r="6" fill="{c}"/>'
                f'<text x="{tx + 20}" y="{ty}" font-family="{SANS}" font-size="16" font-weight="600" fill="{t["text"]}">{e(n)}</text>'
                f'<text x="{tx + bw / 2 - 16}" y="{ty}" text-anchor="end" font-family="{MONO}" font-size="14" fill="{t["muted"]}">{p:.1f}%</text>'
                f'<rect x="{tx + 20}" y="{ty + 12}" width="{bw / 2 - 36}" height="4" rx="2" fill="{t["border"]}"/>'
                f'<rect x="{tx + 20}" y="{ty + 12}" width="0" height="4" rx="2" fill="{c}">'
                f'<animate attributeName="width" from="0" to="{(bw / 2 - 36) * p / max(s["top"][0][2], 1):.1f}" begin="{d:.2f}s" dur=".7s" fill="freeze"/></rect></g>')

    hoje = date.today().strftime("%d/%m/%Y")
    body = (f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="{t["surface"]}" stroke="{t["border"]}"/>'
            f'<text x="34" y="44" font-family="{SANS}" font-size="20" font-weight="700" fill="{t["text"]}">Atividade no GitHub</text>'
            f'<text x="{W - 34}" y="44" text-anchor="end" font-family="{MONO}" font-size="12" fill="{t["muted"]}">atualizado em {hoje}</text>'
            + out)
    label = (f"Atividade no GitHub: {s['contrib']} contribuições e {s['commits']} commits nos últimos 12 meses, "
             f"{s['ativos']} dias ativos, sequência atual de {s['atual']} dias, maior sequência de {s['maior']} dias, "
             f"{s['repos']} repositórios públicos. Linguagens: " + ", ".join(f"{n} {p:.1f}%" for n, _, p in s["top"]))
    return svg(W, H, body, label)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Defina GITHUB_TOKEN.")
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    out.mkdir(parents=True, exist_ok=True)
    s = resumir(fetch(token))
    for theme, t in THEMES.items():
        (out / f"stats-{theme}.svg").write_text(card(t, s), encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k != "top"}, ensure_ascii=False),
          [f"{n} {p:.1f}%" for n, _, p in s["top"]])


if __name__ == "__main__":
    main()
