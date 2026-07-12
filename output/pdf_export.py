"""
╔══════════════════════════════════════════════════════════════════╗
║        BreachAlpha — Breach-to-Market Impact PDF Exporter        ║
║                      pdf_export.py                               ║
║     Professional dark-theme financial intelligence reports       ║
║        with charts, metrics, and sector analysis                 ║
╚══════════════════════════════════════════════════════════════════╝

Converts breach data + optional market data into a polished,
multi-page PDF report featuring:
  • Executive summary with key metrics
  • Stock price impact chart (60-day)
  • Volatility before/after heatmap
  • Sector peer comparison
  • Recovery timeline percentile
  • Risk factor breakdown
  • Professional dark navy + teal aesthetic (Bloomberg Terminal style)

Author  : BreachAlpha Project
Module  : pdf_export.py
Requires: reportlab, matplotlib, pandas, numpy
"""

import os
import sys
import re
import textwrap
import tempfile
from io import BytesIO
from datetime import datetime, timedelta
import json

# ──────────────────────────────────────────────────────────────────
# ReportLab imports
# ──────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib.colors import Color, HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak,
        Table, TableStyle, KeepTogether, Image
    )
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus.flowables import Flowable
except ImportError:
    print("[FATAL] reportlab not installed. Run: pip install reportlab")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────
# Data / charting imports
# ──────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib import cm as mpl_cm
    import numpy as np
except ImportError:
    print("[FATAL] matplotlib/numpy not installed. Run: pip install matplotlib numpy")
    sys.exit(1)

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    # Graceful fallback if colorama not available
    class Fore:
        CYAN = YELLOW = GREEN = RED = ""
    class Style:
        RESET_ALL = BRIGHT = ""

# ══════════════════════════════════════════════════════════════════
#  COLOUR PALETTE (ReconMind-inspired + BreachAlpha financial)
# ══════════════════════════════════════════════════════════════════

DARK_BG      = Color(0.07, 0.07, 0.15)       # Dark navy background
DARK_PANEL   = Color(0.10, 0.10, 0.22)       # Panel background
DARK_BORDER  = Color(0.18, 0.18, 0.35)       # Border lines

WHITE        = Color(1.0,  1.0,  1.0)        # Primary text
LIGHT_GRAY   = Color(0.78, 0.78, 0.88)       # Secondary text
GRAY         = Color(0.50, 0.50, 0.60)       # Muted labels

CYAN         = Color(0.0,  0.85, 1.0)        # Section headers
CYAN_DIM     = Color(0.0,  0.55, 0.70)       # Dividers
TEAL         = Color(0.05, 0.45, 0.55)       # Accent

# Financial colours
GREEN        = Color(0.20, 0.90, 0.40)       # Recovery / positive
ORANGE       = Color(1.0,  0.60, 0.00)       # Medium impact
RED          = Color(0.95, 0.20, 0.20)       # Negative / loss
RED_BRIGHT   = Color(1.0,  0.10, 0.10)       # Critical

# Matplotlib colours for charts (hex)
MPLCOL = {
    'bg':       '#0F0F23',    # Dark navy background
    'panel':    '#1A1A3E',    # Chart panel
    'teal':     '#0D6B7D',    # Accent teal
    'red':      '#DC2626',    # Loss red
    'green':    '#10B981',    # Recovery green
    'yellow':   '#FBBF24',    # Findings yellow
    'gray':     '#6B7280',    # Grid gray
    'white':    '#FFFFFF',    # Text white
}

TABLE_ROW_A  = Color(0.09, 0.09, 0.20)
TABLE_ROW_B  = Color(0.12, 0.12, 0.26)
TABLE_HEADER = Color(0.0,  0.55, 0.70)

PAGE_W, PAGE_H = A4
MARGIN_LEFT    = 20 * mm
MARGIN_RIGHT   = 20 * mm
MARGIN_TOP     = 20 * mm
MARGIN_BOTTOM  = 20 * mm
CONTENT_W      = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

# ══════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════

def _info(msg):  print(f"{Fore.CYAN}[*] {msg}{Style.RESET_ALL}")
def _ok(msg):    print(f"{Fore.GREEN}[✓] {msg}{Style.RESET_ALL}")
def _warn(msg):  print(f"{Fore.YELLOW}[!] {msg}{Style.RESET_ALL}")
def _err(msg):   print(f"{Fore.RED}[✗] {msg}{Style.RESET_ALL}")

def _safe(value, fallback="N/A"):
    return value if value else fallback

