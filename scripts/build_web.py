#!/usr/bin/env python3
"""Build the GitHub Pages interactive web edition of Essentials for Financial Derivatives.

Reads all modular LaTeX sources in chapters/*.tex, converts prose, theorems, proofs,
examples, tables, figures, and cross-references into clean semantic HTML5 with KaTeX
math rendering, and embeds 8 interactive Plotly.js quantitative finance labs.
"""
import html
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS_DIR = os.path.join(ROOT, "chapters")
DOCS_DIR = os.path.join(ROOT, "docs")
FIGURE_SRC = os.path.join(ROOT, "Figure")
FIGURE_DST = os.path.join(DOCS_DIR, "Figure")

PAGES = [
    ("ch01", "chapters/ch01_introduction.tex", "Chapter 1", "01", "Introduction",
     "No-arbitrage, dividend cost-of-carry, Forwards vs. Futures & CCPs, Put–Call Parity, and 0DTE options.", "lab-1"),
    ("ch02", "chapters/ch02_discrete_time_models.tex", "Chapter 2", "02", "Discrete Time Models",
     "Binomial & trinomial trees, CRR convergence, Discrete FTAP 1 & 2, and dividend/negative-rate early exercise.", "lab-2"),
    ("ch03", "chapters/ch03_math_preliminaries.tex", "Chapter 3", "03", "Math Preliminaries",
     "Brownian motion, Itô calculus, multi-D Itô, Girsanov, Feynman–Kac, jump-diffusion, and Fractional Brownian Motion.", "lab-3"),
    ("ch04", "chapters/ch04_black_scholes_model.tex", "Chapter 4", "04", "Black–Scholes Model",
     "BS PDE & Rannacher finite differences, 1st & 2nd-order Greeks (Vanna/Volga/Charm), Black-76, and Deep Hedging.", "lab-4"),
    ("ch05", "chapters/ch05_implied_volatility.tex", "Chapter 5", "05", "Implied Volatility Skew (Smile)",
     "Static no-arbitrage, Breeden–Litzenberger, SVI/SSVI, Dupire, Heston/SABR, Rough Volatility, LSV, Variance Swaps & VIX.", "lab-5"),
    ("ch06", "chapters/ch06_exotic_options.tex", "Chapter 6", "06", "Exotic Options",
     "Digital options & Pin Risk, Barriers & BGK correction, Autocallables/Snowballs, Asian (Kemna–Vorst), Lookback, FX & Quanto.", "lab-6"),
    ("ch07", "chapters/ch07_american_options.tex", "Chapter 7", "07", "American Options",
     "Snell envelope, LCP & smooth pasting, perpetual Put & dividend Call, PSOR, Longstaff–Schwartz (LSM), and Deep Optimal Stopping.", "lab-7"),
    ("ch08", "chapters/ch08_interest_rate_modelling.tex", "Chapter 8", "08", "Interest Rate Modelling",
     "Ho–Lee, Vasicek, CIR (Feller), HJM, Bachelier/Shifted LN, Post-LIBOR SOFR & OIS Multi-Curve, FMM, ISDA CDS & XVA.", "lab-8"),
    ("ch09", "chapters/ch09_problem_set.tex", "Chapter 9", "09", "Problem Set",
     "21 analytical and numerical exercises spanning discrete trees, stochastic calculus, PDEs, Monte Carlo, and FX vol.", None),
    ("appA", "chapters/appA_expectation_conditioning.tex", "Appendix A", "A", "Expectation, Information and Conditioning",
     "Measure-theoretic Lebesgue expectation, integrability, and conditional expectation (Tower Property).", None),
    ("appB", "chapters/appB_monte_carlo.tex", "Appendix B", "B", "Monte Carlo Simulation",
     "CLT confidence intervals, Euler–Maruyama & Milstein schemes, Antithetic/Control/Importance Sampling, and QMC.", None),
    ("appC", "chapters/appC_bs_pde_alternative.tex", "Appendix C", "C", "Alternative Derivation of Black–Scholes PDE",
     "Self-financing portfolio derivation via instantaneous riskless return equivalence.", None),
    ("appD", "chapters/appD_girsanov_proof.tex", "Appendix D", "D", "An Abbreviated Proof of Girsanov's Theorem",
     "Lévy's characterization of Brownian motion and Radon–Nikodym drift transformation under Novikov's condition.", None),
    ("appE", "chapters/appE_bilingual_table.tex", "Appendix E", "E", "Bilingual Terminology Table",
     "English–Chinese quantitative finance glossary covering classical and frontier derivatives terminology.", None),
]

