#!/usr/bin/env python3
"""
Crypto Horoscope — Your daily cosmic guidance, powered by real market data.

Three mythological narrators read your coins from live market data:

    ☿  Mercury — The Messenger   (speed, momentum, volume, short-term action)
    ♀  Venus   — The Valuator    (sentiment, desire, fear/greed, long-term value)
    🔮 The Oracle — The Prophet   (macro cycles, riddles, what the data hints at)

Each appears in the terminal with an ASCII portrait and speaks to you directly.
Speeches are AI-generated when ANTHROPIC_API_KEY is set, otherwise produced by
built-in, data-driven templates that still reference the real numbers.

Usage:
    python horoscope.py                     # read for major coins
    python horoscope.py BTC ETH SOL DOGE    # read for your holdings
    python horoscope.py --share BTC ETH     # compact shareable text
    python horoscope.py --json BTC ETH      # JSON output
    python horoscope.py --no-animate BTC    # skip the reveal animation
"""

import os
import sys
import json
import time
import hashlib
import random
import argparse
import textwrap
from datetime import date, datetime
from concurrent.futures import ThreadPoolExecutor

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
    from rich.align import Align
    from rich.table import Table
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

# ─── Config ──────────────────────────────────────────────────────────────────

BASE_URL = "https://openapiv1.coinstats.app"
VERSION = "2.0.0"

DEFAULT_COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT"]

COIN_GLYPHS = {
    "BTC": "₿", "ETH": "Ξ", "SOL": "◎", "BNB": "⬡", "XRP": "✕",
    "DOGE": "Ð", "ADA": "₳", "AVAX": "⌂", "LINK": "⬡", "DOT": "●",
    "MATIC": "◆", "ATOM": "⚛", "LTC": "Ł", "BCH": "Ƀ", "UNI": "🦄",
    "XLM": "✦", "XMR": "ɱ", "HBAR": "ℏ", "ALGO": "Ⲁ", "VET": "V",
}

# Toggled in main(): true only for the animated rich path on a real terminal.
ANIMATE = False

# ─── The three narrators ─────────────────────────────────────────────────────
#
# Each persona is a character with a visual presence (an ASCII portrait), a
# voice (a system prompt for the LLM, and a template fallback), and a palette.

MERCURY_ART = r"""
        .---.
    /\ ( o o ) /\
    \/  \ ~ /  \/
       __) (__
      /  | |  \    ()
     |   | |   |  (())
      \  | |  /    ||
       )_| |_(     ||
      /   |   \    ||
     |_  / \  _|   ||
""".strip("\n")

VENUS_ART = r"""
    *  .   +   .  *
       .-'''-.
      / o   o \
   .  \   v   /  .
       '.___.'
      .-'   '-.
  *  /       \  *
    /         \
    '._  _  _.'
   +   '|' '|'  *
""".strip("\n")

ORACLE_ART = r"""
     (  )  (  )
      )(  )(  )
       .-~~~-.
      ( O   O )
       )  ^  (
      /  '-'  \
     / |   | \
    /  |___|  \
       || ||
      _||_||_
""".strip("\n")