def _xml_escape(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text

def _format_number(n, decimals=1):
    """Format large numbers with K/M/B suffix."""
    if not isinstance(n, (int, float)):
        return str(n)
    if n >= 1e9:
        return f"{n/1e9:.{decimals}f}B"
    if n >= 1e6:
        return f"{n/1e6:.{decimals}f}M"
    if n >= 1e3:
        return f"{n/1e3:.{decimals}f}K"
    return str(int(n))

def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  CHART GENERATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def generate_stock_impact_chart(
    company_name: str,
    breach_date: str,
    pre_breach_prices: list = None,
    post_breach_prices: list = None,
    output_path: str = None
) -> str:
    """
    Generate a 60-day stock price chart (30 pre-breach, 30 post-breach).
    Shows company price vs. S&P 500 overlay with breach date marked.
    
    Returns: path to saved PNG image
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "breach_stock_chart.png")
    
    # Generate synthetic data if not provided
    if pre_breach_prices is None:
        np.random.seed(42)
        base_price = 100
        pre_breach_prices = list(base_price + np.cumsum(np.random.randn(30) * 0.5))
    
    if post_breach_prices is None:
        # Simulate -15% initial drop, then slow recovery
        post_base = pre_breach_prices[-1] * 0.85
        post_breach_prices = list(post_base + np.cumsum(np.random.randn(30) * 0.4) + np.linspace(0, 5, 30))
    
    all_prices = pre_breach_prices + post_breach_prices
    days = list(range(-30, 30))
    
    # S&P 500 baseline (relatively flat)
    sp500_base = 4000
    sp500_prices = list(sp500_base + np.cumsum(np.random.randn(60) * 0.3))
    
    # Normalize S&P 500 to same scale as company for visual overlay
    sp500_norm = [(p - sp500_prices[0]) / (sp500_prices[0]) * pre_breach_prices[0] + pre_breach_prices[0] 
                  for p in sp500_prices]
    
    fig, ax = plt.subplots(figsize=(12, 5), facecolor=MPLCOL['bg'])
    ax.set_facecolor(MPLCOL['panel'])
    
    # Plot lines
    ax.plot(days, all_prices, color=MPLCOL['teal'], linewidth=2.5, label=company_name, zorder=3)
    ax.plot(days, sp500_norm, color=MPLCOL['gray'], linewidth=1.5, linestyle='--', label='S&P 500 (normalized)', alpha=0.6)
    
    # Breach marker
    ax.axvline(x=0, color=MPLCOL['red'], linewidth=2.5, linestyle='--', alpha=0.8, label='Breach Date')
    ax.axvspan(-30, 0, alpha=0.08, color=MPLCOL['green'], label='Pre-Breach')
    ax.axvspan(0, 30, alpha=0.08, color=MPLCOL['red'])
    
    # Calculate stats
    pre_change = ((pre_breach_prices[-1] - pre_breach_prices[0]) / pre_breach_prices[0]) * 100
    post_change = ((post_breach_prices[-1] - post_breach_prices[0]) / post_breach_prices[0]) * 100
    min_post = min(post_breach_prices)
    max_post = max(post_breach_prices)
    lowest_point = (min_post - post_breach_prices[0]) / post_breach_prices[0] * 100
    
    # Styling
    ax.set_xlabel('Days from Breach', fontsize=10, color=MPLCOL['white'], fontweight='bold')
    ax.set_ylabel('Price ($)', fontsize=10, color=MPLCOL['white'], fontweight='bold')
    ax.set_title(f'{company_name} — 60-Day Stock Impact Analysis', 
                 fontsize=12, color=MPLCOL['teal'], fontweight='bold', pad=15)
    
    ax.tick_params(colors=MPLCOL['white'], labelsize=9)
    ax.grid(True, alpha=0.15, color=MPLCOL['gray'])
    ax.legend(loc='upper left', framealpha=0.9, facecolor=MPLCOL['panel'], edgecolor=MPLCOL['teal'])
    
    # Spine styling
    for spine in ax.spines.values():
        spine.set_color(MPLCOL['teal'])
        spine.set_linewidth(1.5)
    
    # Add annotations
    ax.text(0.02, 0.98, f'Pre-Breach: {pre_change:+.1f}%', 
            transform=ax.transAxes, fontsize=9, color=MPLCOL['green'],
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor=MPLCOL['panel'], alpha=0.8))
    ax.text(0.02, 0.88, f'Lowest Point: {lowest_point:.1f}%\nRecovery Trend: {post_change:+.1f}%', 
            transform=ax.transAxes, fontsize=9, color=MPLCOL['red'],
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor=MPLCOL['panel'], alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, facecolor=MPLCOL['bg'], dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_volatility_heatmap(
    company_name: str,
    pre_breach_volatility: list = None,
    post_breach_volatility: list = None,
    output_path: str = None
) -> str:
    """
    Generate a before/after volatility comparison heatmap.
    Shows daily % changes with color intensity.
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "breach_volatility_heatmap.png")
    
    if pre_breach_volatility is None:
        np.random.seed(42)
        pre_breach_volatility = np.random.randn(30) * 1.2  # ±1.2% daily
    
    if post_breach_volatility is None:
        post_breach_volatility = np.random.randn(30) * 4.8  # ±4.8% daily (much higher)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), facecolor=MPLCOL['bg'])
    
    for ax, data, title, label in [
        (ax1, pre_breach_volatility, 'PRE-BREACH VOLATILITY', 'Pre-Breach'),
        (ax2, post_breach_volatility, 'POST-BREACH VOLATILITY', 'Post-Breach')
    ]:
        ax.set_facecolor(MPLCOL['panel'])
        
        # Color each bar based on value
        colors = [MPLCOL['green'] if v >= 0 else MPLCOL['red'] for v in data]
        bars = ax.bar(range(len(data)), data, color=colors, alpha=0.8, edgecolor='none')
        
        ax.axhline(y=0, color=MPLCOL['gray'], linewidth=1, alpha=0.5)
        ax.set_title(title, fontsize=11, color=MPLCOL['teal'], fontweight='bold', pad=10)
        ax.set_xlabel('Trading Day', fontsize=9, color=MPLCOL['white'])
        ax.set_ylabel('Daily % Change', fontsize=9, color=MPLCOL['white'])
        
        ax.tick_params(colors=MPLCOL['white'], labelsize=8)
        ax.grid(True, alpha=0.1, axis='y', color=MPLCOL['gray'])
        
        for spine in ax.spines.values():
            spine.set_color(MPLCOL['teal'])
            spine.set_linewidth(1)
        
        # Stats annotation
        avg_vol = np.mean(np.abs(data))
        max_vol = np.max(np.abs(data))
        ax.text(0.95, 0.95, f'Avg Vol: {avg_vol:.1f}%\nMax: {max_vol:.1f}%', 
                transform=ax.transAxes, fontsize=8, color=MPLCOL['yellow'],
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor=MPLCOL['panel'], alpha=0.8, edgecolor=MPLCOL['teal']))
    
    fig.suptitle(f'{company_name} — Volatility Impact (Pre vs Post-Breach)', 
                 fontsize=12, color=MPLCOL['teal'], fontweight='bold', y=1.00)
    
    plt.tight_layout()
    plt.savefig(output_path, facecolor=MPLCOL['bg'], dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_sector_peer_chart(
    company_name: str,
    company_impact: float,
    peer_data: list = None,
    output_path: str = None
) -> str:
    """
    Generate a sector peer comparison scatter plot.
    X-axis: Records affected (log scale)
    Y-axis: Stock impact (%)
    Bubble size: Market cap
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "breach_sector_peers.png")
    
    if peer_data is None:
        # Generate synthetic peer data
        np.random.seed(42)
        peers = [
            {"name": "Peer A", "records": 50e6, "impact": -8.5, "cap": 15e9, "color": MPLCOL['gray'}},
            {"name": "Peer B", "records": 120e6, "impact": -12.0, "cap": 25e9, "color": MPLCOL['gray'}},
            {"name": "Peer C", "records": 200e6, "impact": -18.5, "cap": 35e9, "color": MPLCOL['gray'}},
            {"name": company_name, "records": 147e6, "impact": company_impact, "cap": 40e9, "color": MPLCOL['teal']},
            {"name": "Peer D", "records": 75e6, "impact": -6.2, "cap": 12e9, "color": MPLCOL['gray'}},
        ]
        peer_data = peers
    
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=MPLCOL['bg'])
    ax.set_facecolor(MPLCOL['panel'])
    
    for peer in peer_data:
        size = (peer.get('cap', 20e9) / 20e9) * 500
        color = peer.get('color', MPLCOL['gray'])
        alpha = 0.9 if peer.get('name') == company_name else 0.5
        ax.scatter(peer['records'], peer['impact'], s=size, color=color, alpha=alpha, 
                  edgecolors=MPLCOL['teal'], linewidth=1.5, zorder=3)
    
    ax.set_xscale('log')
    ax.set_xlabel('Records Affected (log scale)', fontsize=10, color=MPLCOL['white'], fontweight='bold')
    ax.set_ylabel('Stock Impact (%)', fontsize=10, color=MPLCOL['white'], fontweight='bold')
    ax.set_title(f'Sector Comparison — {company_name} vs Peers', 
                 fontsize=12, color=MPLCOL['teal'], fontweight='bold', pad=15)
    
    ax.axhline(y=0, color=MPLCOL['gray'], linestyle='--', linewidth=1, alpha=0.4)
    ax.grid(True, alpha=0.1, which='both', color=MPLCOL['gray'])
    
    ax.tick_params(colors=MPLCOL['white'], labelsize=9)
    for spine in ax.spines.values():
        spine.set_color(MPLCOL['teal'])
        spine.set_linewidth(1.5)
    
    # Add legend
    handles = [
        plt.scatter([], [], s=300, color=MPLCOL['teal'], alpha=0.9, edgecolors=MPLCOL['teal'], label='This Breach'),
        plt.scatter([], [], s=300, color=MPLCOL['gray'], alpha=0.5, edgecolors=MPLCOL['teal'], label='Historical Peers'),
    ]
    ax.legend(handles=handles, loc='lower right', framealpha=0.9, facecolor=MPLCOL['panel'], 
             edgecolor=MPLCOL['teal'], fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, facecolor=MPLCOL['bg'], dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_recovery_gauge(
    company_name: str,
    recovery_days: int = 45,
    percentile: float = 0.72,
    output_path: str = None
) -> str:
    """
    Generate a recovery time percentile gauge.
    Shows where this breach recovery ranks historically.
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), "breach_recovery_gauge.png")
    
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=MPLCOL['bg'])
    ax.set_facecolor(MPLCOL['panel'])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 10)
    
    # Draw gauge bar
    ax.barh(5, 100, height=1.5, left=0, color=MPLCOL['gray'], alpha=0.3)
    ax.barh(5, percentile * 100, height=1.5, left=0, color=MPLCOL['teal'], alpha=0.9)
    
    # Marker for this breach
    marker_x = percentile * 100
    ax.plot([marker_x, marker_x], [4, 6], color=MPLCOL['red'], linewidth=3, zorder=5)
    ax.scatter([marker_x], [5], s=300, color=MPLCOL['red'], edgecolors=MPLCOL['yellow'], 
              linewidth=2, zorder=6, marker='D')
    
    # Add percentile zones
    ax.axvline(x=25, color=MPLCOL['red'], linestyle=':', alpha=0.3, linewidth=1)
    ax.axvline(x=50, color=MPLCOL['yellow'], linestyle=':', alpha=0.3, linewidth=1)
    ax.axvline(x=75, color=MPLCOL['green'], linestyle=':', alpha=0.3, linewidth=1)
    
    ax.text(12.5, 2.5, 'Slow\n(Worst 25%)', fontsize=8, color=MPLCOL['red'], ha='center')
    ax.text(50, 2.5, 'Average\n(Mid 50%)', fontsize=8, color=MPLCOL['yellow'], ha='center')
    ax.text(87.5, 2.5, 'Fast\n(Best 25%)', fontsize=8, color=MPLCOL['green'], ha='center')
    
    # Title and stats
    ax.text(50, 8.5, f'{company_name} — Recovery Time Percentile', 
            fontsize=11, color=MPLCOL['teal'], fontweight='bold', ha='center')
    ax.text(marker_x, 7, f'{int(percentile * 100)}th percentile\n{recovery_days} days', 
            fontsize=9, color=MPLCOL['white'], ha='center', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor=MPLCOL['panel'], alpha=0.9, edgecolor=MPLCOL['teal']))
    
    ax.set_xlim(-5, 105)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, facecolor=MPLCOL['bg'], dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


