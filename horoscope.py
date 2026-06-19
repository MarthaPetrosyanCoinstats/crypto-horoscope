#!/usr/bin/env python3
"""
Crypto Horoscope — Your daily cosmic guidance, powered by real market data.

The stars have spoken. Your portfolio has not.

Usage:
    python horoscope.py                     # read for major coins
    python horoscope.py BTC ETH SOL DOGE    # read for your holdings
    python horoscope.py --share BTC ETH     # compact shareable text
    python horoscope.py --json BTC ETH      # JSON output
"""

import os
import sys
import json
import hashlib
import random
import argparse
from datetime import date, datetime
from typing import Optional

# ─── Dependency check ────────────────────────────────────────────────────────

try:
    import requests
except ImportError:
    print("Missing dependency: pip install requests rich")
    sys.exit(1)

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    from rich.align import Align
    from rich.table import Table
    from rich.padding import Padding
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

# ─── Config ──────────────────────────────────────────────────────────────────

BASE_URL = "https://openapiv1.coinstats.app"
VERSION = "1.1.0"

DEFAULT_COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT"]

COIN_GLYPHS = {
    "BTC": "₿", "ETH": "Ξ", "SOL": "◎", "BNB": "⬡", "XRP": "✕",
    "DOGE": "Ð", "ADA": "₳", "AVAX": "⌂", "LINK": "⬡", "DOT": "●",
    "MATIC": "◆", "ATOM": "⚛", "LTC": "Ł", "BCH": "Ƀ", "UNI": "🦄",
    "XLM": "✦", "XMR": "ɱ", "HBAR": "ℏ", "ALGO": "Ⲁ", "VET": "V",
}

# ─── API Client ──────────────────────────────────────────────────────────────