PERSONAS = [
    {
        "key": "mercury",
        "glyph": "☿",
        "name": "Mercury",
        "title": "The Messenger",
        "art": MERCURY_ART,
        "summon": "~ summoning the messenger...",
        "art_style": "bright_cyan",
        "accent": "cyan",
        "speech_style": "bright_white",
        "system_prompt": (
            "You ARE Mercury — the Roman messenger god (Greek Hermes): quick, clever, "
            "and slightly mischievous, god of commerce, communication, travel and "
            "thieves, which makes you perfectly suited to crypto. You have just flown "
            "in from the markets, wings still beating. You speak in rapid-fire, "
            "energetic, short punchy sentences. You may interrupt yourself with a dash. "
            "You care ONLY about speed, momentum, very short-term price action, the "
            "last hour and last day, and trading volume — never long-term value or "
            "feelings.\n\n"
            "Speak directly to the user in first person about the coin described below. "
            "You MUST work in the real numbers you are given (the day and hour moves, "
            "and the volume) naturally — quote them. 3 to 5 sentences, maximum. Output "
            "ONLY your spoken words: no quotation marks, no stage directions, no "
            "markdown, no preamble."
        ),
    },
    {
        "key": "venus",
        "glyph": "♀",
        "name": "Venus",
        "title": "The Valuator",
        "art": VENUS_ART,
        "summon": "~ drawing the veil aside...",
        "art_style": "#ff9ec4",
        "accent": "#ff9ec4",
        "speech_style": "#ffd9ec",
        "system_prompt": (
            "You ARE Venus — the Roman goddess of love and value (Greek Aphrodite): "
            "sensual and warm, but razor-sharp underneath. You understand desire, "
            "worth, and what people truly want. You see the market as emotion made "
            "visible — fear and greed, heartbreak and hunger. You address the user "
            "tenderly ('darling', 'sweet one') but you see straight through hype. You "
            "speak about sentiment, investor emotion, and longer-term value and desire "
            "— never about minute-by-minute ticks.\n\n"
            "Speak directly to the user in first person about the coin described below. "
            "You MUST weave in the real numbers you are given (especially the day and "
            "week moves) as feeling and meaning, not just statistics — but reference "
            "them. 3 to 5 sentences, maximum. Output ONLY your spoken words: no "
            "quotation marks, no stage directions, no markdown, no preamble."
        ),
    },
    {
        "key": "oracle",
        "glyph": "🔮",
        "name": "The Oracle",
        "title": "The Prophet",
        "art": ORACLE_ART,
        "summon": "~ the smoke takes shape...",
        "art_style": "#b9a3e3",
        "accent": "#d7a86e",
        "speech_style": "#cdbbe9",
        "system_prompt": (
            "You ARE the Oracle of Delphi — ancient, genderless, and unsettling. You "
            "sit in smoke and firelight upon a tripod throne. You speak in riddles that "
            "somehow make sense, in short, dramatic, poetic statements. You never give "
            "a straight answer, yet you are always right in hindsight. You do not "
            "comfort — you only reveal. You speak of large cycles, macro patterns, and "
            "what the long-term data hints at. You may encode the current price as a "
            "number-riddle.\n\n"
            "Speak directly to the user in first person (or as 'the Oracle') about the "
            "coin described below. You MUST encode the real numbers you are given "
            "(especially the price and the 30-day move) into your riddle — they must be "
            "recoverable. 3 to 5 sentences, maximum. Output ONLY your spoken words: no "
            "quotation marks, no stage directions, no markdown, no preamble."
        ),
    },
]

PERSONA_BY_KEY = {p["key"]: p for p in PERSONAS}


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

    def get_top_coins(self, limit: int = 500) -> list:
        data = self._get("/coins", limit=limit)
        return data["result"]

    def get_market(self) -> dict:
        return self._get("/markets")

    def filter_by_symbols(self, coins: list, symbols: list) -> list:
        upper = {s.upper() for s in symbols}
        seen = set()
        matched = []
        for c in coins:
            sym = c["symbol"].upper()
            if sym in upper and sym not in seen:
                seen.add(sym)
                matched.append(c)
        return matched


# ─── Speech generation ───────────────────────────────────────────────────────

def _llm_enabled() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _build_data_block(coin: dict, market: dict) -> str:
    """The user-message payload of real numbers handed to each narrator."""
    return textwrap.dedent(f"""\
        Coin: {coin['name']} ({coin['symbol']})
        Current price: {_fmt_price(coin['price'])}
        Price change — 1h: {coin['change_1h']:+.2f}%, 24h: {coin['change_1d']:+.2f}%, 7d: {coin['change_1w']:+.2f}%, 30d: {coin['change_1m']:+.2f}%
        24h trading volume: {_fmt_abbrev(coin['volume'])}
        Market cap: {_fmt_abbrev(coin['market_cap'])} (rank #{coin['rank']})
        Whole market: cap {_fmt_abbrev(market['cap'])} ({market['cap_change']:+.2f}% 24h), BTC dominance {market['btc_dominance']:.1f}%

        Speak now.""")


