#!/usr/bin/env python3
"""Atualiza o SVG com o calendário de contribuições do mês corrente."""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

LOGIN = "jonaskenpachi3-design"
TOKEN = os.environ.get("GH_TOKEN")
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
calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [d for week in calendar["weeks"] for d in week["contributionDays"]]
days = [d for d in days if month_start.isoformat() <= d["date"] <= today.isoformat()]
counts = [int(d["contributionCount"]) for d in days]
active_days = sum(c > 0 for c in counts)
peak = max(counts, default=0)
weekday_totals = [0] * 7
for day in days:
    weekday_totals[int(day["weekday"])] += int(day["contributionCount"])
weekday_names = ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"]
best_day = weekday_names[max(range(7), key=lambda i: weekday_totals[i])] if days else "—"
streak = 0
for day in reversed(days):
    if int(day["contributionCount"]) > 0:
        streak += 1
    else:
        break

# Grade semanal: colunas = semanas; linhas = dias da semana.
first_weekday = month_start.weekday()
cells = []
for d in days:
    date = dt.date.fromisoformat(d["date"])
    col = (first_weekday + date.day - 1) // 7
    row = (date.weekday() + 1) % 7
    count = int(d["contributionCount"])
    level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 5 else 3 if count <= 9 else 4
    palette = ["#1e293b", "#134e4a", "#0f766e", "#14b8a6", "#5eead4"]
    x, y = 42 + col * 24, 108 + row * 23
    cells.append(f'<rect x="{x}" y="{y}" width="17" height="17" rx="4" fill="{palette[level]}"><title>{date.isoformat()}: {count} contribuições</title></rect>')
grid = "".join(cells)
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="310" viewBox="0 0 1000 310" role="img" aria-labelledby="title desc">
<title id="title">Contribuições de {today.strftime('%B %Y')}</title>
<desc id="desc">{calendar['totalContributions']} contribuições no mês; {active_days} dias ativos; sequência atual de {streak} dias.</desc>
<rect x="4" y="4" width="992" height="302" rx="22" fill="#101827" stroke="#334155" stroke-width="2"/>
<text x="32" y="43" fill="#f8fafc" font-family="Arial" font-size="21" font-weight="700">ATIVIDADE NO GITHUB • {today.strftime('%m/%Y')}</text>
<text x="32" y="78" fill="#5eead4" font-family="Arial" font-size="25" font-weight="700">{calendar['totalContributions']}</text>
<text x="32" y="97" fill="#94a3b8" font-family="Arial" font-size="12">contribuições no mês</text>
<text x="270" y="78" fill="#f8fafc" font-family="Arial" font-size="25" font-weight="700">{active_days}</text>
<text x="270" y="97" fill="#94a3b8" font-family="Arial" font-size="12">dias ativos</text>
<text x="470" y="78" fill="#f8fafc" font-family="Arial" font-size="25" font-weight="700">{streak}</text>
<text x="470" y="97" fill="#94a3b8" font-family="Arial" font-size="12">dias seguidos neste mês</text>
<text x="710" y="78" fill="#f8fafc" font-family="Arial" font-size="25" font-weight="700">{best_day}</text>
<text x="710" y="97" fill="#94a3b8" font-family="Arial" font-size="12">dia com mais contribuições</text>
{grid}
<text x="42" y="286" fill="#64748b" font-family="Arial" font-size="12">Menos</text>
<rect x="91" y="274" width="14" height="14" rx="3" fill="#1e293b"/><rect x="112" y="274" width="14" height="14" rx="3" fill="#134e4a"/><rect x="133" y="274" width="14" height="14" rx="3" fill="#0f766e"/><rect x="154" y="274" width="14" height="14" rx="3" fill="#14b8a6"/><rect x="175" y="274" width="14" height="14" rx="3" fill="#5eead4"/>
<text x="198" y="286" fill="#64748b" font-family="Arial" font-size="12">Mais</text>
</svg>
"""
Path("assets/contributions.svg").write_text(svg, encoding="utf-8")
print("Calendário atualizado:", calendar["totalContributions"], "contribuições")
