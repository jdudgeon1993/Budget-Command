# Cura — Budget App: Full Reference Spec

*This document is the complete reference for rebuilding Cura in Python/HTMX. Every formula, concept, and design decision is written in plain English. Jargon is explained when it appears.*

---

## 1. OVERVIEW

Cura is a personal budgeting app built on the **envelope budgeting** philosophy. The core idea is simple: every dollar you earn gets assigned a specific "job" before you spend it. You don't just track what you spent — you decide in advance where each dollar will go.

**Key philosophy points:**

- **Zero-based budgeting**: Income minus all bucket allocations should equal zero. Every dollar is claimed by a bucket before the month begins.
- **Envelope system**: Instead of physical envelopes of cash, "buckets" represent spending categories. You put a fixed amount in each bucket at the start of the month, then spend from that bucket.
- **One cash pool**: All budget account balances are treated as a single pool of money. Allocating money to a bucket doesn't move it to a separate account — it just records that you've mentally earmarked it.
- **Ready to Spend (RTS)**: The app's most important number. RTS = how much of your real cash is not yet claimed by any bucket or future obligation. A positive RTS means you have unallocated money. Zero means every dollar has a job. Negative means you've over-allocated.
- **Forward-looking**: You can pre-allocate money to future months. Pre-allocating next month's rent this month claims that cash from your current pool.

The app is called **Cura**, uses a Blueprint × Brutalist dark UI theme, and supports both desktop (sidebar + content area) and mobile (bottom nav bar + tab panes) layouts. Data is stored in Supabase (PostgreSQL) and cached in localStorage.

---

## 2. DATA MODEL

All data lives in a single JavaScript state object `S` that is serialised to localStorage and synced to a single Supabase row. The Python rebuild should store these as separate database tables.

### 2.1 Accounts

```
{
  id: string,           -- unique ID, e.g. "_abc123"
  name: string,         -- display name, e.g. "Chase Checking"
  type: 'budget' | 'savings' | 'debt',
  color: string,        -- hex color, e.g. "#2a9f60"
  openingBalance: number,  -- starting balance set during onboarding
  debtAPR: number,      -- only for type='debt', annual percentage rate
  debtMinPayment: number,  -- only for type='debt'
  creditLimit: number,  -- optional, only for type='debt' (credit cards)
}
```

**Account types:**
- `budget`: Your main spending accounts (checking, everyday savings). These contribute to the single cash pool that RTS is calculated from.
- `savings`: High-yield savings, money market accounts. Also counted as cash (not debt). Can be reconciled like checking accounts.
- `debt`: Credit cards, loans, any account where the balance represents money you owe. The balance is tracked as a positive number representing the amount owed. Debt accounts are NOT part of the cash pool — they don't increase your RTS.

**Important sign convention for debt accounts:** When calculating account balance, a multiplier of `-1` is applied to transactions on debt accounts. An "out" transaction (paying a bill on a credit card) *increases* what you owe. An "in" transaction (payment toward the card) *decreases* what you owe.

### 2.2 Categories

```
{
  id: string,
  name: string,         -- e.g. "Housing", "Food", "Transportation"
  color: string,        -- hex color used for all buckets in this category
  order: number,        -- display order
}
```

Categories are just organizational groups for buckets. They have no financial logic — they are purely for display and grouping in the budget table.

### 2.3 Buckets

Buckets are the core of the envelope system. Each bucket represents one spending envelope.

```
{
  id: string,
  catId: string,         -- which category this bucket belongs to
  name: string,          -- e.g. "Rent", "Groceries", "Emergency Fund"
  type: 'expense' | 'sinking' | 'goal' | 'vault',
  rollover: boolean,     -- whether unspent money carries forward to next month
  archived: boolean,     -- soft-deleted; hidden but history preserved
  defaultBudget: number, -- the typical monthly allocation target
  dueDay: number | 'eom' | null,   -- day of month payment is due (eom = end of month)
  dueDay2: number | null,          -- second due date for split payments
  dueAmount: number | null,        -- exact amount due on dueDay
  dueAmount2: number | null,       -- exact amount due on dueDay2
  payFreq: 'monthly' | 'weekly' | 'biweekly' | 'triweekly' | null,
  targetAmount: number | null,     -- savings goal target (sinking/goal types)
  targetDate: string | null,       -- "YYYY-MM" target date (sinking/goal types)
  contribFreq: 'monthly' | 'weekly' | 'biweekly' | null,
  recurring: boolean,   -- whether it's a recurring bill
  notes: string | null,
  order: number,
  debtAccountId: string | null,    -- links bucket to a debt account for What-If
}
```

**Bucket types:**

