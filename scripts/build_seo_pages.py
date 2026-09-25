#!/usr/bin/env python3
"""
Generates static, crawlable HTML pages for Tech2Market India from the live
Google Sheets data feed. Runs automatically via GitHub Actions (see
.github/workflows/build-seo-pages.yml) — you should not normally need to run
this by hand.

Output:
  /technology/<slug>.html   one real static page per opportunity
  /sector/<slug>.html       one real static page per category
  /sitemap.xml
  /robots.txt

These pages exist purely so search engines can index real content — the
interactive app (index.html, hash routes, live search/filtering) is
untouched and remains the primary way people browse the site. Each static
page links into the app for the full experience.
"""

import csv
import io
import os
import re
import urllib.request

SITE_ROOT = "https://atsaasowc.github.io/tech2market-india"
SHEET_ID = "1HJn4UjGTF1ScFff_ucyUZj0O4vLcwNjERrHmJsQ_S1Q"
OPPORTUNITIES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Opportunities"
COMPANIES_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Companies"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..")
TECH_DIR = os.path.join(OUTPUT_DIR, "technology")
SECTOR_DIR = os.path.join(OUTPUT_DIR, "sector")


def fetch_csv(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(raw)))


def slugify(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "untitled"


def esc(text):
    """Minimal HTML-escaping for text dropped into markup."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def truncate(text, length=155):
    text = (text or "").strip()
    if len(text) <= length:
        return text
    return text[: length - 1].rsplit(" ", 1)[0] + "…"


PAGE_STYLE = """
  :root{
    --ink:#16213E; --brass:#A9782C; --paper:#EDEBE3; --paper-raised:#F7F5EF;
    --line:#D8D3C4; --text-muted:#6B6558;
  }
  *{box-sizing:border-box;}
  body{
    margin:0; background:var(--paper); color:var(--ink);
    font-family:'Source Serif 4',Georgia,serif; line-height:1.6;
  }
  .wrap{max-width:760px; margin:0 auto; padding:32px 20px 60px;}
  a{color:var(--brass);}
  h1{font-size:1.9rem; margin-bottom:6px;}
  .meta{font-family:'IBM Plex Sans',Arial,sans-serif; color:var(--text-muted); font-size:0.92rem; margin-bottom:24px;}
  .block{background:var(--paper-raised); border:1px solid var(--line); padding:20px 22px; margin-bottom:16px; border-radius:2px;}
  .block h2{font-family:'IBM Plex Sans',Arial,sans-serif; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.5px; color:var(--brass); margin:0 0 10px;}
  .score-row{display:flex; justify-content:space-between; font-family:'IBM Plex Sans',Arial,sans-serif; font-size:0.9rem; padding:6px 0; border-bottom:1px dotted var(--line);}
  .score-row:last-child{border-bottom:none;}
  .cta{
    display:inline-block; background:var(--ink); color:#fff; text-decoration:none;
    font-family:'IBM Plex Sans',Arial,sans-serif; padding:12px 22px; border-radius:2px; margin-top:8px;
  }
  .tag-list a{
    display:inline-block; margin:4px 6px 0 0; padding:5px 10px; border:1px solid var(--line);
    border-radius:2px; font-family:'IBM Plex Sans',Arial,sans-serif; font-size:0.85rem; text-decoration:none; color:var(--ink);
  }
  .disclaimer{font-size:0.8rem; color:var(--text-muted); margin-top:24px;}
"""


def render_technology_page(opp, companies_for_opp, category_slug):
    title = opp.get("Title", "Untitled Opportunity")
    oid = opp.get("Opportunity_ID", "")
    short_desc = opp.get("Short_Description", "")
    problem = opp.get("Problem_Solved", "")
    category = opp.get("Category", "Uncategorized")
    institution = opp.get("Institution", "Institution unknown")
    country = opp.get("Country", "")
    trl = opp.get("TRL", "Unknown")
    status = opp.get("Status", "")
    comm_path = opp.get("Commercialization_Path", "")
    source_url = opp.get("Source_URL", "")

    scores = [
        ("India Market Fit", opp.get("India_Market_Fit_Score", "")),
        ("Manufacturability", opp.get("Manufacturability_Score", "")),
        ("Commercialization Readiness", opp.get("Commercialization_Readiness_Score", "")),
        ("Market Opportunity", opp.get("Market_Opportunity_Score", "")),
        ("IP Defensibility", opp.get("IP_Defensibility_Score", "")),
        ("Regulatory Complexity", opp.get("Regulatory_Complexity_Score", "")),
        ("Overall", opp.get("Overall_Score", "")),
    ]
    score_rows = "\n".join(
        f'<div class="score-row"><span>{esc(label)}</span><strong>{esc(val) or "—"}</strong></div>'
        for label, val in scores
    )

    partners_html = ""
    if companies_for_opp:
        names = "".join(f"<li>{esc(c.get('Name',''))}</li>" for c in companies_for_opp)
        partners_html = f'<div class="block"><h2>Potential Commercialization Partners</h2><ul>{names}</ul>' \
                         f'<p class="disclaimer">Identified based on publicly available information and platform analysis — not confirmation of interest.</p></div>'

    source_html = (
        f'<p><a href="{esc(source_url)}" target="_blank" rel="noopener">{esc(source_url)}</a></p>'
        if source_url else '<p>No public source on file.</p>'
    )

    app_link = f"{SITE_ROOT}/#/opportunity/{oid}"
    sector_link = f"{SITE_ROOT}/sector/{category_slug}.html"
    description = truncate(short_desc or problem or title)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Tech2Market India</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE_ROOT}/technology/{esc(slugify(title) + '-' + oid.lower())}.html">
<style>{PAGE_STYLE}</style>
</head>
<body>
<div class="wrap">
  <p><a href="{SITE_ROOT}/">Tech2Market India</a> / <a href="{sector_link}">{esc(category)}</a></p>
  <h1>{esc(title)}</h1>
  <div class="meta">{esc(category)} · {esc(institution)} · {esc(country)} · TRL: {esc(trl)} · {esc(status)}</div>

  <div class="block">
    <h2>Overview</h2>
    <p>{esc(short_desc)}</p>
  </div>

  <div class="block">
    <h2>Problem Solved</h2>
    <p>{esc(problem) or 'Not stated.'}</p>
  </div>

  <div class="block">
    <h2>Commercialization Snapshot</h2>
    {score_rows}
    <p class="disclaimer">These are platform assessments based on available public evidence, not independently verified facts.</p>
  </div>

  {partners_html}

  <div class="block">
    <h2>Commercialization Path</h2>
    <p>{esc(comm_path) or 'Not yet assessed.'}</p>
  </div>

  <div class="block">
    <h2>Source &amp; Evidence</h2>
    {source_html}
  </div>

  <a class="cta" href="{app_link}">Pursue This Technology / View Live Details →</a>
</div>
</body>
</html>"""


def render_sector_page(category, opps_in_category):
    slug = slugify(category)
    items = ""
    for o in opps_in_category:
        oid = o.get("Opportunity_ID", "")
        title = o.get("Title", "Untitled")
        desc = truncate(o.get("Short_Description", ""), 140)
        tech_slug = slugify(title) + "-" + oid.lower()
        items += f'<div class="block"><h2 style="text-transform:none; color:var(--ink); font-size:1.1rem; letter-spacing:0;">' \
                 f'<a href="{SITE_ROOT}/technology/{tech_slug}.html">{esc(title)}</a></h2><p style="margin:0;">{esc(desc)}</p></div>'

    description = truncate(f"{len(opps_in_category)} commercialization opportunities in {category} sourced from Indian research institutions, available for licensing, manufacturing partnership, or investment.")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(category)} Technologies — Tech2Market India</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{SITE_ROOT}/sector/{slug}.html">
