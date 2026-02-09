from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    UserProfile,
    Group,
    GroupMember,
    WalletContribution,
    WalletExpense,
    Expense,
    ExpenseSplit,
    Settlement,
)

# =========================
# INLINE PROFILE IN USER
# =========================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = ("phone", "profile_image", "created_at")
    readonly_fields = ("created_at",)


# =========================
# EXTEND USER ADMIN
# =========================
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# =========================
# RE-REGISTER USER
# =========================
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# =========================
# REGISTER OTHER MODELS
# =========================
admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(WalletContribution)
admin.site.register(WalletExpense)
admin.site.register(Expense)
admin.site.register(ExpenseSplit)
admin.site.register(Settlement)
