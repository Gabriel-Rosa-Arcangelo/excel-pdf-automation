# automation/pdf.py
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, Image
)
from reportlab.graphics.shapes import Drawing, Rect

# Charts via matplotlib (rápido/estável)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ========== TEMA DARK ==========
C_BG_DARK   = "#0B0F19"   # fundo principal (bem escuro)
C_PANEL_BG  = "#111827"   # cards painéis
C_PANEL_ST  = "#374151"   # borda card
C_TEXT      = colors.HexColor("#E5E7EB")  # texto principal (cinza claro)
C_TEXT_MUT  = colors.HexColor("#9CA3AF")  # texto secundário
C_ACCENT    = "#7C3AED"   # roxo (accent)
C_CYAN      = "#38B2AC"   # ciano secundário

# estilos (leves para caber em 1 página)
H1 = ParagraphStyle("H1", fontSize=16, textColor=C_TEXT, spaceAfter=6, leading=20)
H2 = ParagraphStyle("H2", fontSize=11, textColor=colors.HexColor(C_ACCENT), spaceAfter=4, leading=15)
P  = ParagraphStyle("P",  fontSize=9,  textColor=C_TEXT, leading=12)

# ======== fundo escuro na página =========
def _draw_dark_background(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(colors.HexColor(C_BG_DARK))
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    # rodapé discreto (marca)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(12 * mm, 10 * mm, "D’Angelo DevStudio — Automated Report")
    canvas.restoreState()

# ===== Helpers UI =====
def _cover(story, title, subtitle="Automated Excel → PDF report", meta=None):
    story.append(Paragraph(title, H1))
    story.append(Paragraph(subtitle, H2))
    info = f"Generated at: {datetime.now():%Y-%m-%d %H:%M}"
    if meta:
        info += f" — Rows: <b>{meta.get('rows','-')}</b> • Columns: <b>{meta.get('cols','-')}</b>"
    story.append(Paragraph(info, P))
    story.append(Spacer(1, 6))

def _metric_card(title, value, width=38*mm, height=20*mm):
    d = Drawing(width, height)
    d.add(Rect(0, 0, width, height,
               fillColor=colors.HexColor(C_PANEL_BG),
               strokeColor=colors.HexColor(C_PANEL_ST),
               strokeWidth=0.4, radius=5))
    from reportlab.graphics.shapes import String
    d.add(String(6, height-8, title, fontName="Helvetica", fontSize=8,
             fillColor=C_TEXT_MUT))
    d.add(String(6, height-24, str(value), fontName="Helvetica-Bold", fontSize=12,
                fillColor=C_TEXT))

    return d

def _summary_cards(story, stats):
    cards = [
        _metric_card("Rows", stats.get("rows","-")),
        _metric_card("Min value", stats.get("min","-")),
        _metric_card("Max value", stats.get("max","-")),
        _metric_card("Avg value", stats.get("avg","-")),
    ]
    t = Table([cards], colWidths=[42*mm]*4)  # 42*4=168mm < 170mm útil
    t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

def _short(s, n=10):
    s = str(s)
    return s if len(s) <= n else s[:n-1] + "…"

# ===== Largura útil e proporções (1 página, sem distorção) =====
PAGE_IMG_W_MM = 150.0   # 150mm p/ sobrar espaço a textos
BAR_ASPECT    = 6.4 / 3.0
PIE_ASPECT    = 6.4 / 3.4   # pizza um pouco mais “alta” (maior), sem distorcer

# ===== Gráficos matplotlib em modo dark =====
def _setup_dark_axes(fig, ax):
    fig.patch.set_facecolor(C_BG_DARK)
    ax.set_facecolor(C_BG_DARK)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#4B5563")  # cinza médio

def _render_bar_png(pairs, title="Top values"):
    labels = [_short(p[0]) for p in pairs]
    values = [float(p[1]) for p in pairs]
    fig_w_in, fig_h_in, dpi = 6.4, 3.0, 180
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=dpi)
    _setup_dark_axes(fig, ax)
    bars = ax.bar(labels, values, color=C_CYAN, edgecolor="#94A3B8", linewidth=0.6)
    ax.set_title(title, color=C_ACCENT, fontsize=10, pad=6)
    ax.tick_params(axis='x', labelrotation=0, labelsize=8, colors="#E5E7EB")
    ax.tick_params(axis='y', colors="#E5E7EB")
    ax.grid(axis='y', linestyle=':', linewidth=0.6, alpha=0.5, color="#6B7280")
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", facecolor=C_BG_DARK); plt.close(fig); buf.seek(0)
    buf._aspect = fig_w_in / fig_h_in
    return buf