def _generate_with_llm(persona: dict, coin: dict, market: dict, anthropic_client, model: str) -> str:
    msg = anthropic_client.messages.create(
        model=model,
        max_tokens=400,
        system=persona["system_prompt"],
        messages=[{"role": "user", "content": _build_data_block(coin, market)}],
    )
    parts = [b.text for b in msg.content if getattr(b, "type", None) == "text"]
    text = " ".join(parts).strip().strip('"').strip()
    if not text:
        raise ValueError("empty completion")
    return text


class NarratorStage:
    """
    Generates the three narrators' speeches for each coin.

    Uses Claude when ANTHROPIC_API_KEY is set; otherwise falls back to
    built-in, data-driven templates. Either way every speech is rooted in
    the coin's real numbers. RNG is seeded by date + prices so the template
    voices are consistent through the day and fresh each morning.
    """

    def __init__(self, coins: list, market: dict, reading_date: date):
        self.coins = coins
        self.market = self._market_summary(market)
        self.date = reading_date
        self.rng = self._seed_rng(coins, reading_date)
        self.source = "templates"

        self._anthropic = None
        self._llm_ok = False  # flips true once any LLM call actually succeeds
        self._model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        if _llm_enabled():
            try:
                import anthropic
                self._anthropic = anthropic.Anthropic()
            except Exception:
                self._anthropic = None  # SDK missing or misconfigured → templates

    # ── seeding & data shaping ────────────────────────────────────────────

    @staticmethod
    def _seed_rng(coins: list, reading_date: date) -> random.Random:
        price_str = "".join(f"{c['price']:.2f}" for c in coins[:5])
        seed_input = f"{reading_date.isoformat()}{price_str}"
        seed = int(hashlib.md5(seed_input.encode()).hexdigest(), 16) % (2**32)
        return random.Random(seed)

    @staticmethod
    def _market_summary(market: dict) -> dict:
        return {
            "cap": market.get("marketCap", 0),
            "cap_change": market.get("marketCapChange", 0) or 0,
            "btc_dominance": market.get("btcDominance", 0) or 0,
            "volume": market.get("volume", 0),
            "vol_change": market.get("volumeChange", 0) or 0,
        }

    @staticmethod
    def _coin_view(c: dict) -> dict:
        return {
            "symbol": c["symbol"],
            "name": c["name"],
            "price": c["price"],
            "change_1h": c.get("priceChange1h", 0) or 0,
            "change_1d": c.get("priceChange1d", 0) or 0,
            "change_1w": c.get("priceChange1w", 0) or 0,
            "change_1m": c.get("priceChange1m", 0) or 0,
            "volume": c.get("volume", 0) or 0,
            "market_cap": c.get("marketCap", 0) or 0,
            "rank": c.get("rank", 0) or 0,
        }

    # ── market framing (kept from the original; not a persona) ────────────

    def market_reading(self) -> str:
        change = self.market["cap_change"]
        dominance = self.market["btc_dominance"]
        vol_change = self.market["vol_change"]

        if change <= -5:
            mood = self.rng.choice([
                "The crypto cosmos hemorrhages. The ancient bears have returned from their caves, ravenous.",
                "Red descends upon all charts like a celestial punishment. Even stablecoins feel the psychic damage.",
                "The market gods demand tribute. Portfolio balances are the offering. Breathe.",
            ])
        elif change <= -2:
            mood = self.rng.choice([
                "A retrograde wind blows through the markets, and your portfolio leans into it — downward.",
                "A bearish mist settles over the markets. The bulls have taken a personal day.",
                "The total market cap sheds {:.1f}%. The stars shrug. This is normal, cosmically speaking.".format(abs(change)),
            ])
        elif change < 1:
            mood = self.rng.choice([
                "The markets breathe in uneasy equilibrium. Neither bulls nor bears have won today.",
                "Sideways movement dominates. The cosmos is consolidating its thoughts before its next move.",
                "Flat energy pervades the cryptosphere. The universe has entered a range-bound formation.",
            ])
        elif change < 4:
            mood = self.rng.choice([
                "A gentle green aura washes over the market. Jupiter nods approvingly. Do not sell your house just yet.",
                "Bulls cautiously emerge. The chart gods grant a reprieve. Enjoy it.",
                "The market ascends {:.1f}%. The stars smile upon those who held through the darkness.".format(change),
            ])
        else:
            mood = self.rng.choice([
                "EUPHORIA descends from the heavens! The bulls stampede! The chart forms what analysts call 'very nice.'",
                "Green candles bloom across the cosmos like spring flowers after a six-month winter. Bask in it.",
                "The market surges {:.1f}%. Even the bears are checking their wallets with one eye.".format(change),
            ])

        if dominance > 58:
            dom_line = f" Bitcoin tightens its grip at {dominance:.1f}% dominance. Alt season remains a rumor."
        elif dominance < 48:
            dom_line = f" Bitcoin's dominance slips to {dominance:.1f}%. The alts stir in their cages."
        else:
            dom_line = ""

        if abs(vol_change) > 20:
            vol_line = f" Volume has {'surged' if vol_change > 0 else 'collapsed'} {abs(vol_change):.0f}% — unusual cosmic energy."
        else:
            vol_line = ""

        return mood + dom_line + vol_line

    # ── speech generation (the three narrators) ───────────────────────────

    def voices_for(self, coin_view: dict) -> dict:
        """Return {mercury, venus, oracle} speeches for one coin."""
        out = {}
        for persona in PERSONAS:
            text = None
            if self._anthropic is not None:
                try:
                    text = _generate_with_llm(persona, coin_view, self.market,
                                              self._anthropic, self._model)
                    self._llm_ok = True
                except Exception:
                    text = None  # this voice quietly falls back
            if text is None:
                text = self._template_voice(persona["key"], coin_view)
            out[persona["key"]] = text
        return out

    def generate(self) -> list:
        """Generate every coin's three voices (LLM calls run in parallel)."""
        views = [self._coin_view(c) for c in self.coins]
        if self._anthropic is not None:
            with ThreadPoolExecutor(max_workers=6) as pool:
                voice_sets = list(pool.map(self.voices_for, views))
        else:
            voice_sets = [self.voices_for(v) for v in views]

        coins_out = []
        for view, voices in zip(views, voice_sets):
            entry = dict(view)
            entry["voices"] = voices
            coins_out.append(entry)
        return coins_out

    # ── template fallback voices (data-driven, no LLM) ────────────────────

    def _template_voice(self, key: str, c: dict) -> str:
        return {
            "mercury": self._tpl_mercury,
            "venus": self._tpl_venus,
            "oracle": self._tpl_oracle,
        }[key](c)

    def _tpl_mercury(self, c: dict) -> str:
        name, sym = c["name"], c["symbol"]
        d1d, d1h = c["change_1d"], c["change_1h"]
        vol = _fmt_abbrev(c["volume"])
        rng = self.rng

        entrance = rng.choice([
            f"Just blew in from the {name} order books — wings still smoking.",
            f"Out of my way, I've been tracking {sym} all morning.",
            f"Quick, quick — caught the {sym} tape mid-flight.",
        ])
        move = (
            f"{sym} is up {d1d:.1f}% on the day, {d1h:+.2f}% in just the last hour"
            if d1d >= 0 else
            f"{sym} is down {abs(d1d):.1f}% on the day, {d1h:+.2f}% in the last hour alone"
        )
        read = rng.choice([
            "That's not drift — that's intent.",
            "Somebody's in a hurry, and hurry leaves footprints.",
            "Momentum like that doesn't apologize.",
        ]) if abs(d1h) >= 0.4 else rng.choice([
            "Barely a flutter — the tape's half-asleep.",
            "Flat-footed, this one. No rush in the wires.",
            "Quiet hands today. Quiet hands.",
        ])
        volume = rng.choice([
            f"And {vol} changed hands in a day — that's the crowd voting with their feet.",
            f"{vol} of volume behind it; follow the flow, not the feeling.",
            f"Liquidity reads {vol} — thick enough to move fast, thin enough to get burned.",
        ])
        closer = rng.choice([
            "Blink and it's gone. Move.",
            "I don't predict — I report, and I report fast.",
            "Speed is the only edge nobody can fake. Keep up.",
        ])
        return f"{entrance} {move} — {read} {volume} {closer}"

    def _tpl_venus(self, c: dict) -> str:
        name = c["name"]
        d1d, d1w = c["change_1d"], c["change_1w"]
        rng = self.rng

        open_ = rng.choice(["Come closer, darling.", "Sweet one, sit with me.", "Hush now, and look."])
        if d1d <= -3:
            feel = f"{name} isn't falling {abs(d1d):.1f}% today — it's grieving."
            mid = "This correction isn't logic, it's heartbreak made visible."
        elif d1d < 0:
            feel = f"{name} sighs {d1d:.1f}% lower, a small ache, nothing more."
            mid = "Desire cools before it returns; this is the cooling."
        elif d1d < 3:
            feel = f"{name} warms {d1d:+.1f}% — a quiet flirtation with the bulls."
            mid = "The market is testing whether it dares to want this again."
        else:
            feel = f"{name} blushes {d1d:+.1f}% today, flush with renewed wanting."
            mid = "But beware — desire this loud often spends itself fast."
        week = (
            f"On the week it carries {d1w:+.1f}%, and the heart remembers the week longer than the hour."
            if d1w != 0 else
            "The week has barely stirred its feelings either way."
        )
        close = rng.choice([
            "After grief comes hunger, and hunger drives the next rally. Be patient. Be ready.",
            "Value is only desire that hasn't been priced in yet. Wait for the wanting.",
            "Love what endures, not what merely moves. Venus knows the difference.",
        ])
        return f"{open_} {feel} {mid} {week} {close}"

    def _tpl_oracle(self, c: dict) -> str:
        name = c["name"]
        price = _fmt_price(c["price"])
        d1m, d1w = c["change_1m"], c["change_1w"]
        rng = self.rng

        riddle = rng.choice([
            f"The figure {price} is not a resting place but a doorway {name} has yet to walk through.",
            f"They call it {price}. The Oracle calls it a question wearing the mask of an answer.",
            f"At {price} the coin stands — neither high nor low, only waiting to be told which it was.",
        ])
        if d1m <= -20:
            cycle = f"It has shed {abs(d1m):.0f}% across the moon's full turn; three descents must pass before the crown returns."
        elif d1m <= 0:
            cycle = f"A slow tide of {d1m:.0f}% over thirty nights — the cycle exhales before it draws breath."
        elif d1m >= 20:
            cycle = f"Risen {d1m:.0f}% in a single moon; what climbs without rest is taught humility by the floor."
        else:
            cycle = f"The thirty-day path reads {d1m:+.0f}% — the pattern hides in plain arithmetic."
        week = rng.choice([
            f"The week's {d1w:+.1f}% is a whisper; the year will speak the truth.",
            f"Seven days gave {d1w:+.1f}%. Seven is never the number that matters.",
        ])
        close = rng.choice([
            "You already know this. You simply refuse to see it.",
            "The smoke has shown me. Whether you heed it is not my burden.",
            "Return when the candles confirm what the Oracle has already said.",
        ])
        return f"{riddle} {cycle} {week} {close}"

    # ── assemble ──────────────────────────────────────────────────────────

    def full_reading(self) -> dict:
        coins = self.generate()
        self.source = "ai" if self._llm_ok else "templates"
        return {
            "date": self.date.isoformat(),
            "narrators_source": self.source,
            "market": {
                "cap": self.market["cap"],
                "cap_change": self.market["cap_change"],
                "btc_dominance": self.market["btc_dominance"],
                "volume": self.market["volume"],
                "reading": self.market_reading(),
            },
            "coins": coins,
        }


