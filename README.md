# 🔮 crypto-horoscope

> Your daily cosmic portfolio guidance, powered by real market data.

**Mercury is in retrograde, and so is your ETH position.**

`crypto-horoscope` is a CLI tool that reads live cryptocurrency prices, market sentiment, and your portfolio's performance — then translates it all into the ancient language of astrology. The readings are deterministic per day (same data = same reading), genuinely driven by real numbers, and, most importantly, absolutely not financial advice.

```
──────────────── 🔮  CRYPTO HOROSCOPE  ·  Friday, June 19, 2026 ────────────────

╭──────────────────────────── ✦ THE COSMIC MARKET ─────────────────────────────╮
│  Market Cap: $2.25T  Volume 24h: $77.4B  BTC Dom: 55.7%  Change: ▼1.97%      │
│                                                                               │
│  Mercury dances in retrograde, and your portfolio dances with it — downward. │
╰──────────────────────────────────────────────────────────────────────────────╯

✦ YOUR SIGNS

  ₿ BTC $62,588  1d ▼2.23%  1w ▼1.95%  1m ▼19.20%
  The bears have touched Bitcoin, leaving a mark of -2.2%. Your conviction
  shall be tested.

  ◎ SOL $68.28  1d ▼3.89%  1w ▲1.94%  1m ▼19.46%
  Solana descends 3.9% as Mercury casts shadows across your holdings.

╭──────────────────── ☿ MERCURY'S CURSE — Worst Performer ─────────────────────╮
│  AVAX  ▼8.93% today                                                           │
│  Avalanche has entered its shadow period. Consider burning sage. And your     │
│  position.                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────── 🔮 TODAY'S PROPHECY ─────────────────────────────╮
│  "A pattern forms on the charts. Analysts shall name it something             │
│  confident. They will disagree."                                              │
│                                                                               │
│  Lucky numbers: $7.82  ·  $0.9501  ·  $6.03                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Features

- **Real data, cosmic language** — readings are driven by actual 1h/1d/1w/1m price changes, market cap, BTC dominance, and volume
- **Deterministic per day** — same market data = same reading, seeded by date + current prices
- **Any coins** — pass any symbols you hold (`BTC ETH SOL DOGE`) or use the default top 10
- **Mercury's Curse** — highlights your worst daily performer with appropriately dramatic commentary
- **Venus's Blessing** — celebrates your weekly outperformer
- **Three output modes** — rich terminal, shareable plain text, or raw JSON
- **Zero BS** — no charts to install, no wallet to connect, no data stored

## Installation

```bash
git clone https://github.com/marthastcoinstats/crypto-horoscope
cd crypto-horoscope
pip install -r requirements.txt
```

Get a free API key at [openapi.coinstats.app](https://openapi.coinstats.app), then:

```bash
export COINSTATS_API_KEY=your_key_here
```

Or copy `.env.example` to `.env` and fill it in, then `source .env` before running.

## Usage

```bash
# Read for the top 10 coins by market cap
python horoscope.py

# Read for your specific holdings
python horoscope.py BTC ETH SOL DOGE ADA

# Compact share-ready output (great for Discord / Slack / Twitter)
python horoscope.py --share BTC ETH SOL

# Raw JSON (pipe into jq, store in a DB, post to a webhook…)
python horoscope.py --json BTC ETH | jq '.coins[].reading'

# No Rich? Plain text works too
python horoscope.py --plain BTC ETH
```

### Example share output

```
🔮 CRYPTO HOROSCOPE — Jun 19, 2026

Market: $2.25T  ▼2.00%  BTC dom 55.7%
"Mercury dances in retrograde, and your portfolio dances with it — downward."

₿ BTC $62,588  1d ▼2.23%  1w ▼1.95%
Ξ ETH $1,692   1d ▼3.01%  1w ▲0.92%
◎ SOL $68.28   1d ▼3.89%  1w ▲1.94%

☿ Cursed:  SOL ▼3.89%
♀ Blessed: SOL +1.9% this week

🔮 "A pattern forms. Analysts shall name it confidently. They will disagree."

Powered by @CoinStatsApp · coinstats.app/api
```

## How It Works

1. Fetches live market data from the CoinStats API (top 500 coins + global market stats)
2. Filters to your requested symbols, deduplicates by market cap rank
3. Seeds a deterministic random number generator using today's date + current prices
4. Selects horoscope templates based on actual price movements:
   - Daily/weekly/monthly % changes determine the tone (bullish / bearish / apocalyptic)
   - BTC dominance affects the overall narrative
   - Volume changes trigger special commentary
5. Renders with [Rich](https://github.com/Textualize/rich) for beautiful terminal output

## Requirements

- Python 3.9+
- `requests` — API calls
- `rich` — beautiful terminal output (optional but recommended)

## Powered by

**[CoinStats Crypto API](https://coinstats.app/api/)** — real-time prices, market data, and portfolio analytics across 100,000+ coins and 120+ blockchains.

## License

MIT — do whatever you want with it, just don't use it to make actual financial decisions.

---

*Not financial advice. Also not actual astrology.*
