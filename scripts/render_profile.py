#!/usr/bin/env python3
"""Gera o cartão SVG animado de contribuições mensal, no mesmo visual do perfil."""
import calendar as pycal
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

LOGIN = "jonaskenpachi3-design"
OUTPUT = Path("assets/contributions.svg")
PALETTE = ["#263943", "#315c59", "#397f78", "#4bb29e", "#6ee7c8"]
WEEKDAYS = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"]

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""

CSS = """
.f{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif}
.fb{transform-box:fill-box}
@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes pop{0%{opacity:0;transform:scale(.2)}70%{transform:scale(1.15)}100%{opacity:1;transform:scale(1)}}
@keyframes now{0%{opacity:.9;transform:scale(1)}100%{opacity:0;transform:scale(1.9)}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes sweep{0%{transform:translateX(0) skewX(-18deg)}40%,100%{transform:translateX(1500px) skewX(-18deg)}}
.up{animation:up .8s cubic-bezier(.2,.7,.2,1) both}
.fade{animation:fade 1s ease both}
.cell{transform-origin:center;animation:pop .55s cubic-bezier(.2,.7,.2,1) both}
.now{transform-origin:center;animation:now 2.2s ease-out 1.6s infinite}
.rule{transform-origin:0 50%;animation:grow 1.1s cubic-bezier(.2,.7,.2,1) .1s both}
.sheen{animation:sweep 10s ease-in-out 3s infinite}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def fetch_calendar(token, today):
    month_start = today.replace(day=1)
    body = json.dumps({"query": QUERY, "variables": {
        "login": LOGIN,
        "from": month_start.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z",
    }}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "User-Agent": "github-profile-readme",
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise SystemExit(json.dumps(payload["errors"], ensure_ascii=False))
    user = payload.get("data", {}).get("user")
    if not user:
        raise SystemExit("Usuário não encontrado ou token sem permissão de leitura.")
    return user["contributionsCollection"]["contributionCalendar"]


def build_svg(calendar, today):
    month_start = today.replace(day=1)
    days_in_month = pycal.monthrange(today.year, today.month)[1]
    days = [d for week in calendar["weeks"] for d in week["contributionDays"]]
    days = [d for d in days if month_start.isoformat() <= d["date"] <= today.isoformat()]
    active_days = sum(int(d["contributionCount"]) > 0 for d in days)
    weekday_totals = [0] * 7
    by_date = {}
    for day in days:
        count = int(day["contributionCount"])
        weekday_totals[int(day["weekday"])] += count
        by_date[day["date"]] = count
    best_day = WEEKDAYS[max(range(7), key=lambda i: weekday_totals[i])] if any(weekday_totals) else "—"

    # Sequência corrente: se hoje ainda não houve atividade, considera o dia anterior.
    cursor = today if by_date.get(today.isoformat(), 0) else today - dt.timedelta(days=1)
    streak = 0
    while cursor >= month_start and by_date.get(cursor.isoformat(), 0) > 0:
        streak += 1
        cursor -= dt.timedelta(days=1)

    # Faixa horizontal com um bloco por dia do mês (dias futuros aparecem apagados).
    cells = []
    for index in range(days_in_month):
        date = month_start + dt.timedelta(days=index)
        x, y = 44 + index * 36, 153
        if date > today:
            cells.append(
                f'<rect x="{x}" y="{y}" width="22" height="22" rx="4" fill="none" '
                f'stroke="#2c434c" stroke-dasharray="3 3" opacity=".7">'
                f'<title>{date.isoformat()}</title></rect>'
            )
            continue
        count = by_date.get(date.isoformat(), 0)
        level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 5 else 3 if count <= 9 else 4
        delay = 0.5 + index * 0.035
        cells.append(
            f'<rect class="cell fb" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" '
            f'width="22" height="22" rx="4" fill="{PALETTE[level]}">'
            f'<title>{date.isoformat()}: {count} contribuições</title></rect>'
        )
        if date == today:
            cells.append(
                f'<rect class="now fb" x="{x}" y="{y}" width="22" height="22" rx="4" '
                f'fill="none" stroke="#6ee7c8" stroke-width="1.5"/>'
            )
    grid = "".join(cells)
    month_label = today.strftime("%m / %Y")
    total = calendar["totalContributions"]
    legend = "".join(
        f'<rect x="{52 + i * 20}" y="0" width="13" height="13" rx="3" fill="{color}"/>'
        for i, color in enumerate(PALETTE)
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260" role="img" aria-labelledby="t d">
<title id="t">Atividade no GitHub — {month_label}</title>
<desc id="d">{total} contribuições no mês, {active_days} dias ativos e sequência corrente de {streak} dias.</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#14232c"/><stop offset="1" stop-color="#112029"/></linearGradient>
<linearGradient id="line" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#6ee7c8"/><stop offset="1" stop-color="#67b9d0"/></linearGradient>
<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="card"><rect x="3" y="3" width="1194" height="254" rx="16"/></clipPath>
</defs>
<style>{CSS}</style>
<rect x="3" y="3" width="1194" height="254" rx="16" fill="url(#bg)"/>
<g clip-path="url(#card)"><rect class="sheen" x="-240" y="0" width="200" height="260" fill="url(#sheen)"/></g>
<rect x="3" y="3" width="1194" height="254" rx="16" fill="none" stroke="#344d56" stroke-width="1.5"/>
<g class="f">
<text class="fade" x="34" y="43" fill="#e7f0ed" font-size="17" font-weight="700" letter-spacing="2">ATIVIDADE NO GITHUB</text>
<text class="fade" x="1166" y="42" text-anchor="end" fill="#83a2a5" font-size="12">{month_label}</text>
<rect class="rule fb" x="34" y="57.5" width="1132" height="1" fill="#344d56"/>
<g class="up" style="animation-delay:.3s"><text x="36" y="103" fill="#6ee7c8" font-size="31" font-weight="700">{total}</text><text x="36" y="124" fill="#83a2a5" font-size="12" letter-spacing=".6">CONTRIBUIÇÕES</text></g>
<g class="up" style="animation-delay:.4s"><text x="270" y="103" fill="#e7f0ed" font-size="31" font-weight="700">{active_days}</text><text x="270" y="124" fill="#83a2a5" font-size="12" letter-spacing=".6">DIAS ATIVOS</text></g>
<g class="up" style="animation-delay:.5s"><text x="490" y="103" fill="#e7f0ed" font-size="31" font-weight="700">{streak}</text><text x="490" y="124" fill="#83a2a5" font-size="12" letter-spacing=".6">DIAS DE SEQUÊNCIA*</text></g>
<g class="up" style="animation-delay:.6s"><text x="760" y="103" fill="#e7f0ed" font-size="25" font-weight="700">{best_day}</text><text x="760" y="124" fill="#83a2a5" font-size="12" letter-spacing=".6">DIA MAIS ATIVO</text></g>
{grid}
<text class="fade" style="animation-delay:1.2s" x="44" y="220" fill="#83a2a5" font-size="11">* Sequência contabilizada dentro do mês atual.</text>
<g class="fade" style="animation-delay:1.2s" transform="translate(900 207)"><text x="0" y="10" fill="#83a2a5" font-size="11">MENOS</text>{legend}<text x="153" y="10" fill="#83a2a5" font-size="11">MAIS</text></g>
</g>
</svg>
"""


def main():
    token = (os.environ.get("GH_TOKEN") or "").strip()
    if not token:
        raise SystemExit("Configure o secret GH_TOKEN com um token GitHub de leitura.")
    today = dt.datetime.now(dt.timezone.utc).date()
    calendar = fetch_calendar(token, today)
    OUTPUT.write_text(build_svg(calendar, today), encoding="utf-8")
    print("Calendário atualizado:", calendar["totalContributions"], "contribuições")


if __name__ == "__main__":
    main()