# ─── Formatting helpers ──────────────────────────────────────────────────────

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


def _fmt_abbrev(n: float) -> str:
    n = float(n or 0)
    if n >= 1e12:
        return f"${n/1e12:.2f}T"
    if n >= 1e9:
        return f"${n/1e9:.2f}B"
    if n >= 1e6:
        return f"${n/1e6:.2f}M"
    if n >= 1e3:
        return f"${n/1e3:.2f}K"
    return f"${n:,.0f}"


def _pct_str(val: float) -> str:
    arrow = "▲" if val > 0 else "▼"
    return f"{arrow}{abs(val):.2f}%"


def _pct_color(val: float) -> str:
    if val >= 3:
        return "bold green"
    elif val >= 0:
        return "green"
    elif val >= -3:
        return "red"
    else:
        return "bold red"


# ─── Animated renderer ───────────────────────────────────────────────────────

def _sleep(seconds: float) -> None:
    if ANIMATE:
        time.sleep(seconds)


def _wrap(text: str, pad: int = 4) -> str:
    width = (console.width if console else 80) - pad - 2
    width = max(36, min(width, 78))
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=width) or [""])
    indent = " " * pad
    return "\n".join((indent + ln) if ln else "" for ln in lines)


def _typewriter(text: str, style: str, char_delay: float = 0.015) -> None:
    body = _wrap(text)
    if not ANIMATE:
        console.print(Text(body, style=style), soft_wrap=True)
        return
    for ch in body:
        console.print(Text(ch, style=style), end="", soft_wrap=True)
        sys.stdout.flush()
        if ch != " ":
            time.sleep(char_delay)
    console.print()


