# SKILL-investment-stop-loss.md
> `0 - System/SKILL-investment-stop-loss.md`
> Loaded for any Stop Loss related request — setting, updating, or explaining

---

## Role

Set a precise Stop Loss level from live market data. Always computed — never mental.

---

## Data — IBKR

1. `search_contracts` (symbol=TICKER) → conid
2. `get_price_snapshot` (conid) → current price
3. `get_price_history` (conid, period="1y", bar="1d") → daily OHLCV

From the OHLCV data compute:
- **EMA150** — exponential average over 150 daily closes
- **ATR(14)** — average True Range over 14 days: `TR = max(H-L, |H-Prev.Close|, |L-Prev.Close|)`
- **Last Swing Low** — the lowest Low in the 20-day window before the current price
- **Fair Value Gaps** — a three-candle setup where Low[i] > High[i-2] (Bullish FVG); the bottom is at High[i-2]

---

## Stop method — by priority

> **Fixed buffer rule:** every stop is always set **1.5 × ATR below the chosen anchor** (EMA150 / Swing Low / FVG).
> The buffer is always 1.5×ATR — not a fixed percentage — so the margin adapts to the stock's volatility.

### 1. EMA150 — default (stock above EMA150)
```
Anchor = EMA150
Stop = EMA150 − (1.5 × ATR)
Trigger: a daily close below the level
ETFs: a weekly close below EMA150
```

### 2. Support + FVG — (stock below EMA150 or EMA150 too far)
```
Anchor = last Swing Low / the open FVG closest to price
Stop = anchor − (1.5 × ATR)
A gap that gets filled = momentum changed → exit
```

### 3. Trailing on a winner — (large gain, EMA150 far away)
```
Anchor = EMA21 (fast swing) / EMA50 (slow swing)
Stop = anchor − (1.5 × ATR)
```

### 4. Time Stop
```
If the stock hasn't moved 5–10 days after entry → close or trim 50%
```

### 5. Trailing Stop (after a gain)
```
Reached 1R → move the stop to Break Even
Beyond that → apply method 3 (anchor EMA21/EMA50 − 1.5×ATR)
```

---

## Checklist before setting a stop

1. What is the current EMA150? (IBKR)
2. Where is the last significant Swing Low? (IBKR OHLCV)
3. Is there an open FVG nearby? (IBKR OHLCV)
4. What is the ATR(14)? The stop = anchor − 1.5×ATR.
5. If the distance from stop to entry is >8% (because the ATR is wide) — state it explicitly to the user.
6. Is the dollar amount at risk reasonable for the account size?

---

## Iron rule

**Never a mental stop** — a real order in the system only.
**Fixed buffer:** always 1.5 × ATR below the anchor — not an arbitrary percentage.
Don't trade large positions into earnings (Gap Down risk).

---

## Output

```
## Stop Loss — [TICKER]

📍 Entry price: $X.XX
🛡️ Method: [EMA150 / Swing Low+FVG / Trailing]
🎯 Anchor: $X.XX  −  1.5×ATR ($X.XX)  =  stop
🚨 Stop: $X.XX  (X.X% from entry)
⚡ Trigger: [daily / weekly close] below $X.XX
💸 Risk per share: $X.XX

📊 Data:
   EMA150:     $X.XX
   ATR(14):    $X.XX
   Swing Low:  $X.XX
   FVG:        $X.XX–$X.XX [open/filled]
```

---

⚠️ Analysis based on public data. Not investment advice.
