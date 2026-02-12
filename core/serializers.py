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
    class Meta:
        model = UserProfile
        fields = ["phone", "profile_image"]


# =========================
# USER SERIALIZER
# =========================
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


# =========================
# GROUP SERIALIZER
# =========================
class GroupSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "group_type",
            "group_image",
            "wallet_enabled",
            "created_by",
            "members_count",
            "created_at",
        ]

    def get_members_count(self, obj):
        return obj.members.count()


# =========================
# GROUP MEMBER SERIALIZER
# =========================
class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = [
            "id",
            "group",
            "user",
            "joined_at",
        ]


# =========================
# WALLET CONTRIBUTION
# =========================
class WalletContributionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WalletContribution
        fields = "__all__"


# =========================
# WALLET EXPENSE
# =========================
class WalletExpenseSerializer(serializers.ModelSerializer):
    added_by = UserSerializer(read_only=True)

    class Meta:
        model = WalletExpense
        fields = "__all__"


# =========================
# EXPENSE SERIALIZER
# =========================
class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)

    class Meta:
        model = Expense
        fields = "__all__"


# =========================
# EXPENSE SPLIT
# =========================
class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = "__all__"


# =========================
# SETTLEMENT
# =========================
class SettlementSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = Settlement
        fields = "__all__"