class CoinStatsClient:
    """Thin wrapper around the CoinStats API."""

    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers["X-API-KEY"] = api_key

    def _get(self, path: str, **params):
        resp = self.session.get(f"{BASE_URL}{path}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_top_coins(self, limit: int = 500) -> list[dict]:
        data = self._get("/coins", limit=limit)
        return data["result"]

    def get_market(self) -> dict:
        return self._get("/markets")

    def filter_by_symbols(self, coins: list[dict], symbols: list[str]) -> list[dict]:
        upper = {s.upper() for s in symbols}
        seen = set()
        matched = []
        for c in coins:
            sym = c["symbol"].upper()
            if sym in upper and sym not in seen:
                seen.add(sym)
                matched.append(c)
        return matched if matched else []


# ─── Oracle (horoscope engine) ───────────────────────────────────────────────

class CryptoOracle:
    """
    Translates live market data into cosmic wisdom.

    Seeded by today's date + a hash of current prices so readings are
    consistent throughout the day but change daily.
    """

    def __init__(self, coins: list[dict], market: dict, reading_date: date):
        self.coins = coins
        self.market = market
        self.date = reading_date
        self.rng = self._seed_rng(coins, reading_date)

    @staticmethod
    def _seed_rng(coins: list[dict], reading_date: date) -> random.Random:
        price_str = "".join(f"{c['price']:.2f}" for c in coins[:5])
        seed_input = f"{reading_date.isoformat()}{price_str}"
        seed = int(hashlib.md5(seed_input.encode()).hexdigest(), 16) % (2**32)
        return random.Random(seed)

    # ── Market-level readings ─────────────────────────────────────────────

    def market_reading(self) -> str:
        change = self.market.get("marketCapChange", 0)
        dominance = self.market.get("btcDominance", 50)
        vol_change = self.market.get("volumeChange", 0)

        if change <= -5:
            mood = self.rng.choice([
                "The crypto cosmos hemorrhages. The ancient bears have returned from their caves, ravenous.",
                "Red descends upon all charts like a celestial punishment. Even stablecoins feel the psychic damage.",
                "The market gods demand tribute. Portfolio balances are the offering. Breathe.",
            ])
        elif change <= -2:
            mood = self.rng.choice([
                "Mercury dances in retrograde, and your portfolio dances with it — downward.",
                "A bearish mist settles over the markets. The bulls have taken a personal day.",
                "The total market cap sheds {:.1f}%. The stars shrug. This is normal, cosmically speaking.".format(abs(change)),
            ])
        elif change < 1:
            mood = self.rng.choice([
                "The markets breathe in uneasy equilibrium. Neither bulls nor bears have won today. A coin flip masquerades as a trend.",
                "Sideways movement dominates. The cosmos is consolidating its thoughts before its next move.",
                "Flat energy pervades the cryptosphere. The universe has entered a range-bound formation.",
            ])
        elif change < 4:
            mood = self.rng.choice([
                "A gentle green aura washes over the market. Jupiter nods approvingly. Do not sell your house just yet.",
                "Bulls cautiously emerge. The chart gods grant a reprieve. Enjoy it; Mercury returns next week.",
                "The market ascends {:.1f}%. The stars smile upon those who held through the darkness.".format(change),
            ])
        else:
            mood = self.rng.choice([
                "EUPHORIA descends from the heavens! The bulls stampede! The chart forms what analysts call 'very nice.'",
                "Green candles bloom across the cosmos like spring flowers after a six-month winter. Bask in it.",
                "The market surges {:.1f}%. Even the bears are checking their wallets with one eye.".format(change),
            ])

        # BTC dominance commentary
        if dominance > 58:
            dom_line = f" Bitcoin tightens its iron grip at {dominance:.1f}% dominance. Alt season remains a rumor."
        elif dominance < 48:
            dom_line = f" Bitcoin's dominance slips to {dominance:.1f}%. The alts stir in their cages."
        else:
            dom_line = ""

        # Volume energy
        if abs(vol_change) > 20:
            vol_line = f" Unusual cosmic energy detected: volume has {'surged' if vol_change > 0 else 'collapsed'} {abs(vol_change):.0f}%."
        else:
            vol_line = ""

        return mood + dom_line + vol_line

    # ── Per-coin readings ─────────────────────────────────────────────────

    def coin_reading(self, coin: dict) -> str:
        name = coin["name"]
        price = coin["price"]
        d1h = coin.get("priceChange1h", 0) or 0
        d1d = coin.get("priceChange1d", 0) or 0
        d1w = coin.get("priceChange1w", 0) or 0
        d1m = coin.get("priceChange1m", 0) or 0

        # Classify day
        if d1d >= 8:
            day_lines = [
                f"{name} ascends {d1d:.1f}% toward the heavens. The cosmic bulls have chosen you.",
                f"A moon-shot energy blesses {name} today: +{d1d:.1f}%. The chart forms what traders call 'very valid.'",
                f"Jupiter aligns perfectly with {name}'s chart. +{d1d:.1f}%. Do not, however, buy more at the top.",
            ]
        elif d1d >= 3:
            day_lines = [
                f"{name} stirs from its slumber, rising {d1d:.1f}%. A gentle cosmic tailwind guides it upward.",
                f"The stars grant {name} a mild blessing today: +{d1d:.1f}%. Modest gains for the patient soul.",
                f"{name} nudges upward {d1d:.1f}%. Jupiter nods. The bulls take a small victory lap.",
            ]
        elif d1d >= -1:
            day_lines = [
                f"{name} meditates at {_fmt_price(price)}, moving with cosmic stillness. The universe has nothing dramatic to say today.",
                f"Flat energy surrounds {name}. It exists. It breathes. The chart is technically a line.",
                f"{name} consolidates its spiritual energy. Whether this is 'accumulation' or stagnation depends on your optimism.",
            ]
        elif d1d >= -5:
            day_lines = [
                f"{name} descends {abs(d1d):.1f}% as Mercury casts shadows across your holdings.",
                f"The bears have touched {name}, leaving a mark of {d1d:.1f}%. Your conviction shall be tested.",
                f"{name} dips {abs(d1d):.1f}%. The cosmos suggests you 'zoom out.' The chart, upon zooming out, still looks concerning.",
            ]
        else:
            day_lines = [
                f"{name} craters {d1d:.1f}% today. A blood moon rises over your position.",
                f"Dark forces besiege {name}: {d1d:.1f}%. The word 'capitulation' appears in your fortune.",
                f"Astral turbulence strikes {name} with {abs(d1d):.1f}% fury. This is not a good omen. You may still HODL if you wish.",
            ]

        reading = self.rng.choice(day_lines)

        # Monthly context suffix
        if d1m <= -20:
            reading += self.rng.choice([
                f" The moon of {name} has waned {abs(d1m):.0f}% this month. Patience is a virtue. So is a stop-loss.",
                f" This month has not been kind: {d1m:.0f}%. The cosmos is telling you something; what exactly remains unclear.",
            ])
        elif d1m >= 20:
            reading += self.rng.choice([
                f" And yet — {name} still gleams +{d1m:.0f}% this month. The stars have not entirely abandoned you.",
                f" Despite today's turbulence, the monthly chart whispers +{d1m:.0f}%. Perspective, pilgrim.",
            ])

        return reading

    # ── Special sections ──────────────────────────────────────────────────

    def mercury_curse(self) -> Optional[tuple[dict, str]]:
        """The worst daily performer gets Mercury's curse."""
        worst = min(self.coins, key=lambda c: c.get("priceChange1d", 0) or 0)
        change = worst.get("priceChange1d", 0) or 0
        if change >= 0:
            return None  # No curse if everything is up

        curses = [
            f"{worst['name']} has entered its shadow period. Consider burning sage. And your position.",
            f"The cosmic forces single out {worst['name']} for special suffering today: {change:.1f}%.",
            f"{worst['name']} bears Mercury's mark most heavily today. The chart forms what analysts call 'oh no.'",
            f"Of all the coins, {worst['name']} draws the most astral ire: {change:.1f}%. Reflect on your choices.",
        ]
        return worst, self.rng.choice(curses)

    def venus_blessing(self) -> Optional[tuple[dict, str]]:
        """The best performer (weekly) receives Venus's blessing."""
        best = max(self.coins, key=lambda c: c.get("priceChange1w", 0) or 0)
        change = best.get("priceChange1w", 0) or 0
        if change <= 0:
            return None

        blessings = [
            f"Venus smiles upon {best['name']} this week: +{change:.1f}%. The cosmos rewards the believer.",
            f"{best['name']} basks in celestial favor with a weekly gain of +{change:.1f}%. The stars have a favorite.",
            f"Of your holdings, {best['name']} has most pleased the market gods this week: +{change:.1f}%.",
            f"The stellar winds carry {best['name']} higher: +{change:.1f}% on the week. Glory to those who held.",
        ]
        return best, self.rng.choice(blessings)

    def prophecy(self) -> str:
        """A forward-looking statement of magnificent vagueness."""
        prophesies = [
            "A pattern forms on the charts. Analysts shall name it something confident. They will disagree.",
            "A whale stirs in the deep. Its movements will be described as 'bullish' and 'bearish' simultaneously by different influencers.",
            "Volatility approaches from the northwest. The candles that follow will be colorful.",
            "An announcement looms. Its price impact will be the opposite of what you expect.",
            "The stars foresee a consolidation phase. It will last either 3 days or 6 months. The cosmos has not decided.",
            "Someone, somewhere, is about to post a chart with seven indicators and one conclusion. They are very confident.",
            "A support level will be tested. Whether it holds depends on factors the astrologer declines to specify.",
            "The number 'go up' appears in your financial future. Timing remains cosmically ambiguous.",
        ]
        return self.rng.choice(prophesies)

    def lucky_numbers(self) -> list[str]:
        """Lucky numbers are just the current prices. Obviously."""
        selected = self.rng.sample(self.coins, min(3, len(self.coins)))
        return [_fmt_price(c["price"]) for c in selected]

    # ── Full reading ──────────────────────────────────────────────────────

    def full_reading(self) -> dict:
        """Assemble the complete horoscope data."""
        return {
            "date": self.date.isoformat(),
            "market": {
                "cap": self.market.get("marketCap", 0),
                "cap_change": self.market.get("marketCapChange", 0),
                "btc_dominance": self.market.get("btcDominance", 0),
                "volume": self.market.get("volume", 0),
                "reading": self.market_reading(),
            },
            "coins": [
                {
                    "symbol": c["symbol"],
                    "name": c["name"],
                    "price": c["price"],
                    "change_1h": c.get("priceChange1h", 0),
                    "change_1d": c.get("priceChange1d", 0),
                    "change_1w": c.get("priceChange1w", 0),
                    "change_1m": c.get("priceChange1m", 0),
                    "reading": self.coin_reading(c),
                }
                for c in self.coins
            ],
            "mercury_curse": (
                lambda r: {"symbol": r[0]["symbol"], "name": r[0]["name"],
                           "change_1d": r[0].get("priceChange1d", 0), "reading": r[1]}
                if r else None
            )(self.mercury_curse()),
            "venus_blessing": (
                lambda r: {"symbol": r[0]["symbol"], "name": r[0]["name"],
                           "change_1w": r[0].get("priceChange1w", 0), "reading": r[1]}
                if r else None
            )(self.venus_blessing()),
            "prophecy": self.prophecy(),
            "lucky_numbers": self.lucky_numbers(),
        }


# ─── Renderers ───────────────────────────────────────────────────────────────

def _fmt_price(price: float) -> str:
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:.4f}"
    elif price >= 0.0001:
        return f"${price:.6f}"
    else:
        return f"${price:.2e}"


