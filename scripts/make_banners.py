"""Generate the animated header and the footer, in dark and light variants.

    python scripts/make_banners.py

Writes assets/header-{dark,light}.svg and assets/footer-{dark,light}.svg.
The header animates with SMIL only (no scripts), which GitHub renders inside <img>.
The chart is illustrative: a training run whose loss looks healthy while an internal
signal (representation entropy) degrades, NDEWS fires an alert, then the run collapses.
"""
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "dark": dict(
        bg0="#1a1b27", bg1="#24283b", panel="#1f2335", border="#2f3549", grid="#2a2f45",
        text="#c0caf5", muted="#a9b1d6", faint="#565f89",
        accent="#7dcfff", signal="#bb9af7", alert="#e0af68", danger="#f7768e", wave="#24283b",
    ),
    "light": dict(
        bg0="#f6f8fa", bg1="#ffffff", panel="#ffffff", border="#d0d7de", grid="#eaeef2",
        text="#1f2328", muted="#57606a", faint="#8c959f",
        accent="#0969da", signal="#8250df", alert="#9a6700", danger="#cf222e", wave="#eaeef2",
    ),
}

SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'Cascadia Code', Consolas, 'Liberation Mono', monospace"

# One animation cycle. Everything shares dur/begin so it stays in sync across loops.
DUR = "9s"
# The plot is revealed left to right by a clip rect: x from PLOT_X0, full width at t=0.7.
PLOT_X0, PLOT_X1 = 650, 1140
ALERT_X, COLLAPSE_X = 930, 1020


def reveal_time(x):
    """Fraction of the cycle at which the reveal edge reaches x."""
    return round(0.7 * (x - PLOT_X0) / (PLOT_X1 - PLOT_X0), 3)


def appear(at, hold_until=0.92):
    """opacity animation: hidden until `at`, visible until `hold_until`, fades by loop end."""
    a2 = round(at + 0.02, 3)
    return (f'<animate attributeName="opacity" dur="{DUR}" repeatCount="indefinite" '
            f'values="0;0;1;1;0" keyTimes="0;{at};{a2};{hold_until};1"/>')


LOSS = ("M650,95 C700,150 760,180 830,198 S930,214 980,214 C1000,214 1010,210 1020,200 "
        "L1035,212 L1050,170 L1062,185 L1078,130 L1092,150 L1110,95 L1125,110 L1140,80")
ENTROPY = "M650,130 C700,124 740,134 790,127 S870,122 900,128 C930,140 960,170 1000,195 S1080,228 1140,236"


