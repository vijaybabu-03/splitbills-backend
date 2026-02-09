from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import create_group_invite, join_group_with_invite


from .views import (
    register,
    google_login,

    # 🔐 LOGIN (NEW)
    login_with_identifier,

    # 🔐 PASSWORD RESET
    forgot_password,
    reset_password,

    UpiLinkView,
    GroupViewSet,
    GroupMemberViewSet,
    WalletContributionViewSet,
    WalletExpenseViewSet,
    ExpenseViewSet,
    ExpenseSplitViewSet,
    SettlementViewSet,
    UserProfileView,
)

router = DefaultRouter()
router.register("groups", GroupViewSet, basename="groups")
router.register("members", GroupMemberViewSet, basename="members")
router.register(
    "wallet-contributions",
    WalletContributionViewSet,
    basename="wallet-contributions",
)
router.register(
    "wallet-expenses",
    WalletExpenseViewSet,
    basename="wallet-expenses",
)
router.register("expenses", ExpenseViewSet, basename="expenses")
router.register("expense-splits", ExpenseSplitViewSet, basename="expense-splits")
router.register("settlements", SettlementViewSet, basename="settlements")

urlpatterns = [
    # ===============================
    # 🔐 AUTH
    # ===============================
    path("register/", register),
    path("auth/login/", login_with_identifier),
    path("auth/google/", google_login),

    # ===============================
    # 🔐 FORGOT / RESET PASSWORD
    # ===============================
    path("auth/forgot-password/", forgot_password),
    path("auth/reset-password/", reset_password),

    # ===============================
    # 👤 USER PROFILE
    # ===============================
    path("profile/", UserProfileView.as_view(), name="user-profile"),

    # ===============================
    # 📦 CRUD APIs
    # ===============================
    path("", include(router.urls)),

    # ===============================
    # 💸 UPI
    # ===============================
    path("upi-link/", UpiLinkView.as_view(), name="upi-link"),
    # 🔗 INVITES
    path("groups/<int:group_id>/invite/", create_group_invite),
    path("invites/<uuid:token>/join/", join_group_with_invite),

]