- **`expense`** (also called "regular" in some code paths): A standard monthly expense. Money allocated here is expected to be spent this month. With `rollover: true`, any unspent balance carries forward.
- **`sinking`** (also called "sinking fund"): A bucket where you save a fixed amount each month toward a periodic large expense (e.g., annual car insurance, holiday gifts). The "saved" amount accumulates month over month. Different display from expense: shows cumulative saved vs. target.
- **`goal`**: Like a sinking fund but framed as a one-time savings goal (e.g., vacation, down payment). Shows progress toward a target amount by a target date.
- **`vault`**: An internal savings bucket. Money allocated to a vault stays tracked separately from the main RTS pool. Vaults are used to set aside money for things like an emergency fund or a car replacement fund. Vault money from prior months is *already* in your cash balance (it's real money in the bank) but it's tracked so you can see how much you've built up. The vault accumulation shows how much has been saved. Vault money can be "transferred" to a regular bucket (to cover a planned or unexpected expense) or "released to pool" (to add it back to RTS).

### 2.4 Months

Each month object holds the allocations, budgets, and any rollover-related data for that month. Month IDs follow the pattern `m_YYYY_M` where M is 0-indexed (January = 0, December = 11).

```
{
  id: string,           -- e.g. "m_2025_0" = January 2025
  label: string,        -- e.g. "Jan 2025"
  year: number,
  month: number,        -- 0-indexed
  budgets: {            -- target amount for each bucket this month
    [bucketId]: number
  },
  allocations: {        -- actual amount allocated to each bucket this month
    [bucketId]: number
  },
  rolloverReleased: {   -- amounts deliberately released back to RTS from rollover balances
    [bucketId]: number
  },
  vaultWithdrawals: {   -- amounts withdrawn from vault balances (prior-month savings)
    [bucketId]: number
  },
  vaultFromAllocReleased: {  -- amounts released from THIS month's vault allocation (not prior months)
    [bucketId]: number
  },
  projectedIncome: number | null,  -- manually set or auto-calculated expected income
  skippedBuckets: [string],  -- bucket IDs that are intentionally skipped this month
  closed: boolean,           -- true once month is officially closed
  notes: string | null,
  aiReport: string | null,   -- AI-generated monthly review (stored after close)
  closingSnapshot: {         -- saved at close time for historical records
    date: string,
    cash: number,
    netWorth: number,
    debtTotal: number,
    income: number,
    spent: number,
  }
}
```

**Key distinction — `budgets` vs `allocations`:**
- `budgets[bucketId]` = the *target* amount (what you plan to spend monthly). This is the "budget" column in the UI.
- `allocations[bucketId]` = the *actual amount put into the bucket this month*. This is the editable number in the allocation input. You can allocate less than the budget if cash is tight, or more.

### 2.5 Transactions

```
{
  id: string,
  accountId: string,         -- which account this transaction belongs to
  toAccountId: string | null,  -- for transfers: destination account
  debtPaymentAccountId: string | null,  -- for expense txs that are also debt payments
  monthId: string,           -- which month this falls in (e.g. "m_2025_0")
  bucketId: string | null,   -- which bucket this expense is assigned to
  catId: string | null,      -- (legacy field, prefer using bucket's catId)
  desc: string,              -- description / payee name
  amount: number,            -- always positive
  type: 'in' | 'out' | 'xfr' | 'adjustment' | 'opening',
  date: string,              -- "YYYY-MM-DD"
  recurring: boolean,        -- whether to generate future copies of this tx
  reconciled: boolean | null,
  interestCharge: boolean | null,  -- true for system-generated interest charges
  autoGenerated: boolean | null,   -- true for system-generated transactions
}
```

**Transaction types:**
- `in`: Money coming into a budget account (income, deposits, refunds). These flow into the income pool and affect RTS.
- `out`: Money going out of a budget account (expenses, purchases). Assigned to a bucket to reduce that bucket's available amount.
- `xfr`: A transfer between two of your accounts (e.g., moving money from checking to savings). Does not affect the budget pool total since both accounts are yours.
- `adjustment`: A reconciliation adjustment. Added during month-close to make the app's balance match your bank statement. Positive adjustments increase the account balance; negative ones decrease it.
- `opening`: The opening/starting balance for an account. Treated specially — it's not counted as income or a regular transaction.

**Scheduled transactions (future-dated):** Any transaction where `date > today` is considered "scheduled." Scheduled transactions are shown in the ledger with a special style but are excluded from all balance calculations, bucket spending totals, and RTS. They represent planned future spending.

**`isScheduled` function:** `tx.date > todayStr()` — simple date string comparison.

**`monthId` assignment:** When a transaction is created, its `monthId` is derived from its date. The function `dateToMonthId(dateStr)` parses the date, takes the year and 0-indexed month, and returns `m_YYYY_M`. This means if you log a transaction dated in a different month, it goes into that month's records, not the current one.

**Debt payment transactions:** An expense transaction (type `out`) can also be a payment toward a debt account. In this case, `debtPaymentAccountId` is set. The transaction reduces both the budget account balance *and* the debt account balance. This correctly models paying off a credit card: cash goes out of checking, and the card balance goes down.

### 2.6 Paychecks

```
{
  id: string,
  label: string,       -- e.g. "Main Job", "Freelance"
  amount: number,      -- amount per paycheck
  freq: number,        -- frequency in days: 7 (weekly), 14 (biweekly), 15 (semi-monthly: 1st and 15th)
  anchorDate: string,  -- "YYYY-MM-DD" — a known past pay date to anchor the schedule from
}
```

Paychecks are used to calculate projected monthly income and to power the What-If projector. The `freq=15` case is special: it means semi-monthly, alternating between the 1st and 15th of each month (not every 15 days).

### 2.7 Allocation Rules

Allocation rules define how income is automatically split among buckets when a paycheck arrives.

```
{
  id: string,
  name: string,          -- e.g. "5% to Emergency Fund"
  bucketId: string,      -- which bucket to allocate to
  type: 'pct' | 'fixed', -- percentage of income, or fixed dollar amount
  value: number,         -- the percentage (5 for 5%) or fixed amount ($200)
  active: boolean,
}
```

When a user logs an income transaction, the app prompts them with a "Payday Actions" modal showing all active rules and suggesting how much to allocate. The user can toggle individual rules on or off for that paycheck before confirming.

**Also in the system: Payday Transfers.** These are similar but represent money that actually leaves your account (e.g., auto-transfers to an external savings account). They are displayed in the What-If projector as cash outflows on pay dates but do not create actual transactions.

```
{
  id: string,
  name: string,          -- e.g. "External Savings Transfer"
  type: 'pct' | 'fixed',
  value: number,
  active: boolean,
}
```

### 2.8 Vault Transfers

When you move money from a vault bucket to a regular bucket (to pay for something using saved vault funds), that movement is recorded as a vault transfer.

```
{
  id: string,
  fromBucketId: string,  -- the vault bucket
  toBucketId: string,    -- the destination bucket
  amount: number,
  monthId: string,
  date: string,
  reason: 'planned' | 'overspend',
}
```

Mechanically, a vault transfer reduces the vault's allocation this month and increases the destination bucket's allocation by the same amount. The `vaultTransfers` array is a historical record; the actual allocation numbers are what drive the math.

---

## 3. CORE FORMULAS

### 3.1 Account Balance

The balance of an account is computed from scratch from all posted (non-scheduled) transactions.

```
acctBalance(accountId):

  mult = -1 if account.type == 'debt' else 1

  opening = sum of all opening transactions for this account
  balance = opening (or account.openingBalance if no opening tx)

  for each non-scheduled transaction t (excluding opening type):
    if t.accountId == this account:
      if t.type == 'in':   balance += mult * t.amount
      if t.type == 'out':  balance -= mult * t.amount
      if t.type == 'xfr':  balance -= mult * t.amount
      if t.type == 'adjustment': balance += t.amount  (no mult — adjustments are raw)
    if t.toAccountId == this account and t.type == 'xfr':
      balance += mult * t.amount
    if t.debtPaymentAccountId == this account and t.type == 'out':
      balance -= t.amount  (reduces debt, no mult)
```

For a **budget** account, balance is positive when you have money, negative when overdrawn.

For a **debt** account, balance is positive when you *owe* money. An "out" transaction on a debt account (e.g., swiping a credit card) *increases* what you owe (because the -1 multiplier flips it: `balance -= (-1) * amount = balance += amount`). A payment "in" *decreases* what you owe.

### 3.2 Budget Balance (Total Cash Pool)

```
budgetBal = sum of acctBalance(a) for all accounts where a.type == 'budget'
```

This is the single number representing all real money in your budget accounts. Savings accounts are counted separately (they are included in total cash but treated like budget accounts for most purposes).

### 3.3 Total Cash

```
totalCash = sum of acctBalance(a) for all accounts where a.type != 'debt'
```

Includes budget and savings accounts. Used for display purposes.

### 3.4 Bucket Allocation (bAlloc)

```
bAlloc(monthId, bucketId) = month.allocations[bucketId] or 0
```

The amount allocated to this bucket in this specific month.

### 3.5 Bucket Budget (bBudget)

```
bBudget(monthId, bucketId) = month.budgets[bucketId] or 0
```

The target amount for this bucket this month. Used as a reference point (e.g., "needs $X more").

### 3.6 Bucket Spent (bSpent)

```
bSpent(monthId, bucketId) =
  sum of t.amount for all transactions t where:
    t.monthId == monthId
    t.bucketId == bucketId
    t.type == 'out'
    not isScheduled(t)
```

Only posted (non-future-dated) outflow transactions assigned to this bucket, in this month.

### 3.7 Total Allocated

```
totalAllocated(monthId) = sum of bAlloc(monthId, b.id) for all non-archived buckets
```

### 3.8 Rollover Balance (Raw)

The rollover balance is the accumulated surplus (or deficit) from all **prior** months for a bucket with `rollover = true`.

```
rolloverBalRaw(bucketId, currentMonthId):

  if bucket.rollover is false: return 0

  prior_months = all months before currentMonthId (by year/month)

  total = 0
  for each prior month m:
    if bucket is skipped in m: continue
    alloc = m.allocations[bucketId] or 0
    released = m.rolloverReleased[bucketId] or 0
    spent = bSpent(m.id, bucketId)
    total += (alloc - spent) - released

  return total
```

**Why subtract `released`?** When you release a rollover balance back to the RTS pool, you record the released amount in `m.rolloverReleased[bucketId]` for the *month you're currently in*, not the months where the surplus built up. This prevents that released money from continuing to appear in the rollover balance (which would be double-counting — it was already returned to the pool).

### 3.9 Rollover Balance (Net)

```
rolloverBal(bucketId, monthId):
  raw = rolloverBalRaw(bucketId, monthId)
  released = month.rolloverReleased[bucketId] or 0
  return raw - released
```

This subtracts any rollover amount you've released *in the current month itself*. The current month's released amount is stored in the current month's record, not in the prior months. So `rolloverBalRaw` already subtracts prior-month releases (stored in those prior months' records), and `rolloverBal` additionally subtracts any release you've done in the current month.

