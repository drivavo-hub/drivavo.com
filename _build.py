#!/usr/bin/env python3
"""Build drivavo.com/writing/ from the Markdown posts in _writing/.

Each post is _writing/YYYY-MM-DD-slug.md with front matter (title, subtitle, date, slug).
Writes writing/index.html (the list) and writing/<slug>/index.html (each post).
Run from the repo root: python3 _build.py
Folders starting with "_" are not served by GitHub Pages.
"""
import datetime, html, os, re, glob
import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "_writing")
OUT = os.path.join(ROOT, "writing")

CSS = """
:root{
  --bg:#15122A;--panel:#1D1937;--ink:#ECEAF5;--ink-2:#B3AFC8;--line:#332D56;--indigo:#EDE8FB;--orange:#F2A24A;--teal:#6FC2BC;
  --display:"DM Serif Display",Georgia,"Times New Roman",serif;--body:"IBM Plex Sans",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:880px;margin:0 auto;padding-inline:20px;padding-block:28px 56px;display:flex;flex-direction:column;gap:56px}
a{color:inherit}
a:focus-visible{outline:2px solid var(--teal);outline-offset:3px}
header.top{display:flex;align-items:center;gap:12px}
header.top .home{display:flex;align-items:center;gap:12px;text-decoration:none}
header.top img{width:44px;height:auto}
header.top .word{font-family:var(--display);font-size:26px;letter-spacing:.01em;color:var(--indigo)}
header.top nav{margin-left:auto;font-size:13px;letter-spacing:.06em;text-transform:uppercase}
header.top nav a{color:var(--ink-2);text-decoration:none;padding:6px 0}
header.top nav a:hover,header.top nav a[aria-current]{color:var(--indigo)}
h1{font-family:var(--display);font-weight:400;font-size:clamp(34px,5.4vw,50px);line-height:1.08;margin:0;color:var(--indigo);text-wrap:balance}
.posts{list-style:none;margin:0;padding:0;border-top:1px solid var(--line)}
.posts li{border-bottom:1px solid var(--line);padding:26px 0 24px 32px}
.posts .date{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);margin:0 0 6px}
.posts h2{font-family:var(--display);font-weight:400;font-size:30px;line-height:1.15;margin:0 0 8px;color:var(--indigo);text-wrap:balance}
.posts h2 a{text-decoration:none}
.posts h2 a:hover{text-decoration:underline;text-decoration-color:var(--orange);text-underline-offset:5px;text-decoration-thickness:1px}
.posts .dek{color:var(--ink-2);margin:0;max-width:62ch}
article{max-width:68ch}
article .kicker{font-size:13px;letter-spacing:.06em;text-transform:uppercase;margin:0 0 16px}
article .kicker a{color:var(--teal);text-decoration:none}
article .dek{font-size:20px;line-height:1.5;color:var(--ink-2);margin:16px 0 0}
article .byline{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);margin:22px 0 0;padding-bottom:26px;border-bottom:1px solid var(--line)}
.body{margin-top:30px;font-size:18px;line-height:1.72}
.body p{margin:0 0 20px}
.body h2{font-family:var(--display);font-weight:400;font-size:28px;line-height:1.2;margin:40px 0 14px;color:var(--indigo)}
.body a{color:var(--orange);text-decoration:none;white-space:nowrap}
.body a:hover{text-decoration:underline}
.more{font-size:15px;margin:0}
.more a{color:var(--teal);text-decoration:none}
footer{font-size:13px;color:var(--ink-2);border-top:1px solid var(--line);padding-top:18px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 24px}
@media (max-width:640px){
  .wrap{gap:40px}
  .posts li{padding-left:0}
  .body{font-size:17px}
}
""".strip()

def page(title, description, body, current_writing=True):
    return f"""<!doctype html>
<html lang="en">
<head>
<title>{html.escape(title)}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{html.escape(description, quote=True)}">
<meta name="robots" content="noindex, nofollow, noarchive, noimageindex">
<link rel="icon" type="image/png" sizes="64x64" href="/favicon.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
/* Built by _build.py from _writing/*.md. Same palette and type as the lander (index.html). */
{CSS}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a class="home" href="/"><img src="/logo.png" alt=""><span class="word">Drivavo</span></a>
    <nav><a href="/writing/"{' aria-current="page"' if current_writing else ''}>Writing</a></nav>
  </header>
{body}
  <footer>
    <span>Drivavo, LLC</span>
    <span>Colorado · Florida</span>
  </footer>
</div>
</body>
</html>
"""

def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    meta = dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)
    meta["body_md"] = m.group(2).strip()
    meta["date"] = datetime.date.fromisoformat(meta["date"])
    return meta

def nice(d):
    return d.strftime("%B ") + str(d.day) + d.strftime(", %Y")

def linkify(h):
    h = re.sub(r"(?<![\w@/:.])([\w.+-]+@[\w-]+\.[\w.]+\w)", r'<a href="mailto:\1">\1</a>', h)
    def tel(m):
        digits = re.sub(r"\D", "", m.group(0))
        return f'<a href="tel:+1{digits}">{m.group(0)}</a>'
    return re.sub(r"\(\d{3}\) \d{3}-\d{4}", tel, h)

def main():
    posts = sorted((parse(p) for p in glob.glob(os.path.join(SRC, "*.md"))), key=lambda p: p["date"], reverse=True)
    today = datetime.date.today()
    posts = [p for p in posts if p["date"] <= today]  # future-dated posts wait for their day
    for p in posts:
        body_html = linkify(markdown.markdown(p["body_md"], output_format="html5"))
        body_html = "\n".join("      " + l for l in body_html.splitlines())
        content = f"""  <article>
    <p class="kicker"><a href="/writing/">Writing</a></p>
    <h1>{html.escape(p['title'])}</h1>
    <p class="dek">{html.escape(p['subtitle'])}</p>
    <p class="byline">Bill Henry · <time datetime="{p['date'].isoformat()}">{nice(p['date'])}</time></p>
    <div class="body">
{body_html}
    </div>
  </article>
  <p class="more"><a href="/writing/">More writing</a></p>"""
        d = os.path.join(OUT, p["slug"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(
            page(f"{p['title']} · Drivavo", p["subtitle"], content, current_writing=False))
    items = "\n".join(f"""    <li>
      <p class="date"><time datetime="{p['date'].isoformat()}">{nice(p['date'])}</time></p>
      <h2><a href="/writing/{p['slug']}/">{html.escape(p['title'])}</a></h2>
      <p class="dek">{html.escape(p['subtitle'])}</p>
    </li>""" for p in posts)
    content = f"""  <section>
    <h1>Writing</h1>
  </section>
  <ul class="posts">
{items}
  </ul>"""
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page("Writing · Drivavo", "Writing from Bill Henry at Drivavo.", content))
    print(f"built {len(posts)} post(s)")

if __name__ == "__main__":
    main()