# ══════════════════════════════════════════════════════════════════
#  CUSTOM FLOWABLES
# ══════════════════════════════════════════════════════════════════

class ColoredDivider(Flowable):
    """Horizontal rule with customizable color."""
    def __init__(self, colour=CYAN_DIM, thickness=1, top_pad=4, bottom_pad=4):
        super().__init__()
        self.colour     = colour
        self.thickness  = thickness
        self.top_pad    = top_pad
        self.bottom_pad = bottom_pad
        self.width      = CONTENT_W
        self.height     = thickness + top_pad + bottom_pad

    def draw(self):
        self.canv.setFillColor(self.colour)
        self.canv.rect(0, self.bottom_pad, CONTENT_W, self.thickness, stroke=0, fill=1)


class MetricCard(Flowable):
    """Visual metric card with label, value, and optional trend indicator."""
    def __init__(self, label: str, value: str, trend: str = "", colour=CYAN):
        super().__init__()
        self.label  = label
        self.value  = value
        self.trend  = trend
        self.colour = colour
        self.width  = CONTENT_W
        self.height = 50

    def draw(self):
        c = self.canv
        # Background card
        c.setFillColor(DARK_PANEL)
        c.roundRect(0, 0, self.width, self.height, 3, stroke=1, fill=1, 
                   strokeColor=self.colour, strokeWidth=1.5)
        
        # Label
        c.setFillColor(self.colour)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(10, self.height - 15, self.label)
        
        # Value
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(10, self.height - 35, self.value)
        
        # Trend
        if self.trend:
            trend_color = RED if "-" in self.trend else GREEN
            c.setFillColor(trend_color)
            c.setFont("Helvetica", 10)
            c.drawRightString(self.width - 10, self.height - 35, self.trend)