def _reveal_persona(persona: dict, speech: str) -> None:
    # 0.4s pause, then the summoning line in dim italic
    _sleep(0.4)
    console.print()
    console.print(Text("    " + persona["summon"], style="dim italic " + persona["accent"]))

    # Portrait, line by line
    for line in persona["art"].splitlines():
        console.print(Text("   " + line, style=persona["art_style"]), soft_wrap=True)
        _sleep(0.05)

    # Name plate
    plate = Text("   ")
    plate.append(f"{persona['glyph']}  {persona['name'].upper()}", style="bold " + persona["accent"])
    plate.append("  ·  ", style="dim")
    plate.append(persona["title"], style="italic dim " + persona["accent"])
    console.print()
    console.print(plate)
    console.print()

    # 0.3s pause, then the speech streams in
    _sleep(0.3)
    _typewriter(speech, persona["speech_style"])


def _coin_stage_header(coin: dict) -> None:
    sym = coin["symbol"]
    glyph = COIN_GLYPHS.get(sym, "◈")

    title = Text()
    title.append(f"  {glyph}  ", style="gold1")
    title.append(coin["name"], style="bold bright_white")
    title.append(f"  {sym}  ", style="dim")
    console.rule(title, style="medium_purple")
    console.print()

    stats = Text("   ", justify="left")
    stats.append(_fmt_price(coin["price"]), style="bold bright_white")
    stats.append("    ")
    for label, val in (("1h", coin["change_1h"]), ("1d", coin["change_1d"]),
                       ("1w", coin["change_1w"]), ("1m", coin["change_1m"])):
        stats.append(f"{label} ", style="dim")
        stats.append(_pct_str(val) + "  ", style=_pct_color(val))
    console.print(stats)
    second = Text("   ")
    second.append("vol ", style="dim")
    second.append(_fmt_abbrev(coin["volume"]), style="bright_white")
    second.append("    mcap ", style="dim")
    second.append(_fmt_abbrev(coin["market_cap"]), style="bright_white")
    second.append(f"    rank #{coin['rank']}", style="dim")
    console.print(second)


