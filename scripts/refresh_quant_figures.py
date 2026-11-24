"""Refresh the profile figures from saved outputs in two public notebooks."""

import base64
import json
import re
import struct
from pathlib import Path
from urllib.request import urlopen

BASE = "https://raw.githubusercontent.com/aryaanay/Quantitative-Finance-Model-Development-Portfolio/main/"
ORDER = "OrderBookSimulator_InventoryAwareMarketMaking.ipynb"
PAIRS = "PairsTradingSystem_StatisticalArbitrage.ipynb"
NUMBER = r"-?\d+(?:\.\d+)?"
CAP_ROW = re.compile(rf"^Cap=(\d+): PnL=\$({NUMBER}), mean\|inv\|={NUMBER}, %time at cap=({NUMBER})%$", re.M)
PAIR_ROW = re.compile(rf"^\s*([A-Z]{{1,5}}-[A-Z]{{1,5}})\s+({NUMBER})\s+{NUMBER}\s+({NUMBER})\s+{NUMBER}\s+{NUMBER}\s+(?:True|False)\s*$", re.M)


def value(text):
    return "".join(text) if isinstance(text, list) else text


def outputs(notebook):
    return [output for cell in notebook["cells"] for output in cell.get("outputs", [])]


def stream(notebook):
    return "\n".join(value(output["text"]) for output in outputs(notebook) if "text" in output)


def replace_once(source, pattern, replacement):
    updated, count = re.subn(pattern, lambda _: replacement, source, flags=re.M)
    if count != 1:
        raise ValueError("Expected one chart template match")
    return updated


def refresh_summary(svg, order, pairs):
    caps = [(int(cap), float(pnl), float(time)) for cap, pnl, time in CAP_ROW.findall(stream(order))]
    scores = [(pair, float(train), float(test)) for pair, train, test in PAIR_ROW.findall(stream(pairs))]
    if ([c for c, _, _ in caps] != [500, 200, 100, 50] or len(scores) != 9
            or len({pair for pair, _, _ in scores}) != 9):
        raise ValueError("Notebook tables no longer match the chart layout")
    if any(not 0 <= pnl <= 6000 or not 0 <= time <= 100 for _, pnl, time in caps):
        raise ValueError("Inventory values exceed the chart scale")
    if any(not -.25 <= score <= 1.15 for _, *row in scores for score in row):
        raise ValueError("Sharpe values exceed the chart scale")

    for index, (cap, pnl, time) in enumerate(caps):
        y = 138 + index * 43
        row = (
            f'<text x="34" y="{y}">{cap}</text>'
            f'<rect class="track" x="137" y="{y-14}" width="151" height="14" rx="7"/>'
            f'<rect class="mint" x="137" y="{y-14}" width="{pnl/6000*151:.1f}" height="14" rx="7"/>'
            f'<text x="308" y="{y}">${pnl:,.0f}</text>'
            f'<rect class="track" x="464" y="{y-14}" width="145" height="14" rx="7"/>'
            f'<rect class="amber" x="464" y="{y-14}" width="{time*1.45:.1f}" height="14" rx="7"/>'
            f'<text x="627" y="{y}">{time:.1f}%</text>'
        )
        svg = replace_once(svg, rf'^<text x="34" y="{y}">.*$', row)
    for index, (pair, train, test) in enumerate(scores):
        y = 463 + index * 35
        start = round(221 + (train + .25) * 347)
        end = round(221 + (test + .25) * 347)
        css = "cross" if train * test < 0 else "axis"
        row = (
            f'<text x="34" y="{y+7}">{pair.replace("-", "–")}</text>'
            f'<line class="{css}" x1="{start}" x2="{end}" y1="{y}" y2="{y}"/>'
            f'<circle class="train" cx="{start}" cy="{y}" r="6"/>'
            f'<circle class="mint" cx="{end}" cy="{y}" r="7"/>'
        )
        svg = replace_once(svg, rf'^<text x="34" y="{y+7}">.*$', row)
    _, first_pnl, first_time = caps[0]
    _, last_pnl, last_time = caps[-1]
    flips = sum(train * test < 0 for _, train, test in scores)
    return replace_once(
        svg, r'^<desc id="desc">.*</desc>$',
        f'<desc id="desc">At caps of 500 and 50, simulated P&amp;L was {first_pnl:,.0f} and '
        f'{last_pnl:,.0f} dollars. Time at the cap was {first_time:.1f}% and {last_time:.1f}%. '
        f'{flips} of {len(scores)} bank pairs changed Sharpe ratio sign between periods.</desc>',
    )


def refresh_plot(svg, notebook):
    plots = [value(output["data"]["image/png"]) for output in outputs(notebook)
             if "image/png" in output.get("data", {})]
    if len(plots) != 1:
        raise ValueError("Expected one saved order-book plot")
    encoded = "".join(plots[0].split())
    png = base64.b64decode(encoded, validate=True)
    if (len(png) < 24 or png[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            or struct.unpack(">II", png[16:24]) != (986, 451)):
        raise ValueError("Saved plot no longer fits the profile animation")
    return replace_once(svg, r'data:image/png;base64,[A-Za-z0-9+/=]+',
                        "data:image/png;base64," + encoded)


def fetch(name):
    with urlopen(BASE + name, timeout=15) as response:
        return json.loads(response.read(8_000_001))


def main():
    order, pairs = fetch(ORDER), fetch(PAIRS)
    summary = Path("quant-experiments.svg")
    plot = Path("order-book-simulation.svg")
    # Validate both outputs before touching either tracked file.
    refreshed = [
        (summary, refresh_summary(summary.read_text(encoding="utf-8"), order, pairs)),
        (plot, refresh_plot(plot.read_text(encoding="utf-8"), order)),
    ]
    for path, content in refreshed:
        if path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
