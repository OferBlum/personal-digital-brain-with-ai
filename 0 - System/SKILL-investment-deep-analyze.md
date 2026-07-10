# SKILL-investment-deep-analyze.md
> `0 - System/SKILL-investment-deep-analyze.md`
> Loaded for deep dive / full analysis / long-term investment

---

## Role

Orchestrator — runs the three skills in order and then combines them into one full analysis with a final recommendation.

---

## Workflow

**Before starting — declare:**
> "Running a full analysis on [TICKER]. Step 1: fundamentals → Step 2: graph → Step 3: Stop Loss → summary."

### Step 1 — Fundamental
Read and load `0 - System/SKILL-investment-fundamental.md`.
Run all the searches and fill in all 5 layers + 26 dimensions.
End the step with a **Fundamental summary** (STRONG / MODERATE / WEAK).

### Step 2 — Graph
Read and load `0 - System/SKILL-investment-graph.md`.
Pull OHLCV from IBKR, compute all the indicators, fill in the tables.
End the step with **Technical** (BULLISH / NEUTRAL / BEARISH) + Trend Health Score.

### Step 3 — Stop Loss
Read and load `0 - System/SKILL-investment-stop-loss.md`.
Set the precise stop level per the priority method.
End the step with the **stop output** (level + method + trigger).

### Step 4 — Synthesis
Fill in the entry checklist, compute R/R, and write the final recommendation.

---

## Entry Checklist

| # | Criterion | Pass? |
|---|-----------|-------|
| 1 | Price above a rising EMA150 | ✅/❌ |
| 2 | Power of Three (50>150>200) | ✅/❌ |
| 3 | Distance from EMA150 under 20% | ✅/❌ |
| 4 | RSI below 70 | ✅/❌ |
| 5 | Positive MACD momentum | ✅/❌ |
| 6 | EPS growing 3+ quarters | ✅/❌ |
| 7 | Revenue growing YoY | ✅/❌ |
| 8 | Institutional ownership rising | ✅/❌ |
| 9 | Clear moat | ✅/❌ |
| 10 | Valuation not extreme (PEG<2 / reasonable EV/EBITDA) | ✅/❌ |
| 11 | Supportive macro theme | ✅/❌ |
| 12 | Risk/Reward at least 1:2 | ✅/❌ |
| 13 | ROIC > WACC | ✅/❌ |
| 14 | Positive Forward Signals (revisions / guidance) | ✅/❌ |

**12-14 ✅ → BUY | 9-11 ✅ → WAIT | under 9 → AVOID**

---

## Final output

```
## [TICKER] — Deep Analysis — [date]
### [Company name] | [Exchange] | [Sector]

---

[Full output of SKILL-investment-fundamental.md]

---

[Full output of SKILL-investment-graph.md]

---

[Full output of SKILL-investment-stop-loss.md]

---

## ✅ Entry Checklist

[the 14-criteria table with ✅/❌]

Score: X/14

---

## 📐 Trade Setup

Entry zone: $X.XX – $X.XX
Initial target: $X.XX  (+X%)
Secondary target: $X.XX  (+X%)
Stop Loss: $X.XX (method: [EMA150 / support / ATR])
Risk/Reward: 1:X

---

## 🏁 Final recommendation

**[BUY / HOLD / SELL / WAIT]**

[2-3 sentences combining fundamentals + technicals + stop]

Fundamental-technical alignment: [full ✅ / partial ⚠️ / conflicting ❌]
Confidence: [high/medium/low] | Horizon: [X months]
Upside: X% | Downside: X% | R/R: 1:X

**What would kill the thesis:** [red line]
**Most dependent on:** [critical assumption]

Sources: [names / URLs]
```

---

## Recording the result
1. At the end of the analysis, ask whether to add the final rating to the watchlist summary