THEOREM_ENVS = {
    "definition": "Definition",
    "proposition": "Proposition",
    "theorem": "Theorem",
    "lemma": "Lemma",
    "corollary": "Corollary",
    "example": "Example",
    "note": "Note",
    "remark": "Remark",
    "problem": "Problem",
}


def build_label_index():
    """First pass: map every \\label{...} to (slug, human_label)."""
    label_map = {}
    for slug, relpath, chap_label, chap_num, title, _, _ in PAGES:
        with open(os.path.join(ROOT, relpath), "r", encoding="utf-8") as f:
            tex = f.read()
        counters = {k: 0 for k in THEOREM_ENVS}
        counters.update({"section": 0, "subsection": 0, "equation": 0, "table": 0, "figure": 0})
        # Simple sequential scan for labels
        tokens = re.finditer(
            r"\\(chapter|section|subsection|begin)\*?\{([^}]+)\}|\\label\{([^}]+)\}",
            tex,
        )
        cur_num = chap_num
        for m in tokens:
            if m.group(1) == "chapter":
                cur_num = chap_num
            elif m.group(1) == "section":
                counters["section"] += 1
                counters["subsection"] = 0
                cur_num = f"{chap_num}.{counters['section']}"
            elif m.group(1) == "subsection":
                counters["subsection"] += 1
                cur_num = f"{chap_num}.{counters['section']}.{counters['subsection']}"
            elif m.group(1) == "begin":
                env = m.group(2)
                if env in THEOREM_ENVS:
                    counters[env] += 1
                    cur_num = f"{chap_num}.{counters[env]}"
                elif env in ("equation", "align"):
                    counters["equation"] += 1
                    cur_num = f"{chap_num}.{counters['equation']}"
                elif env in ("table", "longtable"):
                    counters["table"] += 1
                    cur_num = f"{chap_num}.{counters['table']}"
                elif env == "figure":
                    counters["figure"] += 1
                    cur_num = f"{chap_num}.{counters['figure']}"
            elif m.group(3):
                label_map[m.group(3)] = (slug, cur_num)
    return label_map


