from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Group,
    GroupMember,
    WalletContribution,
    WalletExpense,
    Expense,
    ExpenseSplit,
    Settlement,
    UserProfile
)

# =========================
# USER PROFILE SERIALIZER
# =========================
class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False)

    class Meta:
        model = UserProfile
        fields = ["profile_image"]


# =========================
# USER SERIALIZER
# =========================
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


# =========================
# GROUP SERIALIZER (🔥 UPDATED)
# =========================
class GroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    group_image = serializers.ImageField(required=False)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "group_type",
            "group_image",      # 🔥 NEW
            "wallet_enabled",
            "created_by",
            "created_at",
        ]


# =========================
# GROUP MEMBER
# =========================
class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMember
        fields = "__all__"


# =========================
# WALLET CONTRIBUTION
# =========================
class WalletContributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletContribution
        fields = "__all__"


# =========================
# WALLET EXPENSE
# =========================
class WalletExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletExpense
        fields = "__all__"


# =========================
# EXPENSE
# =========================
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = "__all__"


# =========================
# EXPENSE SPLIT
# =========================
class ExpenseSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseSplit
        fields = "__all__"


# =========================
# SETTLEMENT
# =========================
class SettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = "__all__"