### 3.10 Bucket Available

```
bucketAvailable(bucketId, monthId):
  alloc = bAlloc(monthId, bucketId)
  roll = rolloverBal(bucketId, monthId)
  spent = bSpent(monthId, bucketId)
  effectiveBudget = alloc + roll
  available = effectiveBudget - spent
```

This is what shows in the "Available" column. It can be negative if you've overspent.

### 3.11 Effective Budget

```
effectiveBudget(bucketId, monthId) = bAlloc(monthId, bucketId) + rolloverBal(bucketId, monthId)
```

The total amount the bucket has to work with: this month's allocation plus any carry-forward from prior months.

### 3.12 Vault Accumulated

```
vaultAccumulated(bucketId) =
  sum over all months of:
    month.allocations[bucketId] - (month.vaultWithdrawals[bucketId] or 0)
```

The total amount saved in a vault, across all months, minus any withdrawals (releases to pool from prior-month savings). This is the vault's "bank balance."

Note: `vaultFromAllocReleased` is *not* subtracted here because `vaultFromAllocReleased` reduces `allocations` directly (when you release from the current month's vault allocation, the allocation itself is reduced), so the formula automatically accounts for it through the allocation numbers.

### 3.13 Sinking Fund Saved

```
sinkingSaved(bucketId, monthId):
  = rolloverBal(bucketId, monthId) + bAlloc(monthId, bucketId) - bSpent(monthId, bucketId)
```

For sinking funds and goals: the cumulative total saved. This is identical to `bucketAvailable` — it's the same formula, just named differently to make intent clear when displaying sinking fund progress.

### 3.14 Month Income

```
monthIncome(monthId) =
  sum of t.amount for all transactions t where:
    t.monthId == monthId
    t.type == 'in'
    t.accountId is a budget-type account
```

Opening balances, transfers, and expenses on budget accounts are excluded. Only explicit income deposits count.

### 3.15 Total Rollover Released

```
totalRolloverReleased(monthId) =
  sum of all values in month.rolloverReleased
```

Used in the RTS formula to add back releases from future months.

---

## 4. MONTH SYSTEM

### How Months Work

Each month is a separate record. When you view a different month, all the allocation and spending data shown comes from that month's record. Month IDs are strings like `m_2025_0` (January 2025, since months are 0-indexed like JavaScript's `Date` object).