def convert_tabular(body, caption="", label_id=""):
    """Convert a LaTeX tabular/tabularx/longtable body to a clean booktabs HTML table."""
    # Remove longtable header/footer directives
    body = re.sub(r"\\end(?:first)?head|\\end(?:last)?foot", "", body)
    body = re.sub(r"\\multicolumn\{(\d+)\}\{[^}]*\}\{([^}]*)\}", r"\2", body)
    body = re.sub(r"\\(?:toprule|bottomrule|hline|centering|small|footnotesize|normalsize)\b", "", body)
    body = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}", "", body)

    # Split header vs body on \midrule
    parts = re.split(r"\\midrule", body, maxsplit=1)
    def parse_rows(chunk):
        rows = []
        for raw_row in re.split(r"\\\\(?:\[[^\]]*\])?", chunk):
            raw_row = raw_row.strip()
            if not raw_row or raw_row.startswith("\\caption") or raw_row.startswith("\\label"):
                continue
            cells = [c.strip() for c in raw_row.split("&")]
            if any(cells):
                rows.append(cells)
        return rows

    head_rows = parse_rows(parts[0]) if len(parts) == 2 else []
    body_rows = parse_rows(parts[1]) if len(parts) == 2 else parse_rows(parts[0])

    id_attr = f' id="{html.escape(label_id)}"' if label_id else ""
    out = [f'<div class="table-wrap"{id_attr}><table class="booktabs">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    if head_rows:
        out.append("<thead>")
        for r in head_rows:
            out.append("<tr>" + "".join(f"<th>{c}</th>" for c in r) + "</tr>")
        out.append("</thead>")
    out.append("<tbody>")
    for r in body_rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def convert_tex_to_html(tex, slug, chap_num, label_map):
    """Convert a chapter's LaTeX source into clean HTML + collect TOC headings."""
    # Strip comments (preserving escaped \%)
    tex = re.sub(r"(?<!\\)%.*", "", tex)
    # Remove top-level \chapter{...}
    tex = re.sub(r"\\chapter\*?\{[^}]*\}(?:\s*\\label\{[^}]*\})?", "", tex, count=1)

    # Protect math blocks so inline LaTeX replacements never touch math internals
    math_store = []
    def stash_math(m):
        idx = len(math_store)
        math_store.append(m.group(0))
        return f"@@MATH{idx}@@"

    # Display math environments: equation, align, align*, gather*, \[...\]
    def stash_display_env(m):
        env = m.group(1)
        inner = m.group(2)
        lbl_m = re.search(r"\\label\{([^}]+)\}", inner)
        anchor = f'<span id="{html.escape(lbl_m.group(1))}"></span>' if lbl_m else ""
        inner_clean = re.sub(r"\\label\{[^}]+\}", "", inner)
        if env in ("align", "align*"):
            latex = f"$$\\begin{{aligned}}{inner_clean}\\end{{aligned}}$$"
        elif env in ("gather", "gather*"):
            latex = f"$$\\begin{{gathered}}{inner_clean}\\end{{gathered}}$$"
        else:
            latex = f"$${inner_clean}$$"
        idx = len(math_store)
        math_store.append(anchor + latex)
        return f"\n\n@@MATH{idx}@@\n\n"

    tex = re.sub(r"\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}", stash_display_env, tex, flags=re.DOTALL)
    tex = re.sub(r"\\\[(.*?)\\\]", lambda m: stash_math(m), tex, flags=re.DOTALL)
    # Inline math $...$
    tex = re.sub(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$", stash_math, tex, flags=re.DOTALL)

    # Convert figures
    def repl_figure(m):
        block = m.group(1)
        img_m = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", block)
        cap_m = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", block)
        lbl_m = re.search(r"\\label\{([^}]+)\}", block)
        if not img_m:
            return ""
        src = img_m.group(1)
        cap = cap_m.group(1) if cap_m else ""
        id_attr = f' id="{html.escape(lbl_m.group(1))}"' if lbl_m else ""
        if src.lower().endswith(".pdf"):
            return f'<figure class="tex-fig"{id_attr}><p><a href="{html.escape(src)}" target="_blank">Open vector figure ({html.escape(os.path.basename(src))})</a></p><figcaption>{cap}</figcaption></figure>'
        return f'<figure class="tex-fig"{id_attr}><img src="{html.escape(src)}" alt="{html.escape(cap)}" loading="lazy"><figcaption>{cap}</figcaption></figure>'

    tex = re.sub(r"\\begin\{figure\}(?:\[[^\]]*\])?(.*?)\\end\{figure\}", repl_figure, tex, flags=re.DOTALL)

    # Convert tables (table + tabular/tabularx, and longtable)
    def repl_table(m):
        block = m.group(1)
        cap_m = re.search(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}", block)
        lbl_m = re.search(r"\\label\{([^}]+)\}", block)
        tab_m = re.search(r"\\begin\{(?:tabularx?|tabular)\}(?:\{[^}]*\})*\{[^}]*\}(.*?)\\end\{(?:tabularx?|tabular)\}", block, flags=re.DOTALL)
        if not tab_m:
            return ""
        return "\n\n" + convert_tabular(tab_m.group(1), cap_m.group(1) if cap_m else "", lbl_m.group(1) if lbl_m else "") + "\n\n"

    tex = re.sub(r"\\begin\{table\}(?:\[[^\]]*\])?(.*?)\\end\{table\}", repl_table, tex, flags=re.DOTALL)
    tex = re.sub(
        r"\\begin\{longtable\}\{[^}]*\}(.*?)\\end\{longtable\}",
        lambda m: "\n\n" + convert_tabular(m.group(1), "Bilingual Quantitative Finance Terminology", "tab:bilingual") + "\n\n",
        tex,
        flags=re.DOTALL,
    )

    # Convert theorem-like environments & proof
    counters = {k: 0 for k in THEOREM_ENVS}
    for env, label_name in THEOREM_ENVS.items():
        def make_repl(e, ln):
            def _repl(m):
                counters[e] += 1
                opt = m.group(1) or ""
                body = m.group(2)
                lbl_m = re.search(r"\\label\{([^}]+)\}", body)
                id_attr = f' id="{html.escape(lbl_m.group(1))}"' if lbl_m else ""
                body = re.sub(r"\\label\{[^}]+\}", "", body)
                opt_str = f" ({opt})" if opt else ""
                return f'\n\n<div class="env-box env-{e}"{id_attr}><div class="env-title">{ln} {chap_num}.{counters[e]}{opt_str}</div>\n\n{body.strip()}\n\n</div>\n\n'
            return _repl
        tex = re.sub(rf"\\begin\{{{env}\}}(?:\[([^\]]*)\])?(.*?)\\end\{{{env}\}}", make_repl(env, label_name), tex, flags=re.DOTALL)

    tex = re.sub(
        r"\\begin\{proof\}(?:\[([^\]]*)\])?(.*?)\\end\{proof\}",
        lambda m: f'\n\n<div class="env-proof"><div class="env-title">{m.group(1) or "Proof"}.</div>\n\n{m.group(2).strip()} <span class="qed-mark">&#9723;</span>\n\n</div>\n\n',
        tex,
        flags=re.DOTALL,
    )

    # Convert sections, subsections, subsubsections, paragraphs and collect TOC
    toc = []
    sec_c = 0
    sub_c = 0

    def repl_sec(m):
        nonlocal sec_c, sub_c
        star, title = m.group(1), m.group(2)
        sec_id = f"sec-{sec_c + 1}"
        if not star:
            sec_c += 1
            sub_c = 0
            display = f"{chap_num}.{sec_c} {title}"
        else:
            sec_id = f"sec-s-{len(toc) + 1}"
            display = title
        toc.append(("h2", sec_id, display))
        return f'\n\n<h2 id="{sec_id}">{display}</h2>\n\n'

    def repl_subsec(m):
        nonlocal sub_c
        star, title = m.group(1), m.group(2)
        if not star:
            sub_c += 1
            sub_id = f"sub-{sec_c}-{sub_c}"
            display = f"{chap_num}.{sec_c}.{sub_c} {title}"
        else:
            sub_id = f"sub-s-{len(toc) + 1}"
            display = title
        toc.append(("h3", sub_id, display))
        return f'\n\n<h3 id="{sub_id}">{display}</h3>\n\n'

    tex = re.sub(r"\\section(\*?)\{([^}]*)\}", repl_sec, tex)
    tex = re.sub(r"\\subsection(\*?)\{([^}]*)\}", repl_subsec, tex)
    tex = re.sub(r"\\subsubsection\*?\{([^}]*)\}", r"\n\n<h4>\1</h4>\n\n", tex)
    tex = re.sub(r"\\paragraph\{([^}]*)\}", r"\n\n<h4>\1</h4>\n\n", tex)

    # Convert remaining labels into spans
    tex = re.sub(r"\\label\{([^}]+)\}", lambda m: f'<span id="{html.escape(m.group(1))}"></span>', tex)

    # Convert lists (supports nested enumerate/itemize)
    for _ in range(3):
        tex = re.sub(r"\\begin\{enumerate\}(?:\[[^\]]*\])?", "\n<ol>\n", tex)
        tex = re.sub(r"\\end\{enumerate\}", "\n</ol>\n", tex)
        tex = re.sub(r"\\begin\{itemize\}(?:\[[^\]]*\])?", "\n<ul>\n", tex)
        tex = re.sub(r"\\end\{itemize\}", "\n</ul>\n", tex)
    tex = re.sub(r"\\item(?:\[([^\]]*)\])?\s*", lambda m: f"<li><strong>{m.group(1)}</strong> " if m.group(1) else "<li>", tex)

    # Inline formatting & typography
    tex = re.sub(r"\\textbf\{((?:[^{}]|\{[^{}]*\})*)\}", r"<strong>\1</strong>", tex)
    tex = re.sub(r"\\(?:emph|textit)\{((?:[^{}]|\{[^{}]*\})*)\}", r"<em>\1</em>", tex)
    tex = re.sub(r"\\(?:texttt|path|verb\|)\{?([^}|]*)[}|]", r"<code>\1</code>", tex)
    tex = tex.replace("\\&", "&amp;").replace("\\%", "%").replace("\\$", "$").replace("\\_", "_")
    tex = tex.replace("\\^o", "ô").replace('\\\"o', "ö").replace("\\'e", "é").replace("\\'a", "á").replace('\\\"u', "ü")
    tex = re.sub(r"\\`\{?([a-zA-Z])\}?", r"\1", tex)
    tex = tex.replace("``", "&ldquo;").replace("''", "&rdquo;").replace("---", "&mdash;").replace("--", "&ndash;")
    tex = tex.replace("~", "&nbsp;").replace("\\,", " ").replace("\\ ", " ").replace("\\qedhere", "")

    # Cross-references \ref & \eqref
    def repl_ref(m):
        is_eq = m.group(1) == "eqref"
        lbl = m.group(2)
        if lbl in label_map:
            target_slug, num = label_map[lbl]
            href = f"#{lbl}" if target_slug == slug else f"{target_slug}.html#{lbl}"
            txt = f"({num})" if is_eq else num
            return f'<a href="{href}">{txt}</a>'
        return f"({lbl})" if is_eq else lbl

    tex = re.sub(r"\\(eq)?ref\{([^}]+)\}", repl_ref, tex)
    # Clean stray commands
    tex = re.sub(r"\\(?:noindent|smallskip|medskip|bigskip|newpage|clearpage|centering|vspace\*?\{[^}]*\})\b", "", tex)

    # Wrap plain paragraphs cleanly
    blocks = re.split(r"\n\s*\n", tex)
    html_blocks = []
    block_tags = ("<h2", "<h3", "<h4", "<div", "</div", "<ul", "</ul", "<ol", "</ol", "<li", "<figure", "<table", "<p")
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b.startswith(block_tags) or re.fullmatch(r"@@MATH\d+@@", b):
            html_blocks.append(b)
        else:
            html_blocks.append(f"<p>{b}</p>")
    out = "\n".join(html_blocks)

    # Restore stashed math
    for i, mstr in enumerate(math_store):
        out = out.replace(f"@@MATH{i}@@", mstr)

    # Also clean TOC titles of stashed math tokens
    clean_toc = []
    for lvl, hid, htitle in toc:
        for i, mstr in enumerate(math_store):
            htitle = htitle.replace(f"@@MATH{i}@@", mstr)
        clean_toc.append((lvl, hid, htitle))

    return out, clean_toc


def render_shell(active_slug, eyebrow, title, body_html, toc_items, pager_html, has_plotly=False):
    nav_main = []
    nav_app = []
    for slug, _, _, num, ptitle, _, _ in PAGES:
        cls = "nav-link active" if slug == active_slug else "nav-link"
        item = f'<li><a class="{cls}" href="{slug}.html"><span class="nav-num">{num}</span><span>{html.escape(ptitle)}</span></a></li>'
        if slug.startswith("ch"):
            nav_main.append(item)
        else:
            nav_app.append(item)

    toc_html = ""
    if toc_items:
        lis = [f'<li class="toc-{lvl}"><a href="#{hid}">{htitle}</a></li>' for lvl, hid, htitle in toc_items]
        toc_html = f'<aside class="toc-panel"><div class="toc-title">On this page</div><ul class="toc-list">{"".join(lis)}</ul></aside>'
    else:
        toc_html = '<aside class="toc-panel"></aside>'

    plotly_tag = '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js" defer></script>\n  <script src="assets/labs.js" defer></script>' if has_plotly else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} — Essentials for Financial Derivatives</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;0,6..72,700;1,6..72,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
  <link rel="stylesheet" href="assets/style.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
  {plotly_tag}
  <script defer src="assets/app.js"></script>
</head>
<body>
  <header class="topbar">
    <div class="topbar-left">
      <button class="btn-pill menu-toggle" id="menu-toggle" aria-label="Toggle chapters">Chapters</button>
      <a class="topbar-brand" href="index.html">Essentials for Financial Derivatives</a>
    </div>
    <div class="topbar-actions">
      <a class="btn-pill" href="Essentials_for_Financial_Derivatives.pdf" target="_blank">PDF Edition</a>
      <a class="btn-pill" href="https://github.com/Derek-Y-JQ/Essentials_for_Financial_Derivatives" target="_blank">GitHub</a>
      <button class="btn-pill" id="theme-toggle">Dark mode</button>
    </div>
  </header>

  <div class="layout">
    <nav class="sidebar" aria-label="Table of Contents">
      <input class="sidebar-search" id="nav-search" type="search" placeholder="Filter chapters...">
      <div class="sidebar-group-title">Chapters</div>
      <ul class="nav-list">{"".join(nav_main)}</ul>
      <div class="sidebar-group-title">Appendices</div>
      <ul class="nav-list">{"".join(nav_app)}</ul>
    </nav>

    <main class="content">
      <div class="chapter-eyebrow">{html.escape(eyebrow)}</div>
      <h1>{html.escape(title)}</h1>
      {body_html}
      {pager_html}
    </main>

    {toc_html}
  </div>
</body>
</html>
"""


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    # Sync raster/vector images to docs/Figure/
    os.makedirs(FIGURE_DST, exist_ok=True)
    for fn in os.listdir(FIGURE_SRC):
        if fn.lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".pdf")):
            shutil.copy2(os.path.join(FIGURE_SRC, fn), os.path.join(FIGURE_DST, fn))

    label_map = build_label_index()

    # Build chapter & appendix pages
    for idx, (slug, relpath, chap_label, chap_num, title, desc, lab_id) in enumerate(PAGES):
        with open(os.path.join(ROOT, relpath), "r", encoding="utf-8") as f:
            tex = f.read()
        body_html, toc_items = convert_tex_to_html(tex, slug, chap_num, label_map)
        if lab_id:
            lab_html = f'<section id="{lab_id}" class="quant-lab"></section>'
            # Insert interactive lab right before the last section or at the top of the chapter
            body_html = lab_html + "\n" + body_html
            toc_items.insert(0, ("h2", lab_id, "Interactive Quant Lab"))

        prev_html = '<div style="flex:1"></div>'
        if idx > 0:
            pslug, _, plabel, _, ptitle, _, _ = PAGES[idx - 1]
            prev_html = f'<a class="pager-card prev" href="{pslug}.html"><span class="pager-dir">&larr; Previous ({plabel})</span><span class="pager-title">{html.escape(ptitle)}</span></a>'
        next_html = '<div style="flex:1"></div>'
        if idx + 1 < len(PAGES):
            nslug, _, nlabel, _, ntitle, _, _ = PAGES[idx + 1]
            next_html = f'<a class="pager-card next" href="{nslug}.html"><span class="pager-dir">Next ({nlabel}) &rarr;</span><span class="pager-title">{html.escape(ntitle)}</span></a>'
        pager = f'<div class="chapter-pager">{prev_html}{next_html}</div>'

        page_html = render_shell(slug, chap_label, title, body_html, toc_items, pager, has_plotly=bool(lab_id))
        with open(os.path.join(DOCS_DIR, f"{slug}.html"), "w", encoding="utf-8") as out:
            out.write(page_html)

    # Build landing page index.html with live interactive Black-Scholes hero lab
    cards_main = []
    cards_app = []
    for slug, _, chap_label, chap_num, title, desc, lab_id in PAGES:
        badge = " &middot; Interactive Lab" if lab_id else ""
        card = f'<a class="chapter-card" href="{slug}.html"><div class="c-num">{html.escape(chap_label)}{badge}</div><div class="c-title">{html.escape(title)}</div><div class="c-desc">{html.escape(desc)}</div></a>'
        if slug.startswith("ch"):
            cards_main.append(card)
        else:
            cards_app.append(card)

    hero_body = f"""
    <div class="hero">
      <p class="hero-subtitle">A modern, self-contained monograph on mathematical finance and derivatives pricing—spanning discrete trees, Itô &amp; rough calculus, Black–Scholes, SVI &amp; rough volatility, exotic &amp; American options, post-LIBOR SOFR multi-curve interest rates, and XVA.</p>
      <div class="hero-cta">
        <a class="btn-pill primary" href="ch01.html">Start Reading (Chapter 1)</a>
        <a class="btn-pill" href="Essentials_for_Financial_Derivatives.pdf" target="_blank">Download 180-Page PDF (Libertinus)</a>
        <a class="btn-pill" href="https://github.com/Derek-Y-JQ/Essentials_for_Financial_Derivatives/tree/main/code" target="_blank">Companion Python Code</a>
      </div>
    </div>
    <section id="lab-4" class="quant-lab"></section>
    <h2>Chapters</h2>
    <div class="chapter-grid">{"".join(cards_main)}</div>
    <h2>Appendices</h2>
    <div class="chapter-grid">{"".join(cards_app)}</div>
    """
    index_html = render_shell("index", "Interactive Web Monograph · Junqi Yin (NUS)", "Essentials for Financial Derivatives", hero_body, [], "", has_plotly=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as out:
        out.write(index_html)

    print(f"Built {len(PAGES) + 1} HTML pages in {DOCS_DIR}/ with {len(label_map)} resolved cross-reference anchors.")


if __name__ == "__main__":
    main()