def _render_pie_png(labels, values, title="Distribution"):
    total = float(sum(values)) if values else 0.0
    # pizza maior (altura/fig_h_in maior)
    fig_w_in, fig_h_in, dpi = 6.4, 3.4, 180
    fig, ax = plt.subplots(figsize=(fig_w_in, fig_h_in), dpi=dpi)
    fig.patch.set_facecolor(C_BG_DARK)
    ax.set_facecolor(C_BG_DARK)

    if total > 0:
        autopct = lambda pct: f"{pct:.1f}%"
        colors_pal = [C_ACCENT, C_CYAN, "#49BFB7", "#3D9BCB", "#2F78AD"]
        wedges, texts, autotexts = ax.pie(
            values,
            labels=[_short(l, 12) for l in labels],
            autopct=autopct, startangle=90,
            colors=colors_pal, pctdistance=0.8,
            textprops={'fontsize':8, 'color':"#E5E7EB"}
        )
        for t in autotexts: t.set_color("#F9FAFB")
    ax.set_title(title, color=C_ACCENT, fontsize=10, pad=6)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", facecolor=C_BG_DARK); plt.close(fig); buf.seek(0)
    buf._aspect = fig_w_in / fig_h_in
    return buf

# ===== Builder principal (1 página) =====
def build_pdf_enhanced(path_or_buffer, title, df, top_n=6):
    """
    1 página (dark):
      • Capa + cards
      • Texto mais detalhado (2-3 frases)
      • Bar (Top N) + Pie (faixas), ambos dark e sem distorção
    """
    doc = SimpleDocTemplate(
        path_or_buffer, pagesize=A4,
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )

    story = []

    # Meta & stats
    meta = {"rows": len(df.index), "cols": len(df.columns)}
    stats = {"rows": meta["rows"], "min": "-", "max": "-", "avg": "-"}
    label_col = "sample_id" if "sample_id" in df.columns else (df.columns[0] if len(df.columns) else "item")

    fv = None
    if "value" in df.columns:
        try:
            fv = df["value"].astype(float)
            stats["min"] = round(fv.min(), 2)
            stats["max"] = round(fv.max(), 2)
            stats["avg"] = round(fv.mean(), 2)
        except Exception:
            pass

    # Capa + cards
    _cover(story, title, meta=meta)
    _summary_cards(story, stats)

    # Texto explicativo (mais rico, mas curto para caber)
    bullets = []
    bullets.append("This one page report gives an executive overview of the uploaded dataset, focusing on what matters for decision making.")
    bullets.append("We present the top entries by ‘value’ and how all rows distribute across value ranges, highlighting extremes and central tendency.")
    if stats["avg"] != "-":
        bullets.append(f"Summary: avg <b>{stats['avg']}</b>, min <b>{stats['min']}</b>, max <b>{stats['max']}</b>.")
    story.append(Paragraph(" ".join(bullets), P))
    story.append(Spacer(1, 5))

    # BAR: Top N
    if fv is not None:
        tmp = df[[label_col, "value"]].copy()
        tmp["value"] = tmp["value"].astype(float)
        tmp = tmp.sort_values("value", ascending=False).head(top_n)
        pairs = list(zip(tmp[label_col].astype(str), tmp["value"].tolist()))
        bar_png = _render_bar_png(pairs, title=f"Top {top_n} by value")
        bar_w_mm = PAGE_IMG_W_MM
        bar_h_mm = bar_w_mm / (bar_png._aspect)
        story.append(Paragraph("Top items by ‘value’. Use it to spot outliers and best performers at a glance.", P))
        story.append(KeepTogether([Image(bar_png, width=bar_w_mm*mm, height=bar_h_mm*mm)]))
        story.append(Spacer(1, 4))

    # PIE: 4 faixas
    if fv is not None and len(fv):
        vmin, vmax = float(fv.min()), float(fv.max())
        rng = max(1.0, vmax - vmin); step = rng / 4.0
        edges = [vmin, vmin+step, vmin+2*step, vmin+3*step, vmax]
        labels = [f"{edges[i]:.1f}–{edges[i+1]:.1f}" for i in range(4)]
        counts = []
        for i in range(4):
            if i < 3: counts.append(int(((fv >= edges[i]) & (fv <  edges[i+1])).sum()))
            else:     counts.append(int(((fv >= edges[i]) & (fv <= edges[i+1])).sum()))
        pie_png = _render_pie_png(labels, counts, title="Value distribution (bins)")
        pie_w_mm = PAGE_IMG_W_MM
        pie_h_mm = pie_w_mm / (pie_png._aspect)
        story.append(Paragraph("Distribution across value ranges. Quickly assess concentration vs dispersion.", P))
        story.append(KeepTogether([Image(pie_png, width=pie_w_mm*mm, height=pie_h_mm*mm)]))

    # Monta 1 página com fundo dark
    doc.build(story, onFirstPage=_draw_dark_background, onLaterPages=_draw_dark_background)
