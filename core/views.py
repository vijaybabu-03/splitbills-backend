import json
import urllib.parse
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.utils.timezone import now
from .models import GroupInvite
from django.shortcuts import get_object_or_404


from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny


from google.oauth2 import id_token
from google.auth.transport import requests

from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Group,
    GroupMember,
    WalletContribution,
    WalletExpense,
    Expense,
    ExpenseSplit,
    Settlement,
    UserProfile,
    PasswordResetOTP,
)

from .serializers import (
    GroupSerializer,
    GroupMemberSerializer,
    WalletContributionSerializer,
    WalletExpenseSerializer,
    ExpenseSerializer,
    ExpenseSplitSerializer,
    SettlementSerializer,
    UserProfileSerializer,
)

from .services import get_wallet_summary, get_settle_up


# =====================================================
# 🔐 LOGIN WITH USERNAME / EMAIL / PHONE
# =====================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def login_with_identifier(request):
    identifier = request.data.get("identifier")
    password = request.data.get("password")

    if not identifier or not password:
        return Response(
            {"error": "identifier and password required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(username=identifier).first()

    if not user:
        user = User.objects.filter(email=identifier).first()

    if not user:
        profile = UserProfile.objects.filter(phone=identifier).first()
        if profile:
            user = profile.user

    if not user or not user.check_password(password):
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        status=status.HTTP_200_OK,
    )


# =====================================================
# 🔵 GOOGLE LOGIN
# =====================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def google_login(request):
    token = request.data.get("token")

    if not token:
        return Response({"error": "Google token required"}, status=400)

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,  # 👈 IMPORTANT
        )

        if idinfo["iss"] not in [
            "accounts.google.com",
            "https://accounts.google.com",
        ]:
            return Response({"error": "Invalid issuer"}, status=400)

        if idinfo["aud"] != settings.GOOGLE_CLIENT_ID:
            return Response({"error": "Invalid audience"}, status=400)

    except ValueError:
        return Response({"error": "Invalid Google token"}, status=400)

    email = idinfo.get("email")
    name = idinfo.get("name", "")

    if not email:
        return Response({"error": "Email not found"}, status=400)

    user, created = User.objects.get_or_create(
        username=email,
        defaults={"email": email, "first_name": name},
    )

    if created:
        user.set_unusable_password()
        user.save()
        UserProfile.objects.create(user=user)

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        status=200,
    )