**Month status:** Every month is one of three states:
- `present`: The calendar's current month (today's year and month).
- `past`: Any month before the current calendar month.
- `future`: Any month after the current calendar month.

Status is determined purely by the calendar, not by whether the month is "closed."

### Active Month vs Current Month

`S.activeMonth` is the month the user is *viewing* in the app. This can be different from the current calendar month — users can navigate to past months to review history, or to future months to plan ahead.

`currentMonthId()` always returns today's calendar month ID.

The RTS displayed in the topbar is always computed for today's real position (`todayReadyToSpend()`), not for the month being viewed. This prevents confusing situations where looking at a past month would make it seem like you have more or less money than you actually do.

### Auto-Advance

When the app loads, if `S.activeMonth` is a past month (the user last used the app in a prior month), the app auto-advances to the current calendar month. This ensures the user is always looking at the current month by default when they open the app.

### Creating a Month

`ensureMonth()` creates the current calendar month if it doesn't exist. `addNextMonth()` creates the next month after the last existing one. When a month is created, all buckets get a `budgets` entry (from `bucket.defaultBudget`) and an `allocations` entry of `0`. The user then fills in allocations.

### Closing a Month

The month-close wizard (`confirmCloseMonth`) performs these actions:
1. Posts any interest charges for debt accounts.
2. Optionally raises overspent bucket budgets for future months.
3. Saves a `closingSnapshot` with net worth, income, and spending totals.
4. Sets `month.closed = true`.

A closed month is read-only. Transactions and allocations cannot be changed. To edit a closed month, it must be reopened (no UI for this yet, but the data supports it by setting `closed = false`).

---

## 5. ROLLOVER SYSTEM

### Which Buckets Support Rollover

Only `expense`-type buckets (and potentially `sinking`/`goal` buckets) with `rollover: true` carry forward a balance. Vault buckets have their own accumulation system (see Section 6). Regular expense buckets with `rollover: false` start each month fresh — any unspent money disappears back into the general pool.

### How Surplus Carries Forward

If you allocate $200 to Groceries in January and only spend $150, the $50 surplus is "in" the rollover. In February, `rolloverBal(groceries, February)` returns $50. Your effective budget in February is `bAlloc(February) + $50 rollover`. If you're allocated another $200 in February, you effectively have $250 to spend.

Rollovers can also go negative. If you overspend by $30, the rollover subtracts $30 from next month's effective budget, nudging you to allocate more or spend less to compensate.

### How Releases Work

Sometimes you have a large rollover balance in a bucket you don't need anymore (e.g., you've been saving for an insurance bill that's now been paid). You can "release" that rollover back to the RTS pool.

When you release rollover for bucket B in month M:
- `M.rolloverReleased[B]` is increased by the release amount.
- `rolloverBal(B, M)` decreases immediately (the formula subtracts this from `rolloverBalRaw`).
- RTS increases because the released amount is no longer claimed.

**Why releases are stored in the current month, not prior months:** The rollover balance is calculated as the sum across all prior months. If we subtracted the release from a past month, we'd be altering historical data. Instead, we store the release in the current month and subtract it in the `rolloverBal` formula. The `rolloverBalRaw` function subtracts any releases stored in prior months' `rolloverReleased` maps (those prior releases were made in past viewing sessions). The outer `rolloverBal` function subtracts the current month's release.

### The Double-Counting Issue (Fixed)

**Historical context for the rebuild:** In an earlier version, the RTS formula was adding rollover releases twice:
1. Once via the rolloverBal calculation (releases reduce rolloverBal, which reduces the "claimed" amount, which increases RTS).
2. Once more by explicitly adding releases back to RTS.

The fix: The current RTS formula does NOT separately add current-month releases. Instead, `rolloverBal` already accounts for them. Future-month releases *are* added back to RTS (see Section 9) because `futureClaimed` doesn't use `rolloverBal`.

### Undo Release

`undoReleaseRollover(bucketId, monthId)` simply deletes `month.rolloverReleased[bucketId]`. This restores the rollover balance to what it was before the release, and RTS decreases accordingly.

---

## 6. VAULT SYSTEM

### What a Vault Is

A vault is a special bucket type (`type: 'vault'`) that acts as an internal savings tracker. It answers the question "how much have I set aside for X?" without those savings being part of your normal monthly spending.

Examples: Emergency fund, new car fund, home down payment fund.

**Key property:** Vault money is real money sitting in your bank account. It's part of your `budgetBal`. It is *already included* in your cash balance and therefore already "in" the RTS calculation from prior months. Allocating to a vault this month claims that money from the current RTS pool (just like any other bucket). But prior months' vault allocations are already reflected in your account balance — they're already in the pool.

### Vault Accumulated Formula

```
vaultAccumulated(bucketId) =
  sum over all months of:
    month.allocations[bucketId] - (month.vaultWithdrawals[bucketId] or 0)
```

This shows the total you've built up in the vault over all time.

### How Vault Transfers Work (Vault → Another Bucket)

