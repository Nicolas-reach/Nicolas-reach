#!/usr/bin/env python3
"""Generates two hexagon charts (SVG) for the profile README:

  assets/hex-atividade.svg   -> Commits, Pull Requests, Issues, Reviews, Repositories, Stars
  assets/hex-linguagens.svg  -> the 6 most used languages in your repositories

Usage (GitHub Actions): GITHUB_TOKEN=... USERNAME=your-username python scripts/hex_stats.py
Usage (local preview):  python scripts/hex_stats.py --demo
Uses only the Python standard library.
"""
import json
import math
import os
import sys
import urllib.request

# ---------- "Green and steel" palette ----------
BG = "#0d1110"
PANEL = "#121816"
STEEL = "#9aa7a1"
STEEL_LIGHT = "#d4dcd8"
GRID = "#2a3530"
GREEN = "#43a047"
GREEN_LIGHT = "#7bd88f"
GREEN_DARK = "#1b5e20"
FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"

SHORT = {"Jupyter Notebook": "Jupyter", "TypeScript": "TypeScript", "Dockerfile": "Docker"}

W, H = 460, 440
CX, CY, R = 230, 255, 115

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoryContributions
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        sys.exit(f"GitHub API error: {data['errors']}")
    user = data["data"]["user"]
    cc = user["contributionsCollection"]
    repos = user["repositories"]

    langs = {}
    for repo in repos["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            langs[name] = langs.get(name, 0) + edge["size"]

    activity = [
        ("Commits", cc["totalCommitContributions"]),
        ("Pull Requests", cc["totalPullRequestContributions"]),
        ("Issues", cc["totalIssueContributions"]),
        ("Reviews", cc["totalPullRequestReviewContributions"]),
        ("Repositories", repos["totalCount"]),
        ("Stars", sum(r["stargazerCount"] for r in repos["nodes"])),
    ]
    return activity, langs, cc["contributionCalendar"]["totalContributions"]


def demo():
    activity = [("Commits", 3120), ("Pull Requests", 412), ("Issues", 23),
                ("Reviews", 18), ("Repositories", 31), ("Stars", 337)]
    langs = {"CSS": 550, "HTML": 200, "Jupyter Notebook": 130, "Java": 50,
             "Python": 40, "JavaScript": 30}
    return activity, langs, 4079


# ---------- Drawing ----------
def point(i, frac, n=6):
    ang = -math.pi / 2 + 2 * math.pi * i / n
    return CX + R * frac * math.cos(ang), CY + R * frac * math.sin(ang)


def poly(fracs):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (point(i, f) for i, f in enumerate(fracs)))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(title, subtitle, labels, values_txt, fracs, rings, ring_labels=None):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           "<defs>",
           f'<linearGradient id="steel" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{STEEL_LIGHT}"/>'
           f'<stop offset="0.5" stop-color="{STEEL}"/><stop offset="1" stop-color="#5d6964"/></linearGradient>',
           f'<radialGradient id="fill"><stop offset="0" stop-color="{GREEN_LIGHT}" stop-opacity="0.55"/>'
           f'<stop offset="1" stop-color="{GREEN}" stop-opacity="0.25"/></radialGradient>',
           '<filter id="glow"><feGaussianBlur stdDeviation="2.5" result="b"/>'
           '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
           "<style>.lbl{font:600 13px " + FONT + ";fill:" + STEEL_LIGHT + "}"
           ".val{font:700 12px " + FONT + ";fill:" + GREEN_LIGHT + "}"
           ".rng{font:9px " + FONT + ";fill:#5d6964}"
           "@keyframes grow{from{transform:scale(0)}to{transform:scale(1)}}"
           ".shape{transform-origin:" + f"{CX}px {CY}px" + ";animation:grow 1.2s ease-out}</style>",
           "</defs>",
           f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{BG}" stroke="url(#steel)" stroke-width="2"/>',
           f'<text x="24" y="38" style="font:700 17px {FONT};fill:{STEEL_LIGHT};letter-spacing:2px">{esc(title)}</text>',
           f'<text x="24" y="58" style="font:12px {FONT};fill:{STEEL}">{esc(subtitle)}</text>',
           f'<line x1="24" y1="68" x2="{W-24}" y2="68" stroke="{GREEN_DARK}" stroke-width="2"/>']

    out.append(f'<polygon points="{poly([1] * 6)}" fill="{PANEL}"/>')
    for k in range(1, rings + 1):
        out.append(f'<polygon points="{poly([k / rings] * 6)}" fill="none" stroke="{GRID}" stroke-width="1"/>')
        if ring_labels:
            x, y = point(0, k / rings)
            out.append(f'<text class="rng" x="{x + 4:.1f}" y="{y + 3:.1f}">{ring_labels[k - 1]}</text>')
    for i in range(6):
        x, y = point(i, 1)
        out.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')

    out.append(f'<g class="shape"><polygon points="{poly(fracs)}" fill="url(#fill)" stroke="{GREEN_LIGHT}" '
               f'stroke-width="2" stroke-linejoin="round" filter="url(#glow)"/>')
    for i, f in enumerate(fracs):
        x, y = point(i, f)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{BG}" stroke="{GREEN_LIGHT}" stroke-width="2"/>')
    out.append("</g>")

    for i, (lab, val) in enumerate(zip(labels, values_txt)):
        x, y = point(i, 1.22)
        anchor = "middle" if abs(x - CX) < 5 else ("start" if x > CX else "end")
        dy = -8 if i == 0 else (6 if i == 3 else 0)
        out.append(f'<text class="lbl" x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}">{esc(lab)}</text>')
        out.append(f'<text class="val" x="{x:.1f}" y="{y + dy + 15:.1f}" text-anchor="{anchor}">{esc(val)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def main():
    if "--demo" in sys.argv:
        activity, langs, total = demo()
    else:
        token, login = os.environ.get("GITHUB_TOKEN"), os.environ.get("USERNAME")
        if not token or not login:
            sys.exit("Set GITHUB_TOKEN and USERNAME.")
        activity, langs, total = fetch(login, token)

    # Activity: logarithmic scale (1, 10, 100, 1k, 10k), like the 3D chart
    fr = [min(math.log10(v + 1) / 4, 1) if v > 0 else 0.02 for _, v in activity]
    svg_a = card("ACTIVITY", f"{fmt(total)} contributions in the last year",
                 [a for a, _ in activity], [fmt(v) for _, v in activity], fr, 4,
                 ["10", "100", "1k", "10k"])

    # Languages: top 6, radius proportional to share
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]
    while len(top) < 6:
        top.append(("—", 0))
    total_b = sum(langs.values()) or 1
    pct = [b / total_b * 100 for _, b in top]
    mx = max(pct) or 1
    fr_l = [max(math.sqrt(p / mx), 0.03) for p in pct]  # sqrt: keeps small differences visible
    svg_l = card("LANGUAGES", "Share of code across repositories",
                 [SHORT.get(n, n) for n, _ in top], [f"{p:.1f}%" if p else "" for p in pct], fr_l, 4)

    os.makedirs("assets", exist_ok=True)
    with open("assets/hex-atividade.svg", "w", encoding="utf-8") as f:
        f.write(svg_a)
    with open("assets/hex-linguagens.svg", "w", encoding="utf-8") as f:
        f.write(svg_l)
    print("Generated: assets/hex-atividade.svg, assets/hex-linguagens.svg")


if __name__ == "__main__":
    main()