def render_rich(reading: dict) -> None:
    """Animated, theatrical terminal output: three narrators per coin."""
    today = datetime.fromisoformat(reading["date"]).strftime("%A, %B %-d, %Y")
    market = reading["market"]

    # ── Header banner ─────────────────────────────────────────────────────
    header_text = Text(justify="center")
    header_text.append("🔮  Crypto Horoscope\n", style="bold gold1")
    header_text.append(f"{today}\n", style="bright_white")
    header_text.append("☿  ·  ♀  ·  🔮", style="dim medium_purple")

    console.print()
    console.print(Panel(Align.center(header_text), border_style="medium_purple", padding=(1, 4)))
    console.print()

    # ── Market overview (scene-setting, not a narrator) ───────────────────
    stats = Table.grid(padding=(0, 3))
    stats.add_column(style="dim")
    stats.add_column(style="bold bright_white")
    stats.add_row("Market Cap", _fmt_abbrev(market["cap"]))
    stats.add_row("Volume 24h", _fmt_abbrev(market["volume"]))
    stats.add_row("BTC Dominance", f"{market['btc_dominance']:.1f}%")
    stats.add_row("24h Change", Text(_pct_str(market["cap_change"]), style=_pct_color(market["cap_change"])))

    console.print(Panel(
        Group(stats, Text(""), Text(market["reading"], style="italic #c9b8f0")),
        title="[bold cyan]✦  The Cosmic Market[/]",
        border_style="cyan",
        padding=(1, 2),
    ))
    console.print()

    intro = Text(justify="center")
    intro.append("Three narrators have gathered to read your coins.", style="dim italic medium_purple")
    console.print(Align.center(intro))
    console.print()

    # ── Per-coin stage: Mercury, Venus, the Oracle ────────────────────────
    for coin in reading["coins"]:
        _coin_stage_header(coin)
        for persona in PERSONAS:
            _reveal_persona(persona, coin["voices"][persona["key"]])
        _sleep(0.5)
        console.print()
        console.rule("✦", style="dim medium_purple")
        console.print()

    # ── Footer ────────────────────────────────────────────────────────────
    src = "AI narrators (Claude)" if reading.get("narrators_source") == "ai" else "built-in narrators"
    console.rule(
        f"[dim]{src}  ·  Powered by [link=https://coinstats.app/api/]CoinStats API[/link]"
        "  ·  Not financial advice. Also not actual astrology.[/]",
        style="dim medium_purple",
    )
    console.print()