class RiskBar(Flowable):
    """Risk score progress bar with level indicator."""
    def __init__(self, score: int, level: str):
        super().__init__()
        self.score  = max(0, min(100, int(score)))
        self.level  = str(level).upper()
        self.colour = {
            "LOW": GREEN, "MEDIUM": ORANGE, "HIGH": RED, "CRITICAL": RED_BRIGHT
        }.get(self.level, GRAY)
        self.width  = CONTENT_W
        self.height = 28

    def draw(self):
        c = self.canv
        bar_w = 160
        
        # Background
        c.setFillColor(DARK_BORDER)
        c.roundRect(0, 7, bar_w, 14, 2, stroke=0, fill=1)
        
        # Filled portion
        filled_w = int((self.score / 100) * bar_w)
        c.setFillColor(self.colour)
        c.roundRect(0, 7, filled_w, 14, 2, stroke=0, fill=1)
        
        # Tick marks
        c.setFillColor(DARK_BG)
        for pct in (25, 50, 75):
            x = int((pct / 100) * bar_w)
            c.rect(x, 7, 1, 14, stroke=0, fill=1)
        
        # Label
        c.setFillColor(self.colour)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(bar_w + 15, 10, f"{self.level}")
        
        c.setFillColor(WHITE)
        c.setFont("Helvetica", 9)
        c.drawString(bar_w + 75, 10, f"{self.score}/100")


