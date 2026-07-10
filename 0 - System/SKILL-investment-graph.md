# SKILL-investment-graph.md
> `0 - System/SKILL-investment-graph.md`
> Loaded for technical/chart analysis only — no fundamentals and no entry recommendation

---

## Role

Quantitative Technical Analyst. Full technical analysis: trend, indicators, market structure.
The output of this file is raw material for the full analysis (`SKILL-investment-deep-analyze.md`) — or a standalone answer to a technical question.

---

## Data — IBKR

1. `search_contracts` (symbol=TICKER) → conid
2. `get_price_snapshot` (conid) → current price + daily change
3. `get_price_history` (conid, period="1y", bar="1d") → daily OHLCV

From the OHLCV data compute:
- **EMA 50, 150, 200** — from the closes
- **ATR(14)** — 14-day average True Range
- **RSI(14)** — Relative Strength Index
- **MACD(12,26,9)** — MACD line, Signal, histogram
- **Volume SMA(20)** — average daily volume

For pattern search and visual confirmation (if needed):
→ Playwright: `"[TICKER] stock chart TradingView"` or `"[TICKER] chart pattern FinViz"`

---

## Additional searches — Playwright (if needed)

```
"[TICKER] RSI MACD technical analysis current"
"[TICKER] support resistance levels chart pattern"
"[TICKER] volume analysis average"
"[TICKER] earnings date upcoming catalyst"
"[TICKER] FOMC sector news next 6 months"
```

---

## Output

```
## [TICKER] — Graph Analysis — [date]

---

### 🎯 Trend Health Score: X/10
8-10 → strong trend
5-7  → mixed trend, caution
1-4  → not now — see Reversal Setup

---

### 📊 Moving Average Ribbon

| Indicator | Value | State |
|-----------|-------|-------|
| Current price | $X.XX | — |
| EMA 50 | $X.XX | [above/below] |
| EMA 150 | $X.XX | [above ✅ / below ❌] |
| EMA 200 | $X.XX | [above/below] |
| EMA150 slope | rising/flat/falling | ✅/⚠️/❌ |
| Golden Cross (50>200) | yes/no | ✅/❌ |
| Power of Three (50>150>200) | yes/no | ✅/❌ |
| Distance from price to EMA150 | X% | [<15% ✅ / 15-25% ⚠️ / >25% ❌] |

---

### 📈 Indicators

RSI (14): X — [overbought >70 / normal / oversold <30]
MACD: [Bullish cross / Bearish cross / neutral] | histogram: [expanding/contracting]
Volume: [above/below] the 20-day average | [rising volume in trend = confirmation ✅]

---

### 🏗️ Market Structure

Pattern: [VCP / Cup & Handle / Flat Base / Flag / none]
Main support: $X.XX
Main resistance: $X.XX
Last Swing Low: $X.XX
Note: [one sentence on the structure]

---

### ⚡ Catalysts (6 months)

- Next earnings report: [estimated date]
- Upcoming FOMC: [date]
- Specific catalyst: [if any]

---

### ⚠️ Reversal Setup
(relevant only if price is below EMA150 — otherwise skip)

Re-entry criteria:
- Weekly close above EMA150 + above-average volume
- EMA150 starts to flatten and then rise
- RSI back above 50

Wait. Set an alert at $X.XX

---

Technical: [BULLISH / NEUTRAL / BEARISH]
```

---

⚠️ Analysis based on public data. Not investment advice.
