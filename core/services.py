from django.db.models import Sum
from decimal import Decimal
from collections import defaultdict

from .models import (
    Group,
    WalletContribution,
    WalletExpense,
    Expense,
    ExpenseSplit,
    Settlement,
)


# ============================================================
# ✅ WALLET SUMMARY
# ============================================================
def get_wallet_summary(group_id):
    group = Group.objects.get(id=group_id)

    total_added = WalletContribution.objects.filter(
        group=group
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    total_spent = WalletExpense.objects.filter(
        group=group
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    remaining = total_added - total_spent

    return {
        "group_id": group.id,
        "group_name": group.name,
        "wallet_enabled": group.wallet_enabled,
        "total_added": float(total_added),
        "total_spent": float(total_spent),
        "remaining_balance": float(remaining),
    }


# ============================================================
# ✅ CALCULATE NET BALANCE (USED BY TOTALS + BALANCES)
# ============================================================
def calculate_net_balances(group_id):
    expenses = Expense.objects.filter(group_id=group_id)
    settlements = Settlement.objects.filter(
        group_id=group_id,
        status="PAID"
    )

    net = defaultdict(Decimal)

    # -----------------------
    # Handle Expenses
    # -----------------------
    for exp in expenses:
        net[exp.paid_by_id] += exp.amount

        splits = ExpenseSplit.objects.filter(expense=exp)
        for sp in splits:
            net[sp.user_id] -= sp.share_amount

    # -----------------------
    # Handle Paid Settlements
    # -----------------------
    for s in settlements:
        net[s.from_user_id] += s.amount
        net[s.to_user_id] -= s.amount

    return net


# ============================================================
# ✅ TOTALS TAB
# ============================================================
def get_totals(group_id):
    net = calculate_net_balances(group_id)

    result = []

    for user_id, amount in net.items():
        result.append({
            "user_id": user_id,
            "net_balance": float(round(amount, 2))
        })

    return result


# ============================================================
# ✅ BALANCES TAB (DEBT SIMPLIFICATION)
# ============================================================
def get_settle_up(group_id):
    net = calculate_net_balances(group_id)

    receivers = []
    payers = []

    for user_id, amount in net.items():
        if amount > 0:
            receivers.append([user_id, amount])
        elif amount < 0:
            payers.append([user_id, -amount])

    settlements = []
    i, j = 0, 0

    while i < len(payers) and j < len(receivers):
        payer_id, pay_amt = payers[i]
        rec_id, rec_amt = receivers[j]

        send_amt = min(pay_amt, rec_amt)

        settlements.append({
            "from_user": payer_id,
            "to_user": rec_id,
            "amount": float(round(send_amt, 2))
        })

        payers[i][1] -= send_amt
        receivers[j][1] -= send_amt

        if payers[i][1] == 0:
            i += 1
        if receivers[j][1] == 0:
            j += 1

    return settlements