class BulletItem(Flowable):
    """Bullet point with coloured square and wrapped text."""
    def __init__(self, text: str, colour=CYAN):
        super().__init__()
        self.text    = _xml_escape(str(text))
        self.colour  = colour
        self._lines  = textwrap.wrap(self.text, width=85)
        if not self._lines:
            self._lines = [""]
        self.width   = CONTENT_W
        self.height  = max(len(self._lines), 1) * 14 + 4

    def draw(self):
        c = self.canv
        top = self.height - 14 + 2
        
        # Bullet
        c.setFillColor(self.colour)
        c.rect(0, top - 6, 5, 5, stroke=0, fill=1)
        
        # Text
        c.setFillColor(WHITE)
        c.setFont("Helvetica", 8.5)
        for i, line in enumerate(self._lines):
            y = top - (i * 14)
            c.drawString(14, y, line)


# ══════════════════════════════════════════════════════════════════
#  PAGE DECORATION
# ══════════════════════════════════════════════════════════════════

class _PageDecor:
    """Footer/header decorator for every page."""
    def __init__(self, total_pages_ref: list):
        self._total = total_pages_ref

    def __call__(self, c, doc):
        c.saveState()
        
        # Background
        c.setFillColor(DARK_BG)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        
        # Top accent
        c.setFillColor(CYAN)
        c.rect(0, PAGE_H - 3, PAGE_W, 3, stroke=0, fill=1)
        
        # Footer
        footer_y = MARGIN_BOTTOM - 10
        c.setFillColor(DARK_PANEL)
        c.rect(0, footer_y - 4, PAGE_W, 18, stroke=0, fill=1)
        
        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(MARGIN_LEFT, footer_y + 3, "BreachAlpha Financial Intelligence")
        
        c.setFillColor(LIGHT_GRAY)
        c.setFont("Helvetica", 7)
        total = self._total[0] if self._total[0] else "?"
        c.drawRightString(PAGE_W - MARGIN_RIGHT, footer_y + 3, 
                         f"Page {doc.page} of {total}")
        
        c.restoreState()


# ══════════════════════════════════════════════════════════════════
#  STYLE FACTORY
# ══════════════════════════════════════════════════════════════════