def _pct_str(val: float) -> str:
    arrow = "▲" if val > 0 else "▼"
    return f"{arrow}{abs(val):.2f}%"


def _pct_color(val: float) -> str:
    """Rich color for a percentage value."""
    if val >= 3:
        return "bold green"
    elif val >= 0:
        return "green"
    elif val >= -3:
        return "red"
    else:
        return "bold red"


def render_rich(reading: dict) -> None:
    """Beautiful terminal output using Rich."""
    today = datetime.fromisoformat(reading["date"]).strftime("%A, %B %-d, %Y")
    market = reading["market"]

    # ── Header banner ─────────────────────────────────────────────────────
    header_text = Text(justify="center")
    header_text.append("🔮  Crypto Horoscope\n", style="bold gold1")
    header_text.append(f"{today}\n", style="bright_white")
    header_text.append("✦  ·  ✦  ·  ✦  ·  ✦  ·  ✦  ·  ✦", style="dim yellow")

    console.print()
    console.print(Panel(
        Align.center(header_text),
        border_style="medium_purple",
        padding=(1, 4),
    ))
    console.print()

    # ── Market overview ───────────────────────────────────────────────────
    cap_b = market["cap"] / 1e12
    vol_b = market["volume"] / 1e9
    cap_change = market["cap_change"]
    dom = market["btc_dominance"]

    stats = Table.grid(padding=(0, 3))
    stats.add_column(style="dim")
    stats.add_column(style="bold bright_white")
    stats.add_row("Market Cap", f"${cap_b:.2f}T")
    stats.add_row("Volume 24h", f"${vol_b:.1f}B")
    stats.add_row("BTC Dominance", f"{dom:.1f}%")
    stats.add_row(
        "24h Change",
        Text(_pct_str(cap_change), style=_pct_color(cap_change)),
    )

    market_content = Group(
        stats,
        Text(""),
        Text(market["reading"], style="italic #c9b8f0"),
    )

    console.print(Panel(
        market_content,
        title="[bold cyan]✦  The Cosmic Market[/]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    # ── Coin panels ───────────────────────────────────────────────────────
    console.rule("[bold medium_purple]✦  Your Signs  ✦[/]", style="dim medium_purple")
    console.print()

    for coin in reading["coins"]:
        sym = coin["symbol"]
        glyph = COIN_GLYPHS.get(sym, "◈")
        price = coin["price"]
        d1h = coin.get("change_1h", 0) or 0
        d   = coin.get("change_1d", 0) or 0
        w   = coin.get("change_1w", 0) or 0
        m   = coin.get("change_1m", 0) or 0

        # Border tint follows daily trend
        if d >= 3:
            border = "green3"
        elif d <= -5:
            border = "red3"
        else:
            border = "medium_purple"

        stats_text = Text()
        stats_text.append(_fmt_price(price), style="bold bright_white")
        stats_text.append("     ")
        stats_text.append("1h ", style="dim")
        stats_text.append(_pct_str(d1h), style=_pct_color(d1h))
        stats_text.append("   1d ", style="dim")
        stats_text.append(_pct_str(d), style=_pct_color(d))
        stats_text.append("   1w ", style="dim")
        stats_text.append(_pct_str(w), style=_pct_color(w))
        stats_text.append("   1m ", style="dim")
        stats_text.append(_pct_str(m), style=_pct_color(m))

        coin_content = Group(
            stats_text,
            Text(""),
            Text(f'"{coin["reading"]}"', style="italic #c9b8f0"),
        )

        console.print(Panel(
            coin_content,
            title=f"[gold1]{glyph}[/]  [bold white]{coin['name']}[/]  [dim]{sym}[/]",
            border_style=border,
            padding=(1, 2),
        ))
        console.print()

    # ── Mercury's Curse ───────────────────────────────────────────────────
    curse = reading.get("mercury_curse")
    if curse:
        c_glyph = COIN_GLYPHS.get(curse["symbol"], "◈")
        curse_header = Text()
        curse_header.append(f"{c_glyph}  {curse['symbol']}  ", style="bold red")
        curse_header.append(_pct_str(curse["change_1d"]) + " today", style="bold red")

        console.print(Panel(
            Group(
                curse_header,
                Text(""),
                Text(f'"{curse["reading"]}"', style="italic #ffb3b3"),
            ),
            title="[bold red]☿  Mercury's Curse  —  Worst Today[/]",
            border_style="red",
            padding=(1, 2),
        ))
        console.print()

    # ── Venus's Blessing ──────────────────────────────────────────────────
    blessing = reading.get("venus_blessing")
    if blessing:
        b_glyph = COIN_GLYPHS.get(blessing["symbol"], "◈")
        blessing_header = Text()
        blessing_header.append(f"{b_glyph}  {blessing['symbol']}  ", style="bold green3")
        blessing_header.append(f"+{abs(blessing['change_1w']):.1f}% this week", style="bold green3")

        console.print(Panel(
            Group(
                blessing_header,
                Text(""),
                Text(f'"{blessing["reading"]}"', style="italic #b3ffcc"),
            ),
            title="[bold green3]♀  Venus's Blessing  —  Weekly Brightest[/]",
            border_style="green3",
            padding=(1, 2),
        ))
        console.print()

    # ── Prophecy ─────────────────────────────────────────────────────────
    lucky = "   ✦   ".join(reading["lucky_numbers"])
    console.print(Panel(
        Group(
            Text(f'"{reading["prophecy"]}"', style="italic bright_white"),
            Text(""),
            Text(f"Lucky numbers:  {lucky}", style="dim gold1"),
        ),
        title="[bold magenta]🔮  Today's Prophecy[/]",
        border_style="magenta",
        padding=(1, 2),
    ))

    # ── Footer ────────────────────────────────────────────────────────────
    console.print()
    console.rule(
        "[dim]Powered by [link=https://coinstats.app/api/]CoinStats API[/link]"
        "  ·  coinstats.app/api  ·  Not financial advice. Also not actual astrology.[/]",
        style="dim medium_purple",
    )
    console.print()


def render_plain(reading: dict) -> None:
    """Plain text output for terminals without Rich."""
    today = datetime.fromisoformat(reading["date"]).strftime("%A, %B %d, %Y")
    market = reading["market"]

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  Crypto Horoscope — {today}")
    print(sep)

    cap_b = market["cap"] / 1e12
    print(f"\n  Market Cap: ${cap_b:.2f}T  ({_pct_str(market['cap_change'])})")
    print(f"  BTC Dominance: {market['btc_dominance']:.1f}%")
    print(f"\n  {market['reading']}")
    print()

    print("  YOUR SIGNS")
    print("  " + "-" * 40)
    for coin in reading["coins"]:
        d = coin["change_1d"]
        w = coin["change_1w"]
        print(f"\n  {coin['symbol']} {_fmt_price(coin['price'])}  1d {_pct_str(d)}  1w {_pct_str(w)}")
        print(f"  {coin['reading']}")

    curse = reading.get("mercury_curse")
    if curse:
        print(f"\n  MERCURY'S CURSE: {curse['symbol']} {_pct_str(curse['change_1d'])} today")
        print(f"  {curse['reading']}")

    blessing = reading.get("venus_blessing")
    if blessing:
        print(f"\n  VENUS'S BLESSING: {blessing['symbol']} +{abs(blessing['change_1w']):.1f}% this week")
        print(f"  {blessing['reading']}")

    print(f"\n  PROPHECY: \"{reading['prophecy']}\"")
    print(f"  Lucky numbers: {'  ·  '.join(reading['lucky_numbers'])}")
    print(f"\n{sep}")
    print("  Powered by CoinStats API (https://coinstats.app/api/)")
    print("  Not financial advice. Also not actual astrology.")
    print(f"{sep}\n")


def render_share(reading: dict) -> None:
    """Compact share-friendly output for Discord / Twitter / Slack."""
    today = datetime.fromisoformat(reading["date"]).strftime("%b %-d, %Y")
    market = reading["market"]

    lines = [
        f"🔮 Crypto Horoscope — {today}",
        "",
        f"Market: ${market['cap']/1e12:.2f}T  {_pct_str(market['cap_change'])}  BTC dom {market['btc_dominance']:.1f}%",
        f"\"{market['reading'][:120]}\"" if len(market['reading']) > 120 else f"\"{market['reading']}\"",
        "",
    ]

    for coin in reading["coins"]:
        glyph = COIN_GLYPHS.get(coin["symbol"], "◈")
        lines.append(
            f"{glyph} {coin['symbol']} {_fmt_price(coin['price'])}  "
            f"1d {_pct_str(coin['change_1d'])}  1w {_pct_str(coin['change_1w'])}"
        )

    curse = reading.get("mercury_curse")
    blessing = reading.get("venus_blessing")
    lines.append("")
    if curse:
        lines.append(f"☿ Cursed: {curse['symbol']} {_pct_str(curse['change_1d'])}")
    if blessing:
        lines.append(f"♀ Blessed: {blessing['symbol']} +{abs(blessing['change_1w']):.1f}% this week")

    lines += [
        "",
        f"🔮 \"{reading['prophecy']}\"",
        "",
        "Powered by @CoinStatsApp · coinstats.app/api",
    ]

    print("\n".join(lines))


# ─── CLI ─────────────────────────────────────────────────────────────────────

def get_api_key() -> str:
    key = os.environ.get("COINSTATS_API_KEY", "").strip()
    if not key:
        print("Error: COINSTATS_API_KEY environment variable not set.")
        print("Get your free key at: https://openapi.coinstats.app")
        print("Then run:  export COINSTATS_API_KEY=your_key_here")
        sys.exit(1)
    return key


def main():
    parser = argparse.ArgumentParser(
        description="🔮 Crypto Horoscope: daily cosmic guidance powered by real market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python horoscope.py                      # top coins reading
  python horoscope.py BTC ETH SOL DOGE     # your holdings
  python horoscope.py --share BTC ETH      # shareable text
  python horoscope.py --json BTC ETH       # JSON output

environment:
  COINSTATS_API_KEY    your CoinStats API key (required)
        """,
    )
    parser.add_argument(
        "coins",
        nargs="*",
        metavar="SYMBOL",
        help="coin symbols to read (default: top 10 by market cap)",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="compact shareable output for Discord/Slack/Twitter",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_out",
        help="output raw JSON",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="plain text output (no Rich formatting)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Crypto Horoscope {VERSION}",
    )
    args = parser.parse_args()

    api_key = get_api_key()
    client = CoinStatsClient(api_key)

    # Fetch data
    try:
        if HAS_RICH and not args.json_out and not args.share and not args.plain:
            with console.status("[dim]Consulting the stars…[/]"):
                all_coins = client.get_top_coins(limit=500)
                market = client.get_market()
        else:
            all_coins = client.get_top_coins(limit=500)
            market = client.get_market()
    except requests.HTTPError as e:
        print(f"API error: {e}")
        sys.exit(1)
    except requests.ConnectionError:
        print("Connection error: check your internet connection.")
        sys.exit(1)

    # Resolve requested symbols
    symbols = [s.upper() for s in args.coins] if args.coins else DEFAULT_COINS
    coins = client.filter_by_symbols(all_coins, symbols)

    if not coins:
        print(f"No matching coins found for: {', '.join(symbols)}")
        print("Try common symbols like BTC, ETH, SOL, DOGE, ADA…")
        sys.exit(1)

    # Generate reading
    oracle = CryptoOracle(coins, market, date.today())
    reading = oracle.full_reading()

    # Render
    if args.json_out:
        print(json.dumps(reading, indent=2))
    elif args.share:
        render_share(reading)
    elif args.plain or not HAS_RICH:
        render_plain(reading)
    else:
        render_rich(reading)


if __name__ == "__main__":
    main()