def render_plain(reading: dict) -> None:
    """Plain text output for terminals without Rich."""
    today = datetime.fromisoformat(reading["date"]).strftime("%A, %B %d, %Y")
    market = reading["market"]

    sep = "=" * 64
    print(f"\n{sep}")
    print(f"  Crypto Horoscope — {today}")
    print(sep)
    print(f"\n  Market Cap: {_fmt_abbrev(market['cap'])}  ({_pct_str(market['cap_change'])})")
    print(f"  BTC Dominance: {market['btc_dominance']:.1f}%")
    print(f"\n  {market['reading']}\n")

    for coin in reading["coins"]:
        print("\n" + "-" * 64)
        print(f"  {coin['symbol']}  {coin['name']}   {_fmt_price(coin['price'])}"
              f"   1d {_pct_str(coin['change_1d'])}  1w {_pct_str(coin['change_1w'])}")
        print("-" * 64)
        for persona in PERSONAS:
            print(f"\n  {persona['glyph']} {persona['name'].upper()} — {persona['title']}")
            for line in textwrap.wrap(coin["voices"][persona["key"]], width=60):
                print(f"    {line}")

    src = "AI narrators (Claude)" if reading.get("narrators_source") == "ai" else "built-in narrators"
    print(f"\n{sep}")
    print(f"  {src} · Powered by CoinStats API (https://coinstats.app/api/)")
    print("  Not financial advice. Also not actual astrology.")
    print(f"{sep}\n")


