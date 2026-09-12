from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if not username or not password:
            return None

        try:
            user = UserModel._default_manager.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            user = (
                UserModel._default_manager
                .filter(Q(username__iexact=username) | Q(email__iexact=username))
                .order_by('id')
                .first()
            )

        if user and self.user_can_authenticate(user) and user.check_password(password):
            return user

        return None