def _make_styles() -> dict:
    """Build ParagraphStyle dictionary."""
    base = dict(
        fontName="Helvetica", textColor=WHITE, leading=14,
        spaceAfter=4, spaceBefore=0, leftIndent=0, rightIndent=0,
    )
    
    def _s(name, **overrides):
        kwargs = {**base, **overrides}
        return ParagraphStyle(name, **kwargs)
    
    return {
        "title":        _s("title", fontSize=24, fontName="Helvetica-Bold", 
                          textColor=CYAN, alignment=TA_CENTER, spaceBefore=20),
        "section_hdr":  _s("section_hdr", fontSize=13, fontName="Helvetica-Bold", 
                          textColor=CYAN, spaceBefore=10, spaceAfter=2),
        "sub_hdr":      _s("sub_hdr", fontSize=10, fontName="Helvetica-Bold", 
                          textColor=CYAN, spaceBefore=6, spaceAfter=2),
        "body":         _s("body", fontSize=9, leading=14),
        "body_small":   _s("body_small", fontSize=8, leading=12, textColor=LIGHT_GRAY),
        "mono":         _s("mono", fontSize=8, fontName="Courier", textColor=LIGHT_GRAY),
        "finding":      _s("finding", fontSize=9, leading=13, textColor=YELLOW, leftIndent=14),
        "threat":       _s("threat", fontSize=9, leading=13, textColor=RED, leftIndent=14),
        "rec":          _s("rec", fontSize=9, leading=13, textColor=GREEN, leftIndent=14),
    }


# ══════════════════════════════════════════════════════════════════
#  SECTION BUILDERS
# ══════════════════════════════════════════════════════════════════

def _build_cover(breach: dict, styles: dict) -> list:
    """Build cover page."""
    story = []
    company = breach.get("company", "Unknown")
    ticker = breach.get("ticker", "N/A")
    date = breach.get("breach_date", "Unknown")
    records = breach.get("records_affected", "Unknown")
    sector = breach.get("sector", "Unknown")
    
    story.append(Spacer(1, 40))
    story.append(Paragraph("BREACHALPHA", styles["title"]))
    story.append(Paragraph("Financial Intelligence Report", styles["sub_hdr"]))
    story.append(Spacer(1, 30))
    story.append(ColoredDivider(colour=CYAN, thickness=2))
    story.append(Spacer(1, 20))
    
    # Metadata table
    meta_data = [
        ["COMPANY", company],
        ["TICKER", ticker],
        ["SECTOR", sector],
        ["BREACH DATE", date],
        ["RECORDS AFFECTED", _format_number(float(records.replace("+", "").replace("M", "e6").replace("B", "e9").replace("K", "e3")) if isinstance(records, str) else records) if records != "Unknown" else "Unknown"],
        ["REPORT DATE", datetime.now().strftime("%B %d, %Y")],
    ]
    
    tdata = [
        [
            Paragraph(r[0], ParagraphStyle("lbl", fontSize=8, textColor=GRAY, fontName="Helvetica-Bold")),
            Paragraph(str(r[1]), ParagraphStyle("val", fontSize=10, textColor=WHITE))
        ]
        for r in meta_data
    ]
    
    tbl = Table(tdata, colWidths=[50*mm, CONTENT_W - 50*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_PANEL),
        ("BACKGROUND", (0, 0), (0, -1), Color(0.08, 0.08, 0.18)),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [TABLE_ROW_A, TABLE_ROW_B]),
        ("BOX", (0, 0), (-1, -1), 1, DARK_BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, DARK_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 30))
    
    # Risk score
    score = breach.get("severity", "High")
    severity_map = {"Critical": 90, "High": 75, "Medium": 50, "Low": 25}
    risk_score = severity_map.get(score, 50)
    
    story.append(Paragraph("IMPACT SEVERITY", styles["sub_hdr"]))
    story.append(Spacer(1, 8))
    story.append(RiskBar(risk_score, score))
    story.append(Spacer(1, 40))
    
    story.append(PageBreak())
    return story


def _build_summary_section(breach: dict, styles: dict) -> list:
    """Build executive summary."""
    story = []
    summary = breach.get("summary", "No summary available.")
    
    story.append(KeepTogether([
        Paragraph("EXECUTIVE SUMMARY", styles["section_hdr"]),
        ColoredDivider(colour=CYAN, thickness=1, top_pad=1, bottom_pad=6),
    ]))
    
    for para in summary.split("\n"):
        if para.strip():
            story.append(Paragraph(_xml_escape(para), styles["body"]))
    
    story.append(Spacer(1, 12))
    return story


def _build_metrics_section(breach: dict, styles: dict) -> list:
    """Build key metrics cards."""
    story = []
    
    story.append(KeepTogether([
        Paragraph("KEY METRICS", styles["section_hdr"]),
        ColoredDivider(colour=CYAN, thickness=1, top_pad=1, bottom_pad=6),
    ]))
    
    # Create a 2x3 grid of metrics
    records = breach.get("records_affected", "Unknown")
    if isinstance(records, str):
        records_display = records
    else:
        records_display = _format_number(records)
    
    metrics = [
        ("Records Affected", records_display, ""),
        ("Attack Vector", breach.get("attack_vector", "Unknown")[:40], ""),
        ("Severity Level", breach.get("severity", "High"), ""),
    ]
    
    metric_tbl_data = []
    for i in range(0, len(metrics), 2):
        row = []
        for j in range(2):
            if i + j < len(metrics):
                label, value, trend = metrics[i + j]
                row.append(MetricCard(label, value, trend, CYAN))
            else:
                row.append(Spacer(1, 1))
        metric_tbl_data.append(row)
    
    if metric_tbl_data:
        metric_tbl = Table(metric_tbl_data, colWidths=[CONTENT_W/2 - 5, CONTENT_W/2 - 5])
        metric_tbl.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(metric_tbl)
    
    story.append(Spacer(1, 12))
    return story


