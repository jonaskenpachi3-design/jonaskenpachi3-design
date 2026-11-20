#!/usr/bin/env python3
"""Gera um cartão SVG de contribuições mensal com visual consistente ao perfil."""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

LOGIN = "jonaskenpachi3-design"
TOKEN = (os.environ.get("GH_TOKEN") or "").strip()
if not TOKEN:
    raise SystemExit("Configure o secret GH_TOKEN com um token GitHub de leitura.")

today = dt.datetime.now(dt.timezone.utc).date()
month_start = today.replace(day=1)
query = """
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
body = json.dumps({"query": query, "variables": {
    "login": LOGIN,
    "from": month_start.isoformat() + "T00:00:00Z",
    "to": today.isoformat() + "T23:59:59Z"
}}).encode()
req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json",
    "User-Agent": "github-profile-readme"
})
with urllib.request.urlopen(req, timeout=30) as response:
    payload = json.load(response)
if payload.get("errors"):
    raise SystemExit(json.dumps(payload["errors"], ensure_ascii=False))
user = payload.get("data", {}).get("user")
if not user:
    raise SystemExit("Usuário não encontrado ou token sem permissão de leitura.")
calendar = user["contributionsCollection"]["contributionCalendar"]
days = [d for week in calendar["weeks"] for d in week["contributionDays"]]
days = [d for d in days if month_start.isoformat() <= d["date"] <= today.isoformat()]
counts = [int(d["contributionCount"]) for d in days]
active_days = sum(c > 0 for c in counts)
weekday_totals = [0] * 7
by_date = {}
for day in days:
    count = int(day["contributionCount"])
    weekday_totals[int(day["weekday"])] += count
    by_date[day["date"]] = count
weekday_names = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"]
best_day = weekday_names[max(range(7), key=lambda i: weekday_totals[i])] if any(weekday_totals) else "—"

# Sequência corrente: se hoje ainda não houve atividade, considera o dia anterior.
cursor = today if by_date.get(today.isoformat(), 0) else today - dt.timedelta(days=1)
streak = 0
while cursor >= month_start and by_date.get(cursor.isoformat(), 0) > 0:
    streak += 1
    cursor -= dt.timedelta(days=1)

# Faixa horizontal com um bloco por dia do mês.
first_offset = (month_start.weekday() + 1) % 7
palette = ["#172536", "#164e63", "#0e7490", "#0891b2", "#67e8f9"]
cells = []
for day in days:
    date = dt.date.fromisoformat(day["date"])
    col, row = date.day - 1, 0
    count = int(day["contributionCount"])
    level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 5 else 3 if count <= 9 else 4
    x, y = 44 + col * 36, 153
    cells.append(
        f'<rect x="{x}" y="{y}" width="22" height="22" rx="4" fill="{palette[level]}">'
        f'<title>{date.isoformat()}: {count} contribuições</title></rect>'
    )
grid = "".join(cells)
month_label = today.strftime("%m / %Y")
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260" role="img" aria-labelledby="t d">
<title id="t">Atividade no GitHub — {month_label}</title>
<desc id="d">{calendar['totalContributions']} contribuições no mês, {active_days} dias ativos e sequência corrente de {streak} dias.</desc>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#101b29"/><stop offset="1" stop-color="#0b1420"/></linearGradient></defs>
<style>@media(prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect x="3" y="3" width="1194" height="254" rx="16" fill="url(#bg)" stroke="#29384b"/>
<text x="34" y="43" fill="#e2e8f0" font-family="Arial,sans-serif" font-size="17" font-weight="700" letter-spacing="2">ATIVIDADE NO GITHUB</text>
<text x="1166" y="42" text-anchor="end" fill="#8193a8" font-family="Arial,sans-serif" font-size="12">{month_label}</text>
<path d="M34 58H1166" stroke="#29384b"/>
<text x="36" y="103" fill="#67e8f9" font-family="Arial,sans-serif" font-size="31" font-weight="700">{calendar['totalContributions']}</text>
<text x="36" y="124" fill="#8294aa" font-family="Arial,sans-serif" font-size="12">CONTRIBUIÇÕES</text>
<text x="270" y="103" fill="#f1f5f9" font-family="Arial,sans-serif" font-size="31" font-weight="700">{active_days}</text>
<text x="270" y="124" fill="#8294aa" font-family="Arial,sans-serif" font-size="12">DIAS ATIVOS</text>
<text x="490" y="103" fill="#f1f5f9" font-family="Arial,sans-serif" font-size="31" font-weight="700">{streak}</text>
<text x="490" y="124" fill="#8294aa" font-family="Arial,sans-serif" font-size="12">DIAS DE SEQUÊNCIA*</text>
<text x="760" y="103" fill="#f1f5f9" font-family="Arial,sans-serif" font-size="25" font-weight="700">{best_day}</text>
<text x="760" y="124" fill="#8294aa" font-family="Arial,sans-serif" font-size="12">DIA MAIS ATIVO</text>
{grid}
<text x="44" y="220" fill="#71839a" font-family="Arial,sans-serif" font-size="11">* Sequência contabilizada dentro do mês atual.</text>
<g transform="translate(900 207)"><text x="0" y="10" fill="#71839a" font-family="Arial,sans-serif" font-size="11">MENOS</text><rect x="52" y="0" width="13" height="13" rx="3" fill="#172536"/><rect x="72" y="0" width="13" height="13" rx="3" fill="#164e63"/><rect x="92" y="0" width="13" height="13" rx="3" fill="#0e7490"/><rect x="112" y="0" width="13" height="13" rx="3" fill="#0891b2"/><rect x="132" y="0" width="13" height="13" rx="3" fill="#67e8f9"/><text x="153" y="10" fill="#71839a" font-family="Arial,sans-serif" font-size="11">MAIS</text></g>
</svg>
"""
Path("assets/contributions.svg").write_text(svg, encoding="utf-8")
print("Calendário atualizado:", calendar["totalContributions"], "contribuições")
