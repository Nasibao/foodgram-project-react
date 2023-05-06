from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import SubscriptionsView, SubsribeView, UserViewSet

app_name = "users"

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "users/subscriptions/",
        SubscriptionsView.as_view(),
        name="subscriptions"
    ),
    path(
        "users/<int:pk>/subscribe/",
        SubsribeView.as_view(),
        name="subscribe"
    ),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]
