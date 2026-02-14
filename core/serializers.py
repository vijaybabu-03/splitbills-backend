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

# =====================================================
# 🔐 USER PROFILE SERIALIZER
# =====================================================
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        required=False
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "profile_image",
        ]

    # -----------------------------
    # 🔥 VALIDATION
    # -----------------------------
    def validate(self, attrs):
        user_data = attrs.get("user", {})
        username = user_data.get("username")

        # ✅ USERNAME VALIDATION
        if username:
            username = username.strip()

            if User.objects.exclude(id=self.instance.user.id)\
                .filter(username=username)\
                .exists():
                raise serializers.ValidationError({
                    "username": "Username already taken."
                })

        # ✅ PHONE VALIDATION
        phone = attrs.get("phone")

        if phone:
            normalized = "".join(filter(str.isdigit, phone))

            if len(normalized) > 10:
                normalized = normalized[-10:]

            normalized = normalized.lstrip("0")

            if UserProfile.objects.exclude(id=self.instance.id)\
                .filter(phone=normalized)\
                .exists():
                raise serializers.ValidationError({
                    "phone": "Phone number already registered."
                })

            attrs["phone"] = normalized

        return attrs

    # -----------------------------
    # 🔥 UPDATE METHOD
    # -----------------------------
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})

        # Update username safely
        if "username" in user_data:
            new_username = user_data["username"].strip()
            instance.user.username = new_username
            instance.user.save()

        # Update phone
        if "phone" in validated_data:
            instance.phone = validated_data["phone"]

        # Update profile image
        if "profile_image" in validated_data:
            instance.profile_image = validated_data["profile_image"]

        instance.save()
        return instance


# =====================================================
# 👤 USER SERIALIZER
# =====================================================
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


# =====================================================
# 👥 GROUP SERIALIZER
# =====================================================
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


# =====================================================
# 👥 GROUP MEMBER SERIALIZER
# =====================================================
class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_creator = serializers.SerializerMethodField()

    class Meta:
        model = GroupMember
        fields = [
            "id",
            "group",
            "user",
            "joined_at",
            "is_creator",
        ]

    def get_is_creator(self, obj):
        return obj.user == obj.group.created_by


# =====================================================
# 💰 WALLET CONTRIBUTION
# =====================================================
class WalletContributionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = WalletContribution
        fields = "__all__"


# =====================================================
# 💳 WALLET EXPENSE
# =====================================================
class WalletExpenseSerializer(serializers.ModelSerializer):
    added_by = UserSerializer(read_only=True)

    class Meta:
        model = WalletExpense
        fields = "__all__"


# =====================================================
# 🧾 EXPENSE
# =====================================================
class ExpenseSerializer(serializers.ModelSerializer):
    paid_by = UserSerializer(read_only=True)

    class Meta:
        model = Expense
        fields = "__all__"


# =====================================================
# 📊 EXPENSE SPLIT
# =====================================================
class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ExpenseSplit
        fields = "__all__"


# =====================================================
# 🤝 SETTLEMENT
# =====================================================
class SettlementSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = Settlement
        fields = "__all__"