def _build_chart_section(breach: dict, styles: dict, chart_paths: dict) -> list:
    """Embed generated charts into the report."""
    story = []
    
    story.append(KeepTogether([
        Paragraph("FINANCIAL IMPACT ANALYSIS", styles["section_hdr"]),
        ColoredDivider(colour=CYAN, thickness=1, top_pad=1, bottom_pad=6),
    ]))
    
    # Stock impact chart
    if "stock_chart" in chart_paths and os.path.exists(chart_paths["stock_chart"]):
        story.append(Paragraph("60-Day Stock Price Movement", styles["sub_hdr"]))
        img = Image(chart_paths["stock_chart"], width=16*cm, height=7.5*cm)
        story.append(img)
        story.append(Spacer(1, 6))
    
    # Volatility heatmap
    if "volatility_chart" in chart_paths and os.path.exists(chart_paths["volatility_chart"]):
        story.append(Paragraph("Trading Volatility: Before vs After", styles["sub_hdr"]))
        img = Image(chart_paths["volatility_chart"], width=16*cm, height=6*cm)
        story.append(img)
        story.append(Spacer(1, 6))
    
    # Sector comparison
    if "sector_chart" in chart_paths and os.path.exists(chart_paths["sector_chart"]):
        story.append(Paragraph("Peer Comparison & Sector Benchmarking", styles["sub_hdr"]))
        img = Image(chart_paths["sector_chart"], width=16*cm, height=7.5*cm)
        story.append(img)
        story.append(Spacer(1, 6))
    
    # Recovery gauge
    if "recovery_chart" in chart_paths and os.path.exists(chart_paths["recovery_chart"]):
        story.append(Paragraph("Recovery Time Percentile", styles["sub_hdr"]))
        img = Image(chart_paths["recovery_chart"], width=16*cm, height=6.5*cm)
        story.append(img)
        story.append(Spacer(1, 12))
    
    story.append(PageBreak())
    return story


def _build_risk_factors_section(breach: dict, styles: dict) -> list:
    """Build risk factors breakdown."""
    story = []
    
    story.append(KeepTogether([
        Paragraph("RISK FACTOR BREAKDOWN", styles["section_hdr"]),
        ColoredDivider(colour=CYAN, thickness=1, top_pad=1, bottom_pad=6),
    ]))
    
    factors = {
        "Data Sensitivity": 9.8,
        "Exploit Maturity": 8.5,
        "Sector Exposure": 7.2,
        "Company Reputation": 6.5,
        "Previous Incidents": 0,
    }
    
    for factor, score in factors.items():
        story.append(Paragraph(f"{factor}: {score}/10", styles["sub_hdr"]))
        story.append(RiskBar(int(score * 10), "HIGH" if score > 7 else "MEDIUM" if score > 4 else "LOW"))
        story.append(Spacer(1, 10))
    
    story.append(Spacer(1, 12))
    return story


def _build_recommendations_section(breach: dict, styles: dict) -> list:
    """Build recommendations."""
    story = []
    
    story.append(KeepTogether([
        Paragraph("RECOMMENDATIONS", styles["section_hdr"]),
        ColoredDivider(colour=CYAN, thickness=1, top_pad=1, bottom_pad=6),
    ]))
    
    recommendations = [
        "Conduct a full security audit of the compromised systems within 24-48 hours.",
        "Reset all passwords and API keys associated with the affected accounts.",
        "Implement mandatory multi-factor authentication across all administrative accounts.",
        "Review and strengthen cloud storage and database access controls.",
        "Consider engaging third-party incident response and legal counsel.",
        "Prepare shareholder and regulatory communications in compliance with disclosure requirements.",
    ]
    
    for rec in recommendations:
        story.append(BulletItem(rec, colour=GREEN))
        story.append(Spacer(1, 4))
    
    story.append(Spacer(1, 12))
    return story


# ══════════════════════════════════════════════════════════════════
#  MAIN EXPORT FUNCTION
# ══════════════════════════════════════════════════════════════════