When you need to use vault savings for something (e.g., your car breaks down and you want to use the car fund):

1. You specify an amount and a destination bucket.
2. The vault's allocation for the current month is reduced by that amount.
3. The destination bucket's allocation for the current month is increased by the same amount.
4. A record is written to `vaultTransfers` for history.

Net effect on RTS: zero (one bucket goes down, another goes up by the same amount).

### How Vault Release to Pool Works (Vault → RTS)

If you decide you don't need the vault savings anymore (e.g., you bought the car, so the car fund is no longer needed) and want the money back in your free pool:

1. First, as much as possible is taken from the **current month's allocation** for that vault.
   - That allocation amount is reduced to zero (or reduced by the release amount).
   - The released-from-current-alloc amount is recorded in `month.vaultFromAllocReleased[bucketId]`.
2. If there's still release amount left (prior-month savings), the remainder is recorded in `month.vaultWithdrawals[bucketId]`.

**Effect on RTS:**
- The current-month allocation reduction immediately adds to RTS (less claimed this month).
- The prior-month withdrawal adjusts `vaultAccumulated` but does NOT directly change RTS. Why? Because prior vault savings were already in the cash pool — they were never subtracted from RTS in the first place (see "Why Prior Month Vault Amounts Are Already in RTS" below).

### Why Prior Month Vault Amounts Are Already in RTS

This is subtle and important. Consider:

- In January, you allocate $500 to your Emergency Fund vault. This is claimed from January's RTS — your RTS goes down by $500.
- The $500 is still in your checking account. It hasn't moved.
- In February, your checking account still has that $500. Your `budgetBal` includes it.
- February's RTS is computed as `budgetBal - curClaimed - futureClaimed`. The $500 in the vault is part of `budgetBal`. But is it in `curClaimed`?

For the **current month**, `curClaimed` uses `bAlloc(currentMonth, vaultId) + rolloverBal(vaultId, currentMonth) - bSpent(currentMonth, vaultId)`. In February, if you don't allocate anything to the vault, `bAlloc = 0` and vault buckets have no rollover, so `curClaimed` for the vault is `0`. The $500 from January is already in `budgetBal` but not in `curClaimed`. So it flows through to RTS automatically — the prior vault savings are already free in the pool as far as RTS is concerned.

This is why "releasing" prior vault savings to pool is really just a bookkeeping operation: it removes the vault record, but it doesn't actually change your cash or your RTS — the money was already available.

### vaultFromAllocReleased Tracking (Needed for Undo)

When releasing from the current month's vault allocation, we need to track how much we took from the allocation (vs. from prior months) so we can undo it correctly:

- **Undo vault release:** Restores `month.vaultWithdrawals[bid]` to 0 and adds `month.vaultFromAllocReleased[bid]` back to `month.allocations[bid]`.

Without `vaultFromAllocReleased`, the undo operation wouldn't know how much of the release came from this month's allocation vs. prior months' savings.

---

## 7. TRANSACTION SYSTEM

### Transaction Types

| Type | Meaning | Effect on RTS |
|------|---------|---------------|
| `in` | Income, deposit, refund | Increases budgetBal → increases RTS |
| `out` | Expense, purchase | Decreases budgetBal; assigned to bucket (reduces available) |
| `xfr` | Transfer between own accounts | Net zero effect (both accounts are yours) |
| `adjustment` | Reconciliation correction | Directly adjusts account balance |
| `opening` | Opening/starting balance | Sets initial account balance |

### Scheduled vs Posted

A transaction is "scheduled" (future-dated) when `tx.date > todayStr()`.

Scheduled transactions:
- Show in the ledger with amber styling.
- Are excluded from all balance, spending, and RTS calculations.
- Represent commitments the user wants to track but that haven't happened yet.
- When the date passes, they automatically become "posted" (no action needed — the formula just uses today's date as the comparison).

### Transfers Between Accounts

A transfer has both `accountId` (source) and `toAccountId` (destination). The source account's balance goes down, the destination goes up. Net effect on total cash: zero. Net effect on RTS: zero (assuming both accounts are budget-type). If transferring from a budget account to a debt account, it reduces what you owe (debt payment).

### Debt Payment Transactions

An expense (type `out`) can have `debtPaymentAccountId` set to a debt account ID. This means:
- The budget account (`accountId`) loses cash.
- The debt account (`debtPaymentAccountId`) is credited — reducing the amount owed.

This correctly models paying a credit card bill: cash leaves checking, card balance goes down.

### How monthId is Assigned

When a transaction is saved, its `monthId` is computed from its `date` field using `dateToMonthId()`. The date is parsed as `YYYY-MM-DD`, and the month is extracted (0-indexed). This means a transaction dated "2025-01-15" gets `monthId = "m_2025_0"` regardless of what month the user is currently viewing.

If the date falls in a month that doesn't have a record yet, that month record is created automatically.

### Recurring Transaction Generation

Transactions with `recurring: true` are flagged, but in the current app, recurring generation is handled by the user creating new entries each month or using the recurring bills feature. The `recurringBills` array (`{id, desc, amount, bucketId, accountId, type, dayOfMonth, active}`) holds bill templates that are referenced in the What-If projector for cash flow planning.

---

## 8. ALLOCATION RULES

Allocation rules automate how income is split among buckets when a paycheck arrives.

### Types

- **Percentage (`pct`)**: A fixed percentage of the income transaction. If the rule is "5% to Emergency Fund" and you log a $2,000 paycheck, the rule suggests $100.
- **Fixed (`fixed`)**: A fixed dollar amount per paycheck. "Save $200 for Vacation" → $200 regardless of paycheck size.

### How They Work

When a user logs an income transaction (type `in`):
1. The app calls `promptAllocationRules(amount, monthId)`.
2. For each active rule, the suggested amount is calculated.
3. A modal appears showing all rules with checkboxes and suggested amounts.
4. The user can toggle individual rules off for this paycheck, or adjust amounts.
5. On confirm, `setAlloc()` is called for each active rule, updating the allocations for the current month.

### Monthly Contribution Estimate

For vault buckets and sinking fund calculations, the app estimates the monthly contribution from allocation rules:

```
vaultMonthlyContrib(bucketId):
  rules = all active allocationRules where rule.bucketId == bucketId

  if no rules:
    # Fall back to average of last 3 months' actual allocations
    return average of recent non-zero allocations

  for each rule:
    paychecksPerMonth = depends on frequency:
      - semi-monthly (freq=15): 2
      - biweekly (freq=14): 30.44 / 14 ≈ 2.17
      - weekly (freq=7): 30.44 / 7 ≈ 4.35

    if rule.type == 'pct':
      contribution += (rule.value / 100) * paycheck.amount * paychecksPerMonth
    if rule.type == 'fixed':
      contribution += rule.value * paychecksPerMonth
```

For sinking fund contribution frequency:
- `monthly`: monthly contribution = bucket's defaultBudget
- `biweekly`: monthly contribution = `defaultBudget * 12 / 26`
- `weekly`: monthly contribution = `defaultBudget * 12 / 52`

---

## 9. READY TO SPEND — DETAILED BREAKDOWN

Ready to Spend (RTS) is the most important number in the app. It answers: **"How much of my actual cash is not yet spoken for?"**

A positive RTS means you have unallocated money. Zero means every dollar has a job. Negative means you've over-allocated (you've promised more than you have).

