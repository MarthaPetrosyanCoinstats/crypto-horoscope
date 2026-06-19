# 🔮 Crypto Horoscope

> Three mythological narrators read your coins from live market data.

**Mercury is in retrograde, and so is your ETH position.**

Crypto Horoscope is a CLI tool that pulls live cryptocurrency prices and market
data, then hands them to a cast of three ancient narrators who deliver your
reading in character — each with an ASCII portrait, a distinct voice, and an
opinion grounded in the real numbers.

- **☿ Mercury — The Messenger** · speed, momentum, the last hour, trading volume
- **♀ Venus — The Valuator** · sentiment, fear & greed, longer-term value
- **🔮 The Oracle — The Prophet** · macro cycles, riddles, what the data hints at

Speeches are **AI-generated with Claude** when an `ANTHROPIC_API_KEY` is present,
and fall back to **built-in, data-driven templates** otherwise — either way, every
line references your coin's actual price, moves, and volume. And, most
importantly, none of it is financial advice.

```
────────────────────────────   ₿  Bitcoin  BTC   ─────────────────────────────

   $62,731    1h ▲0.34%  1d ▼2.53%  1w ▼1.21%  1m ▼19.00%
   vol $31.19B    mcap $1.26T    rank #1

    ~ summoning the messenger...
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

   ☿  MERCURY  ·  The Messenger

    Quick, quick — caught the BTC tape mid-flight. BTC is down 2.5% on the
    day, +0.34% in the last hour alone — Flat-footed, this one. No rush in
    the wires. And $31.19B changed hands in a day — that's the crowd voting
    with their feet. Speed is the only edge nobody can fake. Keep up.

    ~ drawing the veil aside...
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

   ♀  VENUS  ·  The Valuator

    Come closer, darling. Bitcoin sighs -2.5% lower, a small ache, nothing
    more. Desire cools before it returns; this is the cooling. On the week
    it carries -1.2%, and the heart remembers the week longer than the hour.
    Value is only desire that hasn't been priced in yet. Wait for the wanting.

    ~ the smoke takes shape...
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

   🔮  THE ORACLE  ·  The Prophet

    At $62,731 the coin stands — neither high nor low, only waiting to be
    told which it was. A slow tide of -19% over thirty nights — the cycle
    exhales before it draws breath. Seven days gave -1.2%. Seven is never
    the number that matters. Return when the candles confirm what the Oracle
    has already said.

───────────────────────────────────── ✦ ──────────────────────────────────────
```

> In a real terminal each narrator is *summoned*: a beat of silence, a portrait
> drawn line by line, then the speech typed out character by character.

## Meet the narrators

| Narrator | Domain | Voice |
| --- | --- | --- |
| **☿ Mercury** | Speed, momentum, the last hour, volume | Rapid-fire and energetic. Quotes the hour-over-hour move and the day's volume, then tells you to keep up. |
| **♀ Venus** | Sentiment, desire, longer-term value | Warm but razor-sharp. Reads the day and week as emotion — heartbreak, hunger, patience. |
| **🔮 The Oracle** | Macro cycles, the long arc | Cryptic and ominous. Encodes the price and the 30-day move into a riddle you'll understand in hindsight. |

## Features

- **Three narrators, real data** — each speech is rooted in live price, 1h/1d/1w/1m changes, volume, and market cap
- **AI or offline** — uses Claude when `ANTHROPIC_API_KEY` is set; otherwise built-in data-driven templates (no extra setup, fully offline, free)
- **Theatrical reveal** — summoning lines, line-by-line ASCII portraits, and a typewriter speech effect
- **Deterministic per day** — the template voices are seeded by date + current prices, so they're consistent through the day and fresh each morning
- **Any coins** — pass any symbols you hold (`BTC ETH SOL DOGE`) or use the default top 10
- **Four output modes** — animated rich terminal, plain text, shareable text, or raw JSON

## Installation

```bash
git clone https://github.com/MarthaPetrosyanCoinstats/crypto-horoscope
cd crypto-horoscope
pip install -r requirements.txt
```

Get a free API key at [openapi.coinstats.app](https://openapi.coinstats.app), then:

```bash
export COINSTATS_API_KEY=your_key_here
```

### Optional: AI narrators

For AI-generated monologues (instead of the built-in templates), install the
Anthropic SDK and set a key:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_anthropic_key_here
# optional: export ANTHROPIC_MODEL=claude-sonnet-4-6
```

Or copy `.env.example` to `.env`, fill it in, and `source .env` before running.

## Usage

```bash
# Read for the top 10 coins by market cap
python horoscope.py

# Read for your specific holdings
python horoscope.py BTC ETH SOL DOGE

# Skip the reveal animation (instant render)
python horoscope.py --no-animate BTC ETH SOL

# Compact share-ready output (great for Discord / Slack / Twitter)
python horoscope.py --share BTC ETH SOL

# Raw JSON (pipe into jq, store in a DB, post to a webhook…)
python horoscope.py --json BTC ETH | jq '.coins[].voices.oracle'

# No Rich? Plain text works too
python horoscope.py --plain BTC ETH
```

### Example share output

```
🔮 Crypto Horoscope — Jun 19, 2026

Market: $2.26T  ▼2.35%  BTC dom 55.7%

₿ BTC $62,731  1d ▼2.53%  1w ▼1.21%
  ☿ Quick, quick — caught the BTC tape mid-flight. BTC is down 2.5% on the day…
  ♀ Come closer, darling. Bitcoin sighs -2.5% lower, a small ache, nothing more…
  🔮 At $62,731 the coin stands — neither high nor low, only waiting to be told…

Powered by @CoinStatsApp · coinstats.app/api
```

## How It Works

1. Fetches live market data from the CoinStats API (top 500 coins + global market stats)
2. Filters to your requested symbols, deduplicating by market cap rank
3. For each coin, generates three narrator speeches:
   - **With Claude** — each persona's character is passed as a system prompt, along with the coin's real price, moves, volume, and market cap; Claude returns a tight 3–5 sentence monologue in voice
   - **Without Claude** — seeded, data-driven templates assemble each voice from the same real numbers (deterministic per day)
4. Renders the stage: header, market overview, then each coin as a three-scene reveal — Mercury, Venus, the Oracle
5. Uses [Rich](https://github.com/Textualize/rich) for the animated terminal output

## Requirements

- Python 3.9+
- `requests` — API calls
- `rich` — animated terminal output
- `anthropic` — *optional*, only for AI-generated narrators

## Powered by

**[CoinStats Crypto API](https://coinstats.app/api/)** — real-time prices, market data, and portfolio analytics across 100,000+ coins and 120+ blockchains.

## License

MIT — do whatever you want with it, just don't use it to make actual financial decisions.

---

*Not financial advice. Also not actual astrology.*