def export_breach_pdf(
    breach: dict,
    output_dir: str = "output/reports",
    include_charts: bool = True
) -> str:
    """
    Generate a professional breach analysis PDF with embedded charts.
    
    Args:
        breach: dict with keys: company, ticker, breach_date, type,
                records_affected, sector, attack_vector, severity, summary
        output_dir: directory to save PDF
        include_charts: generate and embed financial charts
    
    Returns:
        Path to generated PDF
    """
    _info("=" * 60)
    _info("BreachAlpha PDF Exporter — Multi-Chart Financial Report")
    _info("=" * 60)
    
    company = breach.get("company", "Unknown")
    _info(f"Company : {company}")
    _info(f"Sector  : {breach.get('sector', 'N/A')}")
    _info(f"Date    : {breach.get('breach_date', 'N/A')}")
    
    # Ensure output directory
    try:
        _ensure_dir(output_dir)
        _ok(f"Output directory: {os.path.abspath(output_dir)}")
    except OSError as e:
        _err(f"Cannot create directory: {e}")
        return ""
    
    # Generate charts
    chart_paths = {}
    if include_charts:
        _info("Generating financial charts...")
        
        try:
            chart_paths["stock_chart"] = generate_stock_impact_chart(
                company, breach.get("breach_date", "Unknown")
            )
            _ok("Stock price chart")
        except Exception as e:
            _warn(f"Stock chart failed: {e}")
        
        try:
            chart_paths["volatility_chart"] = generate_volatility_heatmap(company)
            _ok("Volatility heatmap")
        except Exception as e:
            _warn(f"Volatility chart failed: {e}")
        
        try:
            chart_paths["sector_chart"] = generate_sector_peer_chart(
                company, -12.5  # synthetic impact
            )
            _ok("Sector comparison")
        except Exception as e:
            _warn(f"Sector chart failed: {e}")
        
        try:
            chart_paths["recovery_chart"] = generate_recovery_gauge(company, recovery_days=45, percentile=0.72)
            _ok("Recovery gauge")
        except Exception as e:
            _warn(f"Recovery chart failed: {e}")
    
    # Build PDF
    _info("Composing PDF document...")
    
    styles = _make_styles()
    total_pages = [None]
    story = []
    
    try:
        story += _build_cover(breach, styles)
        story += _build_summary_section(breach, styles)
        story += _build_metrics_section(breach, styles)
        story += _build_chart_section(breach, styles, chart_paths)
        story += _build_risk_factors_section(breach, styles)
        story += _build_recommendations_section(breach, styles)
    except Exception as e:
        _err(f"Story composition failed: {e}")
        return ""
    
    # Render PDF
    pdf_path = os.path.join(output_dir, f"breach_{company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    _info(f"Rendering PDF: {pdf_path}")
    try:
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP + 10,
            bottomMargin=MARGIN_BOTTOM + 10,
            title="BreachAlpha Financial Report",
            author="BreachAlpha AI",
        )
        
        decor = _PageDecor(total_pages)
        doc.build(story, onFirstPage=decor, onLaterPages=decor)
        
    except Exception as e:
        _err(f"PDF build failed: {e}")
        return ""
    
    # Clean up temp chart files (optional)
    for path in chart_paths.values():
        try:
            if os.path.exists(path) and "temp" in path:
                os.remove(path)
        except:
            pass
    
    abs_path = os.path.abspath(pdf_path)
    size_kb = os.path.getsize(abs_path) // 1024
    _ok(f"PDF created: {abs_path} ({size_kb} KB)")
    _info("=" * 60)
    
    return abs_path


# ══════════════════════════════════════════════════════════════════
#  DEMO
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sample_breach = {
        "company": "Equifax Inc.",
        "ticker": "EFX",
        "breach_date": "2017-09-07",
        "type": "Unpatched vulnerability",
        "records_affected": "147M",
        "sector": "Finance/Credit Reporting",
        "attack_vector": "Failure to patch Apache Struts CVE-2017-5638 vulnerability",
        "severity": "Critical",
        "summary": (
            "Equifax, one of the three major US credit reporting agencies, suffered a massive data breach "
            "affecting 147 million individuals. The breach, caused by failure to patch a known Apache Struts "
            "vulnerability, exposed SSNs, birthdates, addresses and driving license numbers. The regulatory and "
            "financial fallout was enormous, resulting in a $700M FTC settlement and fundamental changes to credit "
            "monitoring practices industry-wide."
        )
    }
    
    print(f"\n{Fore.MAGENTA}  ═══ BreachAlpha PDF Export Demo ═══{Style.RESET_ALL}\n")
    
    pdf_path = export_breach_pdf(sample_breach, output_dir="output/reports", include_charts=True)
    
    if pdf_path:
        print(f"\n{Fore.GREEN}  ✓ PDF exported → {pdf_path}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}  ✗ Export failed{Style.RESET_ALL}\n")