### Current Month Formula (Step by Step)

```
readyToSpend(activeMonthId):

  # Step 1: Get the real cash on hand
  budgetBal = sum of acctBalance(a) for all budget accounts

  # Step 2: Calculate current month obligations
  # For each bucket, how much is still "owed" this month?
  # max(0, ...) ensures overspent buckets don't give us credit — they already
  # left the bank, so budgetBal is already lower.
  curClaimed = sum over all non-archived buckets of:
    max(0, bAlloc(activeMonth, bucket) + rolloverBal(bucket, activeMonth) - bSpent(activeMonth, bucket))

  # Step 3: Calculate future month obligations
  # Future pre-allocations also claim from the same real cash pool
  futureClaimed = sum over all months AFTER activeMonth of:
    sum over all non-archived buckets of:
      bAlloc(futureMon, bucket)   # NOTE: no rolloverBal here — see below

  # Step 4: Add back releases from future months
  # futureClaimed doesn't include rolloverBal, so future released amounts
  # (which reduce rolloverBal) aren't naturally excluded — we add them back
  futureReleased = sum over all months AFTER activeMonth of:
    sum of all values in month.rolloverReleased

  # Final result
  return budgetBal - curClaimed - futureClaimed + futureReleased
```

### Why curClaimed Uses max(0, ...)

If you've overspent a bucket by $50 (spent $150, allocated $100), the bucket available is -$50. But that $50 already left your bank account — `budgetBal` is already $50 lower. If we counted -$50 in `curClaimed`, it would double-subtract: once from `budgetBal` (the real outflow) and once from the claimed total. By capping at 0, we ensure overspent buckets don't affect RTS — their impact is already captured in `budgetBal`.

### Why futureClaimed Only Uses bAlloc (No rolloverBal)

Future months' rollover balances are not real cash allocations from the future — they represent surpluses from prior months that have already been "claimed" as part of the current month's `curClaimed`. Adding `rolloverBal` to `futureClaimed` would double-count money that's already accounted for in `curClaimed`.

Example: If you have a $100 rollover going into next month, that $100 is already subtracted in `curClaimed` (it's part of what's "owed" this month). If we also added it to `futureClaimed`, we'd subtract it twice.

### Why futureReleased Is Added

When you release a rollover from a future month, that release reduces `rolloverBal` for that future bucket. But since `futureClaimed` doesn't use `rolloverBal`, the reduction has no effect on `futureClaimed` by itself. Without adding `futureReleased` back, releasing future rollover would have no effect on RTS — money would be released but never show up as available. The fix is to explicitly add back `totalRolloverReleased` for each future month.

### Why Current Month Releases Aren't Added Separately

Current month rollover releases are already handled: `rolloverBal` subtracts the current month's `rolloverReleased` from the raw rollover total. So `curClaimed` is automatically lower (less claimed) when you release current-month rollover. No explicit `+released` is needed in the current month.

### Past Month Formula

When viewing a past month, RTS shows what the situation was for that historical month:

```
readyToSpend(pastMonthId):
  budgetBal = current real cash (not historical — still uses today's balance)
  unfulfilled = sum over all non-archived buckets of:
    max(0, bAlloc(pastMonth, bucket) + rolloverBal(bucket, pastMonth) - bSpent(pastMonth, bucket))
  return budgetBal - unfulfilled
```

The past month view uses today's real cash minus the unfulfilled obligations from that past month. This is a historical perspective: "If I had only done that month's allocations, what would be free?" It's less intuitive than the current-month formula and mainly used for review.

### What "Claiming" Means Conceptually

"Claiming" is the mental model for envelope budgeting. When you allocate $500 to rent, you're "claiming" $500 of your cash — it's no longer free to spend elsewhere. The rent claim doesn't move money; it just designates it.

- `curClaimed`: All of this month's unfulfilled designations (allocated but not yet spent).
- `futureClaimed`: All future months' designations (pre-allocated for coming months).
- The difference between `budgetBal` and all claims = RTS = truly free cash.

### todayReadyToSpend vs readyToSpend

`todayReadyToSpend()` is memoized (cached per render cycle) and always uses `currentMonthId()` as the active month. It's used in the topbar, which should always show today's real position regardless of which month the user is viewing.

