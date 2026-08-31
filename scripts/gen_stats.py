"""GitHub istatistik kartını üretir: assets/stats.svg

Dış servise (vercel vb.) bağımlı olmamak için istatistikleri doğrudan
GitHub API'den çekip SVG'yi kendimiz çiziyoruz.
"""

import json
import os
import urllib.error
import urllib.request

USER = os.environ.get("GH_USER", "EmreOzkull")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join("assets", "stats.svg")

API = "https://api.github.com"
HEAD = {
    "Accept": "application/vnd.github+json",
    "User-Agent": f"{USER}-profile-stats",
}
if TOKEN:
    HEAD["Authorization"] = f"Bearer {TOKEN}"


def get(url):
    req = urllib.request.Request(url, headers=HEAD)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def graphql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        f"{API}/graphql", data=body, headers={**HEAD, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    user = get(f"{API}/users/{USER}")

    repos, page = [], 1
    while page <= 10:
        batch = get(f"{API}/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            break
        page += 1

    stars = sum(r.get("stargazers_count", 0) for r in repos)

    merged_prs = 0
    try:
        q = f"{API}/search/issues?q=author:{USER}+type:pr+is:merged&per_page=1"
        merged_prs = get(q).get("total_count", 0)
    except (urllib.error.URLError, KeyError, TypeError):
        pass

    contributions = 0
    try:
        q = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
              totalCommitContributions
              restrictedContributionsCount
            }
          }
        }
        """
        data = graphql(q, {"login": USER})
        c = data["data"]["user"]["contributionsCollection"]
        contributions = c["contributionCalendar"]["totalContributions"]
    except (urllib.error.URLError, KeyError, TypeError):
        pass

    return {
        "repos": user.get("public_repos", len(repos)),
        "stars": stars,
        "prs": merged_prs,
        "followers": user.get("followers", 0),
        "contributions": contributions,
        "since": (user.get("created_at") or "2019")[:4],
    }


CARD = """<svg width="520" height="200" viewBox="0 0 520 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub istatistikleri">
  <defs>
    <pattern id="sd" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.4" fill="#151d2a"/>
    </pattern>
    <clipPath id="sc"><rect width="520" height="200" rx="14"/></clipPath>
  </defs>
  <style>
    .mono{{font-family:'Cascadia Code','JetBrains Mono','Fira Code',Consolas,monospace}}
    .k{{font-size:13px;fill:#56728f;letter-spacing:1px}}
    .v{{font-size:30px;font-weight:700;fill:#f0f6fc}}
    .blink{{animation:b 1.6s steps(2,start) infinite}}
    @keyframes b{{50%{{opacity:.15}}}}
  </style>
  <g clip-path="url(#sc)">
    <rect width="520" height="200" fill="#0d1117"/>
    <rect width="520" height="200" fill="url(#sd)"/>
    <path d="M0,168 H140 L164,144 H340" fill="none" stroke="#1d2b3d" stroke-width="2"/>
    <circle cx="340" cy="144" r="3" fill="#24384f"/>
    <text x="24" y="38" class="mono" font-size="14" fill="#00E5FF">&gt; gh api /users/{user}<tspan class="blink" fill="#FFB000">▮</tspan></text>
    <path d="M24,52 H496" stroke="#1e2836" stroke-width="1.5"/>

    <text x="24"  y="96"  class="mono v">{repos}</text>
    <text x="24"  y="116" class="mono k">DEPO</text>
    <text x="148" y="96"  class="mono v" fill="#FFB000">{contributions}</text>
    <text x="148" y="116" class="mono k">KATKI / YIL</text>
    <text x="272" y="96"  class="mono v" fill="#00E5FF">{prs}</text>
    <text x="272" y="116" class="mono k">BİRLEŞEN PR</text>
    <text x="396" y="96"  class="mono v">{followers}</text>
    <text x="396" y="116" class="mono k">TAKİPÇİ</text>

    <text x="24"  y="176" class="mono" font-size="12" fill="#3b4f66">{since}'dan beri GitHub'da</text>
    <text x="496" y="176" class="mono" font-size="12" fill="#3b4f66" text-anchor="end">@{user}</text>
  </g>
  <rect x="1" y="1" width="518" height="198" rx="14" fill="none" stroke="#1e2836" stroke-width="2"/>
</svg>
"""


def main():
    s = collect()
    svg = CARD.format(user=USER, **s)
    os.makedirs("assets", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"yazildi: {OUT} -> {s}")


if __name__ == "__main__":
    main()
