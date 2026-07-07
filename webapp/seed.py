"""DEV-only sample data, shaped exactly like db.load_all() output.

Lets us build and screenshot the UI locally without Supabase credentials.
The numbers loosely mirror proto.html so visual parity is easy to judge.
"""

from .formulas import current_month_id, parse_month_id


def _mid_offset(months: int) -> str:
    y, m = parse_month_id(current_month_id())
    total = y * 12 + m + months
    return f"m_{total // 12}_{total % 12}"


def sample_data() -> dict:
    mid = current_month_id()
    y, m0 = parse_month_id(mid)
    cats = [
        {"id": "c_housing", "name": "Housing",        "color": "#6366F1", "order": 0},
        {"id": "c_food",    "name": "Food & Dining",  "color": "#10B981", "order": 1},
        {"id": "c_transport", "name": "Transport",    "color": "#F59E0B", "order": 2},
        {"id": "c_savings", "name": "Savings",        "color": "#BF5AF2", "order": 3},
    ]
    buckets = [
        {"id": "b_rent",   "name": "Rent / Mortgage", "catId": "c_housing",   "type": "expense", "order": 0, "archived": False, "dueDay": 1},
        {"id": "b_util",   "name": "Utilities",       "catId": "c_housing",   "type": "expense", "order": 1, "archived": False, "dueDay": 15},
        {"id": "b_groc",   "name": "Groceries",       "catId": "c_food",      "type": "expense", "order": 0, "archived": False},
        {"id": "b_dining", "name": "Dining Out",      "catId": "c_food",      "type": "expense", "order": 1, "archived": False},
        {"id": "b_gas",    "name": "Gas",             "catId": "c_transport", "type": "expense", "order": 0, "archived": False},
        {"id": "b_emerg",  "name": "Emergency Fund",  "catId": "c_savings",   "type": "vault", "order": 0, "archived": False},
    ]
    # Two months of vault history so release/transfer/adjust actions have
    # real prior-month accumulation to draw against, not just this month's
    # own contribution — the exact shape that exposed the RTS bug.
    prev_mid = _mid_offset(-1)
    months = [
        {
            "id": prev_mid,
            "allocations": {"b_emerg": 100},
            "budgets": {},
            "handledBuckets": {}, "vaultWithdrawals": {},
        },
        {
            "id": mid,
            "allocations": {"b_rent": 1500, "b_util": 200, "b_groc": 350, "b_dining": 100, "b_gas": 150, "b_emerg": 50},
            "budgets":     {"b_rent": 1500, "b_util": 300, "b_groc": 400, "b_dining": 100, "b_gas": 200},
            "handledBuckets": {}, "vaultWithdrawals": {},
        },
    ]
    # Dates land early in the month so spending counts today regardless of run date.
    d1 = f"{y}-{(m0 + 1):02d}-01"
    d2 = f"{y}-{(m0 + 1):02d}-02"
    d3 = f"{y}-{(m0 + 1):02d}-03"
    later = f"{y}-{(m0 + 1):02d}-28"
    txs = [
        {"id": "t_inc",  "accountId": "a_check", "type": "in",  "amount": 3200, "monthId": mid, "date": d1, "desc": "Direct Deposit"},
        {"id": "t1", "accountId": "a_check", "bucketId": "b_rent",   "type": "out", "amount": 1500, "monthId": mid, "date": d1, "desc": "Rent Payment"},
        {"id": "t2", "accountId": "a_check", "bucketId": "b_util",   "type": "out", "amount": 140,  "monthId": mid, "date": d2, "desc": "Electric Co"},
        {"id": "t3", "accountId": "a_check", "bucketId": "b_groc",   "type": "out", "amount": 280,  "monthId": mid, "date": d2, "desc": "Whole Foods Market"},
        {"id": "t4", "accountId": "a_check", "bucketId": "b_dining", "type": "out", "amount": 127,  "monthId": mid, "date": d3, "desc": "Restaurant"},
        {"id": "t5", "accountId": "a_check", "bucketId": "b_gas",    "type": "out", "amount": 95,   "monthId": mid, "date": d3, "desc": "Shell"},
        {"id": "t6", "accountId": "a_check", "toAccountId": "a_save", "type": "xfr", "amount": 200, "monthId": mid, "date": d3, "desc": "To Savings"},
        {"id": "t7", "accountId": "a_check", "bucketId": "b_util",   "type": "out", "amount": 60,  "monthId": mid, "date": later, "desc": "Water Bill (scheduled)"},
    ]
    accounts = [
        {"id": "a_check", "name": "Checking", "type": "budget", "openingBalance": 1200, "archived": False},
        {"id": "a_save",  "name": "Savings",  "type": "budget", "openingBalance": 0,    "archived": False},
    ]
    return {
        "accounts": accounts,
        "cats": cats,
        "buckets": buckets,
        "txs": txs,
        "months": months,
        "paychecks": [{"id": "pc1", "label": "Paycheck", "anchorDate": "2026-06-05", "freq": 14, "amount": 1600}],
        "allocationRules": [],
    }


SAMPLE_SESSION = {"access_token": "dev", "user_id": "dev-user", "email": "jdudgeon1993@gmail.com"}