`readyToSpend(mid)` takes a month ID and adjusts if viewing a past month. Used for the main content area.

---

## 10. SINKING FUNDS & GOALS

### Sinking Funds (type = 'sinking')

A sinking fund is for recurring large expenses you save toward month by month. Examples: annual car insurance, holiday gifts, quarterly taxes.

**Display:**
- Shows cumulative saved (`sinkingSaved`) vs. target.
- Shows months remaining and required monthly contribution.
- Progress bar toward target.

**Calculation:**

```
sinkingSaved(bucketId, monthId):
  = rolloverBal(bucketId, monthId) + bAlloc(monthId, bucketId) - bSpent(monthId, bucketId)
```

This is the same as `bucketAvailable`. The semantics differ: for a regular bucket, "available" means "can spend this month." For a sinking fund, it means "how much we've saved toward the goal."

**Months remaining and monthly need:**

```
months_left = (targetDate.year - today.year) * 12 + (targetDate.month - today.month)
monthly_needed = ceil((targetAmount - currentlySaved) / months_left)
```

### Goals (type = 'goal')

Goals work identically to sinking funds mathematically. The difference is intent and display framing: a goal is a one-time milestone (vacation, emergency fund target) rather than a recurring expense. The progress display emphasizes the percentage toward the goal rather than the monthly contribution rhythm.

**Contribution frequency:**

The `contribFreq` field allows expressing the saving rhythm: `monthly`, `weekly`, or `biweekly`. This affects how the contribution amount is displayed and how the What-If projector schedules the saving events.

```
contribAmt(bucket):
  monthly = bucket.defaultBudget
  if contribFreq == 'weekly': return monthly * 12 / 52
  if contribFreq == 'biweekly': return monthly * 12 / 26
  return monthly
```

### Goal Celebrations

When a goal bucket's `sinkingSaved` value reaches or exceeds `targetAmount`, the app triggers a toast notification congratulating the user. The celebration is tracked in `S.celebratedGoals` (an array of `bucketId + '_' + monthId` strings) to avoid showing it again on re-render.

---

## 11. BUILD PHASES

### Phase 1 — Documentation (FORMULAS.md + README) ✓

**What gets built:** This document and a README describing the project.

**Depends on:** Reading and understanding the original index.html source.

**Definition of done:** FORMULAS.md exists at /home/user/Budget-Command/FORMULAS.md. All formulas, data models, and design decisions are documented. Someone unfamiliar with the codebase can read this and understand how the app works.

---

### Phase 2 — New App Skeleton (app.py + base template + warning strip) ✓

**What gets built:**
- Flask app with login/logout/dashboard routes.
- Supabase Python client for database access.
- Base Jinja2 HTML template with the Blueprint × Brutalist theme.
- Authentication flow: login page, session management.
- DEV warning strip on the original app (mobile + desktop).
- HTMX included in the base template.
- Health check endpoint at `/health`.

**Depends on:** Phase 1.

**Definition of done:** App skeleton exists, auth routes work, base template matches original theme, warning strip visible on both layouts. Railway config files in place.

---

### Phase 3 — Railway + Supabase Live (Deploy First, Build Second) ✓

**What gets built:**
- `railway.toml` with gunicorn start command and health check.
- `requirements.txt` with gunicorn added.
- App configured to read `PORT` env var from Railway.
- Environment variables set in Railway dashboard.
- Public Railway URL wired into the warning strip in the original app.

**Depends on:** Phase 2 (working skeleton to deploy).

**Definition of done:** The app is live on Railway, the login screen loads over HTTPS, Supabase auth works (can sign in with real credentials), and the original app's strip links directly to the live URL. Every phase from here is testable immediately after each push.

---

### Phase 4 — Dashboard (Read-only, Desktop Only)

**What gets built:**
- Desktop layout: sidebar with nav + main content area.
- Dashboard tab: RTS card, Accounts card, Buckets summary, Recent ledger, 12-Month Horizon.
- All data read from Supabase (no editing yet).
- All core formula functions translated to Python.
- Month navigation (prev/next/jump-to-today).
- Sidebar vitals: RTS, total cash, age of money.

**Depends on:** Phase 3 (live Railway URL, Supabase connection confirmed working).

**Definition of done:** The dashboard loads with real data on Railway, all key numbers (RTS, cash, allocations, spending) match the original app for the same data. Month navigation works. No editing features yet.

---

### Phase 5 — Buckets (Core Feature, Allocation Logic)

**What gets built:**
- Buckets tab: category groups, bucket rows, allocation inputs.
- Setting allocations (HTMX post, inline update).
- Rollover balance display and release.
- Bucket detail sheet (stats, transaction list for that bucket, rollover history).
- Vault bucket display with accumulated balance.
- Bucket create/edit/archive modal.
- Category create/edit/delete.
- "Fund category" shortcut button.
- Budget health bar (projected income vs. total allocated).

**Depends on:** Phase 4 (all formula functions must be correct).

**Definition of done:** Users can view and edit allocations. RTS updates live when allocations change. Rollover buckets show correct carry-forward. Vaults show accumulated balance. Creating and editing buckets works.

---

### Phase 6 — Transactions (Bread and Butter)

**What gets built:**
- Ledger tab: transaction list grouped by date, filtered by month.
- Add transaction form (description, amount, date, account, type, bucket assignment).
- Edit and delete transactions inline.
- Scheduled transaction handling (future-dated, shown differently).
- Transfer transactions (between accounts).
- Debt payment transactions.
- Bucket assignment from the ledger (inline expand row).
- Ledger search and filter (by type, account, bucket).
- Payee autocomplete and memory (suggest bucket based on past payee).
- Month-close wizard (uncategorized check, account reconciliation, rollover preview).

**Depends on:** Phase 5 (bucket list needed for assignment dropdowns).