# =====================================================
# ✅ REGISTER
# =====================================================
@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def register(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email", "")
    raw_phone = request.data.get("phone")
    phone = None

    if raw_phone:
        phone = "".join(filter(str.isdigit, raw_phone))

        if len(phone) > 10:
            phone = phone[-10:]

        phone = phone.lstrip("0")

    profile_image = request.FILES.get("profile_image")

    if not username or not password:
        return Response({"error": "username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "username already exists"}, status=400)

    if phone and UserProfile.objects.filter(phone=phone).exists():
        return Response({"error": "phone already registered"}, status=400)

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
    )

    UserProfile.objects.create(
        user=user,
        phone=phone,
        profile_image=profile_image,
    )

    return Response({"message": "User registered successfully"}, status=201)


# =====================================================
# 🔐 FORGOT PASSWORD
# =====================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get("email")

    if not email:
        return Response({"error": "Email required"}, status=400)

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    otp = random.randint(100000, 999999)

    PasswordResetOTP.objects.filter(user=user, is_used=False).delete()

    PasswordResetOTP.objects.create(user=user, otp=str(otp))

    send_mail(
        subject="SplitBills Password Reset OTP",
        message=f"Your OTP is {otp}. It is valid for 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response({"message": "OTP sent"}, status=200)


# =====================================================
# 🔁 RESET PASSWORD
# =====================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get("email")
    otp = request.data.get("otp")
    password = request.data.get("password")

    if not email or not otp or not password:
        return Response({"error": "All fields required"}, status=400)

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({"error": "User not found"}, status=404)

    otp_obj = PasswordResetOTP.objects.filter(
        user=user, otp=otp, is_used=False
    ).first()

    if not otp_obj:
        return Response({"error": "Invalid OTP"}, status=400)

    if otp_obj.is_expired():
        otp_obj.delete()
        return Response({"error": "OTP expired"}, status=400)

    user.set_password(password)
    user.save()

    otp_obj.is_used = True
    otp_obj.save()

    return Response({"message": "Password reset successful"}, status=200)


# =====================================================
# ✅ UPI LINK
# =====================================================
class UpiLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        upi_id = request.query_params.get("upi_id")
        name = request.query_params.get("name", "User")
        amount = request.query_params.get("amount", "0")
        note = request.query_params.get("note", "Settle Up")

        if not upi_id:
            return Response({"error": "upi_id required"}, status=400)

        params = {
            "pa": upi_id,
            "pn": name,
            "am": amount,
            "cu": "INR",
            "tn": note,
        }

        return Response({"upi_link": "upi://pay?" + urllib.parse.urlencode(params)})


# =====================================================
# ✅ USER PROFILE
# =====================================================
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(UserProfileSerializer(profile).data)

    def put(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# =====================================================
# ✅ GROUPS (🔥 FIXED – CREATE WORKS)
# =====================================================
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets

from .models import Group, GroupMember
from .serializers import GroupSerializer
from .services import get_wallet_summary, get_settle_up


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # User can SEE only groups they belong to
        return Group.objects.filter(
            members__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        # Creator is always added as member
        group = serializer.save(created_by=self.request.user)
        GroupMember.objects.create(
            group=group,
            user=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()

        # 🔒 ONLY CREATOR CAN DELETE
        if group.created_by != request.user:
            return Response(
                {"detail": "Only group creator can delete this group"},
                status=status.HTTP_403_FORBIDDEN,
            )

        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        return Response(get_wallet_summary(pk))

    @action(detail=True, methods=["get"])
    def settle_up(self, request, pk=None):
        return Response(get_settle_up(pk))

# =====================================================
# ✅ OTHER VIEWSETS (UNCHANGED)
# =====================================================
class GroupMemberViewSet(viewsets.ModelViewSet):
    serializer_class = GroupMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        group_id = self.request.query_params.get("group")
        queryset = GroupMember.objects.filter(
            group__members__user=self.request.user
        )

        if group_id:
            queryset = queryset.filter(group_id=group_id)

        return queryset

    def create(self, request, *args, **kwargs):
        group_id = request.data.get("group")
        identifier = request.data.get("identifier")

        if not group_id or not identifier:
            return Response(
                {"detail": "group and identifier required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response(
                {"detail": "Group not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not GroupMember.objects.filter(
            group=group, user=request.user
        ).exists():
            return Response(
                {"detail": "You are not a member of this group"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = None

        user = User.objects.filter(username=identifier).first()

        if not user:
            user = User.objects.filter(email=identifier).first()

        if not user:
            normalized = "".join(filter(str.isdigit, identifier))

            if len(normalized) > 10:
                normalized = normalized[-10:]

            normalized = normalized.lstrip("0")

            profiles = UserProfile.objects.exclude(phone__isnull=True)

            for profile in profiles:
                stored = "".join(filter(str.isdigit, profile.phone))

                if len(stored) > 10:
                    stored = stored[-10:]

                stored = stored.lstrip("0")

                if stored == normalized:
                    user = profile.user
                    break

        if not user:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if GroupMember.objects.filter(group=group, user=user).exists():
            return Response(
                {"detail": "User already in group"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member = GroupMember.objects.create(group=group, user=user)

        return Response(
            GroupMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        member = self.get_object()
        group = member.group

        if group.created_by != request.user:
            return Response(
                {"detail": "Only group creator can remove members"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if member.user == group.created_by:
            return Response(
                {"detail": "Creator cannot remove themselves"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member.delete()

        return Response(
            {"detail": "Member removed successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class WalletContributionViewSet(viewsets.ModelViewSet):
    queryset = WalletContribution.objects.all()
    serializer_class = WalletContributionSerializer
    permission_classes = [IsAuthenticated]


class WalletExpenseViewSet(viewsets.ModelViewSet):
    queryset = WalletExpense.objects.all()
    serializer_class = WalletExpenseSerializer
    permission_classes = [IsAuthenticated]


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Expense.objects.all()
        group_id = self.request.query_params.get("group")
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        group_id = request.data.get("group")
        title = request.data.get("title")
        amount = request.data.get("amount")

        if not group_id or not title or not amount:
            return Response(
                {"detail": "group, title and amount are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1️⃣ Validate group
        group = Group.objects.filter(id=group_id).first()
        if not group:
            return Response(
                {"detail": "Group not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2️⃣ Validate membership
        if not GroupMember.objects.filter(
            group=group, user=request.user
        ).exists():
            return Response(
                {"detail": "You are not a member of this group"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3️⃣ Create expense (paid_by = logged-in user)
        expense = Expense.objects.create(
            group=group,
            paid_by=request.user,
            title=title,
            amount=amount,
            split_type="EQUAL",
        )

        # 4️⃣ Equal split
        members = GroupMember.objects.filter(group=group)
        share = expense.amount / members.count()

        for member in members:
            ExpenseSplit.objects.create(
                expense=expense,
                user=member.user,
                share_amount=share,
            )

        return Response(
            ExpenseSerializer(expense).data,
            status=status.HTTP_201_CREATED,
        )




class ExpenseSplitViewSet(viewsets.ModelViewSet):
    queryset = ExpenseSplit.objects.all()
    serializer_class = ExpenseSplitSerializer
    permission_classes = [IsAuthenticated]


class SettlementViewSet(viewsets.ModelViewSet):
    queryset = Settlement.objects.all()
    serializer_class = SettlementSerializer
    permission_classes = [IsAuthenticated]
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_group_invite(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Only members can invite
    if not GroupMember.objects.filter(
        group=group, user=request.user
    ).exists():
        return Response(
            {"detail": "Not allowed"},
            status=status.HTTP_403_FORBIDDEN
        )

    invite = GroupInvite.objects.create(
        group=group,
        created_by=request.user,
    )

    invite_link = f"https://splitbills.app/invite/{invite.token}"

    return Response({
        "invite_link": invite_link,
        "expires_at": invite.expires_at,
    })
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def join_group_with_invite(request, token):
    invite = get_object_or_404(GroupInvite, token=token, is_active=True)

    if invite.is_expired():
        invite.is_active = False
        invite.save()
        return Response(
            {"detail": "Invite link expired"},
            status=status.HTTP_400_BAD_REQUEST
        )

    group = invite.group
    user = request.user

    # Already member
    if GroupMember.objects.filter(group=group, user=user).exists():
        return Response(
            {"detail": "Already a member of this group"},
            status=status.HTTP_200_OK
        )

    GroupMember.objects.create(group=group, user=user)

    return Response(
        {
            "message": "Joined group successfully",
            "group_id": group.id,
            "group_name": group.name,
        },
        status=status.HTTP_201_CREATED
    )
