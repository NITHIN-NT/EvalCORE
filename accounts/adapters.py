from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from accounts.models import CustomUser

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Already logged in? Link it. (Standard behavior)
        if sociallogin.is_existing:
            return

        # Check if we have an existing user with this email
        email = sociallogin.user.email
        if email:
            try:
                user = CustomUser.objects.get(email=email)
                # Link the social account to the existing user
                sociallogin.connect(request, user)
            except CustomUser.DoesNotExist:
                pass
