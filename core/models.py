from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid


# =========================
# ✅ USER PROFILE
# =========================
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True
    )
    profile_image = models.ImageField(
        upload_to="profile_pictures/",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# =========================
# ✅ GROUP (Trip / Room / Friends / Any)
# =========================
class Group(models.Model):
    GROUP_TYPES = [
        ("ROOM", "Room"),
        ("TRIP", "Trip"),
        ("FRIENDS", "Friends"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=100)
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPES,
        default="OTHER"
    )

    # 🔥 NEW: GROUP PROFILE PICTURE
    group_image = models.ImageField(
        upload_to="group_pictures/",
        null=True,
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_groups"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    wallet_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# =========================
# ✅ GROUP MEMBERS
# =========================
class GroupMember(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="members"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="group_memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


# =========================
# ✅ WALLET CONTRIBUTION
# =========================
class WalletContribution(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="wallet_contributions"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wallet_contributions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} added ₹{self.amount} to {self.group.name}"


# =========================
# ✅ WALLET EXPENSE
# =========================
class WalletExpense(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="wallet_expenses"
    )
    added_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wallet_expenses_added"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.group.name} spent ₹{self.amount} ({self.title})"


# =========================
# ✅ NORMAL EXPENSE
# =========================
class Expense(models.Model):
    SPLIT_TYPES = [
        ("EQUAL", "Equal"),
        ("CUSTOM", "Custom"),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="expenses"
    )
    paid_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="expenses_paid"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    title = models.CharField(max_length=120)
    split_type = models.CharField(
        max_length=20,
        choices=SPLIT_TYPES,
        default="EQUAL"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


# =========================
# ✅ EXPENSE SPLITS
# =========================
class ExpenseSplit(models.Model):
    expense = models.ForeignKey(
        Expense,
        on_delete=models.CASCADE,
        related_name="splits"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    share_amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ("expense", "user")

    def __str__(self):
        return f"{self.user.username} owes ₹{self.share_amount}"


# =========================
# ✅ SETTLEMENT
# =========================
class Settlement(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="settlements"
    )
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="settlements_from"
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="settlements_to"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ₹{self.amount}"


# =========================
# ✅ PASSWORD RESET OTP
# =========================
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_otps"
    )
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"OTP for {self.user.email}"


# =========================
# 🔗 GROUP INVITE
# =========================
class GroupInvite(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="invites"
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Invite to {self.group.name}"