**Definition of done:** Users can add, edit, delete all transaction types. Assigning to buckets updates bucket available in real time. Month-close flow works. Account balances match after reconciliation.

---

### Phase 7 — Auth (Complete) + Settings

**What gets built:**
- User-scoped data (all Supabase queries filter by user ID — verify no data leakage).
- Session persistence (survives page refresh, expires on logout).
- Settings page: accounts CRUD, paycheck schedule management, allocation rules, recurring bills.
- AI Coach integration (Gemini API key input, model selection, tone preference).
- Natural language transaction parsing.
- Reports tab: cash flow chart, category spending chart, YTD chart, net worth chart.
- What-If / Scenarios tab (scenario builder, 12-month projector).
- Onboarding wizard (first-time setup flow).

**Depends on:** Phase 6 (all core data must be editable before settings make sense).

**Definition of done:** All settings are editable and persist. Reports render with correct data. Multiple users can log in independently. AI coach responds with budget context.

---

### Phase 8 — Polish + Launch

**What gets built:**
- Mobile layout (bottom nav bar, tab panes matching original).
- Performance pass (query optimization, caching heavy formula results).
- Error handling and empty states throughout.
- Export/PDF report generation.
- Final deploy: swap the warning strip to a "Try the new version" link pointing at the live Railway URL.
- Sunset plan for the original index.html.

**Depends on:** All previous phases.

**Definition of done:** The new app is feature-complete and matches or exceeds the original. The original app's strip links to the live build. The rebuild can be used as the primary app.

---

## 12. DESIGN DECISIONS & LESSONS LEARNED

### Why localStorage Must Be User-Scoped (The Privacy Bug and Fix)

**The bug:** Early in development, localStorage used a single key (`bcc_v6`) for all users on the same browser. If Alice and Bob both used the app on the same computer, Alice's data would overwrite Bob's when Bob logged in, and vice versa.

**The fix:** The localStorage key is now user-scoped: `bcc_v6_u_<userId>`. The function `localKey()` returns the user-scoped key when a Supabase user is authenticated, and falls back to the generic key only briefly during the startup window before auth is established.

**Additionally:** On sign-out, the user's localStorage cache is explicitly cleared. Supabase is the source of truth; localStorage is only an offline fallback.

**For the Python rebuild:** This problem doesn't exist in the same form — server-side sessions handle user isolation. But if you ever cache anything client-side (e.g., in cookies or localStorage for offline support), make sure it's user-scoped.

### Why loadFromSupabase() Resets S Before Loading (Prevents Stale Data Contamination)

When the app loads from Supabase, the first thing it does is reset `S` to an empty state. This prevents a subtle bug: if the app starts up and loads the old generic localStorage cache (pre-auth), then the Supabase load overwrites it — but only the fields that exist in the Supabase data. Any fields that were in the old cache but not in Supabase would persist as "stale data" from the previous user's session.

By resetting `S = {}` before the Supabase load, we guarantee a clean slate. The trade-off is a brief flash of empty UI before data arrives, which is acceptable.

### Why Rollover Releases Are Stored in the Destination Month Not the Source Months

When you release a rollover balance, you're looking at a bucket's history across many months. The surplus might have built up over 6 months. Rather than trying to figure out which specific past months to subtract from (which would require complex allocation of the release across historical records), the release is recorded in the **current month's** `rolloverReleased` field.

The `rolloverBal` formula then subtracts this from the raw rollover total. This is simpler and keeps historical data immutable — past months' records never change after the fact. The "release" is a forward-looking adjustment, not a retroactive correction.

### Why Vault Money From Prior Months Is Already in RTS (Not in curClaimed)

Vault buckets do not have `rollover: true`. This means `rolloverBal` for a vault bucket is always 0. Prior months' vault allocations are not carried forward as claims against the current month.

The money is already in your bank account (it was never moved out), and since it's not in `curClaimed`, it flows freely into RTS from `budgetBal`. This is intentional: the vault is not a separate account — it's a mental tracking system. The money is yours, it's in your bank, and it's available as cash. The vault just tells you "this chunk of your bank balance is earmarked for X."

When you make a new allocation to a vault this month, *that* allocation is claimed (it goes into `curClaimed` for the current month). So new vault contributions correctly reduce RTS, but accumulated prior savings don't.

### The Single-File Architecture Problem and Why We're Rebuilding

The original Cura app is a single `index.html` file with roughly 12,500 lines of CSS, HTML, and JavaScript all in one place. This was practical for a solo project that started small, but it has become unmaintainable:

- **No separation of concerns**: CSS, HTML structure, and business logic are interleaved.
- **No testability**: All formulas are JavaScript functions in one giant scope — no unit tests possible.
- **Deployment complexity**: Updating any part requires redeploying the entire file and busting caches everywhere.
- **No server-side rendering**: The entire app runs client-side, which causes a flash of empty content on every page load while data is fetched from Supabase.

The Python/HTMX rebuild solves all of these:
- Python functions for all formulas (testable with pytest).
- Jinja2 templates for HTML (separate, composable).
- CSS in separate files (organized by component).
- HTMX for partial page updates (no custom JavaScript framework needed).
- Server-side rendering (data is ready when the HTML arrives).

### Why What-If / Scenarios Was Kept But Not Rebuilt Yet

The What-If / Scenarios feature (Phase 7) is a complex projector that simulates future cash flow based on your paycheck schedule, bucket budgets, and hypothetical changes (different income, extra spending, turning buckets on/off by date). It's powerful but complex to build and rarely used by new users.

The decision was to prioritize the core loop (dashboard → buckets → ledger) first and add What-If in Phase 7. This allows the rebuild to be useful sooner, and the Scenarios feature can be validated against the original app's output once all the core formulas are working.

---

*End of FORMULAS.md — last updated 2026-05-20.*