def header(c):
    t_alert, t_collapse = reveal_time(ALERT_X), reveal_time(COLLAPSE_X)
    width = PLOT_X1 - PLOT_X0
    grid = "".join(
        f'<line x1="{PLOT_X0}" y1="{y}" x2="{PLOT_X1}" y2="{y}" stroke="{c["grid"]}" stroke-width="1"/>'
        for y in (90, 130, 170, 210, 250)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 320" width="1200" height="320" role="img" aria-label="Manas Maahir. ML researcher and developer. Animated chart: a training run collapses after an early-warning alert fires.">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c["bg0"]}"/>
      <stop offset="1" stop-color="{c["bg1"]}"/>
    </linearGradient>
    <clipPath id="reveal">
      <rect x="{PLOT_X0}" y="60" width="0" height="200">
        <animate attributeName="width" dur="{DUR}" repeatCount="indefinite"
                 values="0;{width};{width};0" keyTimes="0;0.7;0.99;1"/>
      </rect>
    </clipPath>
  </defs>

  <rect width="1200" height="320" fill="url(#bg)"/>

  <!-- identity -->
  <text x="64" y="112" font-family="{MONO}" font-size="16" fill="{c["accent"]}">&gt; ml researcher &amp; developer</text>
  <rect x="326" y="98" width="9" height="18" fill="{c["accent"]}">
    <animate attributeName="opacity" dur="1.1s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;0.5;0.5;1"/>
  </rect>
  <text x="62" y="178" font-family="{SANS}" font-size="60" font-weight="700" fill="{c["text"]}">Manas Maahir</text>
  <text x="64" y="218" font-family="{SANS}" font-size="19" fill="{c["muted"]}">Training dynamics · Continual learning · Reliable AI</text>
  <text x="64" y="252" font-family="{SANS}" font-size="16" font-style="italic" fill="{c["faint"]}">Catching neural networks before they fail.</text>

  <!-- chart panel -->
  <rect x="628" y="30" width="536" height="266" rx="12" fill="{c["panel"]}" stroke="{c["border"]}"/>
  <text x="650" y="54" font-family="{MONO}" font-size="12" fill="{c["faint"]}">training run</text>
  <line x1="930" y1="50" x2="950" y2="50" stroke="{c["accent"]}" stroke-width="2.5"/>
  <text x="956" y="54" font-family="{MONO}" font-size="12" fill="{c["muted"]}">val loss</text>
  <line x1="1030" y1="50" x2="1050" y2="50" stroke="{c["signal"]}" stroke-width="2.5" stroke-dasharray="4 3"/>
  <text x="1056" y="54" font-family="{MONO}" font-size="12" fill="{c["muted"]}">entropy</text>
  {grid}

  <g>
    <animate attributeName="opacity" dur="{DUR}" repeatCount="indefinite" values="0;1;1;0" keyTimes="0;0.03;0.92;1"/>
    <g clip-path="url(#reveal)" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="{ENTROPY}" stroke="{c["signal"]}" stroke-width="2.5" stroke-dasharray="6 4"/>
      <path d="{LOSS}" stroke="{c["accent"]}" stroke-width="3"/>
    </g>

    <!-- NDEWS alert: the entropy signal has started to fall while loss still looks fine -->
    <g opacity="0">
      {appear(t_alert)}
      <line x1="{ALERT_X}" y1="66" x2="{ALERT_X}" y2="250" stroke="{c["alert"]}" stroke-width="1.5" stroke-dasharray="4 4"/>
      <circle cx="{ALERT_X}" cy="142" r="5" fill="{c["alert"]}"/>
      <circle cx="{ALERT_X}" cy="142" r="5" fill="none" stroke="{c["alert"]}" stroke-width="2">
        <animate attributeName="r" dur="1.2s" repeatCount="indefinite" values="5;16"/>
        <animate attributeName="opacity" dur="1.2s" repeatCount="indefinite" values="0.9;0"/>
      </circle>
      <path d="M{ALERT_X - 110},79 l7,-12 l7,12 z" fill="{c["alert"]}"/>
      <text x="{ALERT_X - 103}" y="78" text-anchor="middle" font-family="{SANS}" font-size="9" font-weight="700" fill="{c["panel"]}">!</text>
      <text x="{ALERT_X - 8}" y="79" text-anchor="end" font-family="{MONO}" font-size="12" font-weight="700" fill="{c["alert"]}">NDEWS alert</text>
    </g>

    <!-- collapse: the loss finally reacts -->
    <g opacity="0">
      {appear(t_collapse)}
      <line x1="{COLLAPSE_X}" y1="66" x2="{COLLAPSE_X}" y2="250" stroke="{c["danger"]}" stroke-width="1.5" stroke-dasharray="4 4"/>
      <text x="{COLLAPSE_X + 8}" y="79" font-family="{MONO}" font-size="12" font-weight="700" fill="{c["danger"]}">collapse</text>
    </g>

    <!-- lead time between alert and collapse -->
    <g opacity="0" stroke="{c["muted"]}" stroke-width="1.5">
      {appear(round(t_collapse + 0.04, 3))}
      <line x1="{ALERT_X}" y1="264" x2="{COLLAPSE_X}" y2="264"/>
      <line x1="{ALERT_X}" y1="258" x2="{ALERT_X}" y2="270"/>
      <line x1="{COLLAPSE_X}" y1="258" x2="{COLLAPSE_X}" y2="270"/>
      <text x="{(ALERT_X + COLLAPSE_X) // 2}" y="286" text-anchor="middle" stroke="none" font-family="{MONO}" font-size="12" fill="{c["muted"]}">lead time</text>
    </g>
  </g>
</svg>
'''


def footer(c):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 90" width="1200" height="90" role="img" aria-label="">
  <path d="M0,34 C200,72 400,4 600,32 C800,60 1000,8 1200,36 L1200,90 L0,90 Z" fill="{c["wave"]}"/>
  <path d="M0,48 C220,82 420,16 640,44 C860,70 1020,22 1200,50 L1200,90 L0,90 Z" fill="{c["accent"]}" opacity="0.12"/>
</svg>
'''


if __name__ == "__main__":
    for name, colors in THEMES.items():
        (ASSETS / f"header-{name}.svg").write_text(header(colors), encoding="utf-8")
        (ASSETS / f"footer-{name}.svg").write_text(footer(colors), encoding="utf-8")
    print("wrote", sorted(p.name for p in ASSETS.glob("*-*.svg")))