<style>{PAGE_STYLE}</style>
</head>
<body>
<div class="wrap">
  <p><a href="{SITE_ROOT}/">Tech2Market India</a></p>
  <h1>{esc(category)} Technologies</h1>
  <div class="meta">{len(opps_in_category)} opportunities in this sector</div>
  {items}
  <a class="cta" href="{SITE_ROOT}/#/discover">Browse All Technologies →</a>
</div>
</body>
</html>"""


def build_sitemap(urls):
    entries = "\n".join(f"  <url><loc>{esc(u)}</loc></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>'


def main():
    print("Fetching Opportunities...")
    opportunities = fetch_csv(OPPORTUNITIES_URL)
    opportunities = [o for o in opportunities if (o.get("Opportunity_ID") or "").strip()]
    print(f"  {len(opportunities)} opportunities loaded")

    print("Fetching Companies...")
    try:
        companies = fetch_csv(COMPANIES_URL)
    except Exception as e:
        print(f"  Companies fetch failed ({e}), continuing without partner data")
        companies = []

    companies_by_opp = {}
    for c in companies:
        oid = (c.get("Opportunity_ID") or "").strip()
        if oid:
            companies_by_opp.setdefault(oid, []).append(c)

    os.makedirs(TECH_DIR, exist_ok=True)
    os.makedirs(SECTOR_DIR, exist_ok=True)

    sitemap_urls = [f"{SITE_ROOT}/", f"{SITE_ROOT}/#/discover", f"{SITE_ROOT}/#/find-technology", f"{SITE_ROOT}/#/about"]
    categories = {}

    for opp in opportunities:
        oid = opp.get("Opportunity_ID", "").strip()
        title = opp.get("Title", "")
        category = opp.get("Category", "Uncategorized") or "Uncategorized"
        category_slug = slugify(category)
        categories.setdefault(category, []).append(opp)

        slug = f"{slugify(title)}-{oid.lower()}"
        html = render_technology_page(opp, companies_by_opp.get(oid, []), category_slug)
        path = os.path.join(TECH_DIR, f"{slug}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        sitemap_urls.append(f"{SITE_ROOT}/technology/{slug}.html")

    for category, opps_in_category in categories.items():
        slug = slugify(category)
        html = render_sector_page(category, opps_in_category)
        path = os.path.join(SECTOR_DIR, f"{slug}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        sitemap_urls.append(f"{SITE_ROOT}/sector/{slug}.html")

    with open(os.path.join(OUTPUT_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(sitemap_urls))

    with open(os.path.join(OUTPUT_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_ROOT}/sitemap.xml\n")

    print(f"Generated {len(opportunities)} technology pages, {len(categories)} sector pages, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()

