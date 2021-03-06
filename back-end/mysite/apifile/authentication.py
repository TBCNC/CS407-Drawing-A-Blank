from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _
import datetime
import pytz


# extend the token authentication to add a timeout to the token
class ExpTokenAuthentication(TokenAuthentication):

    def authenticate_credentials(self, key):
        model = self.get_model()

        # see if the user has a token
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        # check token in active
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        # localize datetime objects as cannot compare naive and aware
        # aka set to same timezone regardless of os clock
        utc = pytz.UTC
        time_now = utc.localize(datetime.datetime.utcnow())

        # if token expired, raise error
        # currently set to 1 day usage
        if token.created < time_now - datetime.timedelta(days=1):
            raise exceptions.AuthenticationFailed(_('Token expired'))

        return token.user, token
