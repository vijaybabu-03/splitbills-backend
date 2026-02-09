from django.db.models import Sum
from .models import Group, WalletContribution, WalletExpense
from collections import defaultdict
from .models import Expense, ExpenseSplit


def get_wallet_summary(group_id):
    group = Group.objects.get(id=group_id)

    total_added = WalletContribution.objects.filter(group=group).aggregate(
        total=Sum("amount")
    )["total"] or 0

    total_spent = WalletExpense.objects.filter(group=group).aggregate(
        total=Sum("amount")
    )["total"] or 0

    remaining = total_added - total_spent

    return {
        "group_id": group.id,
        "group_name": group.name,
        "wallet_enabled": group.wallet_enabled,
        "total_added": float(total_added),
        "total_spent": float(total_spent),
        "remaining_balance": float(remaining),
    }

def get_settle_up(group_id):
    """
    Net balance per user:
    + means user should RECEIVE money
    - means user should PAY money
    """
    expenses = Expense.objects.filter(group_id=group_id)

    net = defaultdict(float)

    for exp in expenses:
        paid_by_id = exp.paid_by_id
        net[paid_by_id] += float(exp.amount)

        splits = ExpenseSplit.objects.filter(expense=exp)
        for sp in splits:
            net[sp.user_id] -= float(sp.share_amount)

    # Separate receivers and payers
    receivers = []
    payers = []

    for user_id, amount in net.items():
        if amount > 0:
            receivers.append([user_id, amount])
        elif amount < 0:
            payers.append([user_id, -amount])

    # Create settlement transfers
    settlements = []
    i, j = 0, 0

    while i < len(payers) and j < len(receivers):
        payer_id, pay_amt = payers[i]
        rec_id, rec_amt = receivers[j]

        send_amt = min(pay_amt, rec_amt)

        settlements.append({
            "from_user": payer_id,
            "to_user": rec_id,
            "amount": round(send_amt, 2)
        })

        payers[i][1] -= send_amt
        receivers[j][1] -= send_amt

        if payers[i][1] == 0:
            i += 1
        if receivers[j][1] == 0:
            j += 1

    return settlements