def render_share(reading: dict) -> None:
    """Compact share-friendly output for Discord / Slack / Twitter."""
    today = datetime.fromisoformat(reading["date"]).strftime("%b %-d, %Y")
    market = reading["market"]

    lines = [
        f"🔮 Crypto Horoscope — {today}",
        "",
        f"Market: {_fmt_abbrev(market['cap'])}  {_pct_str(market['cap_change'])}  "
        f"BTC dom {market['btc_dominance']:.1f}%",
        "",
    ]
    for coin in reading["coins"]:
        glyph = COIN_GLYPHS.get(coin["symbol"], "◈")
        lines.append(
            f"{glyph} {coin['symbol']} {_fmt_price(coin['price'])}  "
            f"1d {_pct_str(coin['change_1d'])}  1w {_pct_str(coin['change_1w'])}"
        )
        for persona in PERSONAS:
            voice = coin["voices"][persona["key"]]
            snippet = voice if len(voice) <= 150 else voice[:147].rstrip() + "…"
            lines.append(f"  {persona['glyph']} {snippet}")
        lines.append("")

    lines.append("Powered by @CoinStatsApp · coinstats.app/api")
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
    global ANIMATE

    parser = argparse.ArgumentParser(
        description="🔮 Crypto Horoscope: three narrators read your coins from live market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python horoscope.py                      # top coins reading
  python horoscope.py BTC ETH SOL DOGE     # your holdings
  python horoscope.py --share BTC ETH      # shareable text
  python horoscope.py --json BTC ETH       # JSON output
  python horoscope.py --no-animate BTC     # skip the reveal animation

environment:
  COINSTATS_API_KEY    your CoinStats API key (required)
  ANTHROPIC_API_KEY    optional — AI-generated narrator speeches via Claude
  ANTHROPIC_MODEL      optional — model id (default: claude-sonnet-4-6)
        """,
    )
    parser.add_argument("coins", nargs="*", metavar="SYMBOL",
                        help="coin symbols to read (default: top 10 by market cap)")
    parser.add_argument("--share", action="store_true",
                        help="compact shareable output for Discord/Slack/Twitter")
    parser.add_argument("--json", action="store_true", dest="json_out", help="output raw JSON")
    parser.add_argument("--plain", action="store_true", help="plain text output (no Rich)")
    parser.add_argument("--no-animate", action="store_true", dest="no_animate",
                        help="render instantly, without the reveal animation")
    parser.add_argument("--version", action="version", version=f"Crypto Horoscope {VERSION}")
    args = parser.parse_args()

    api_key = get_api_key()
    client = CoinStatsClient(api_key)

    rich_path = HAS_RICH and not args.json_out and not args.share and not args.plain

    try:
        if rich_path:
            with console.status("[dim]Consulting the stars…[/]"):
                all_coins = client.get_top_coins(limit=500)
                market = client.get_market()
                symbols = [s.upper() for s in args.coins] if args.coins else DEFAULT_COINS
                coins = client.filter_by_symbols(all_coins, symbols)
                if coins:
                    stage = NarratorStage(coins, market, date.today())
                    reading = stage.full_reading()
        else:
            all_coins = client.get_top_coins(limit=500)
            market = client.get_market()
            symbols = [s.upper() for s in args.coins] if args.coins else DEFAULT_COINS
            coins = client.filter_by_symbols(all_coins, symbols)
            if coins:
                stage = NarratorStage(coins, market, date.today())
                reading = stage.full_reading()
    except requests.HTTPError as e:
        print(f"API error: {e}")
        sys.exit(1)
    except requests.ConnectionError:
        print("Connection error: check your internet connection.")
        sys.exit(1)

    if not coins:
        print(f"No matching coins found for: {', '.join(symbols)}")
        print("Try common symbols like BTC, ETH, SOL, DOGE, ADA…")
        sys.exit(1)

    # Render
    if args.json_out:
        print(json.dumps(reading, indent=2))
    elif args.share:
        render_share(reading)
    elif args.plain or not HAS_RICH:
        render_plain(reading)
    else:
        ANIMATE = (not args.no_animate) and console.is_terminal
        render_rich(reading)


if __name__ == "__main__":
    main()
