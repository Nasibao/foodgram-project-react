from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet as DjoserUserViewSet

from .models import Follow, User
from .serializers import FollowSerializer


class SubscriptionsView(generics.ListAPIView):
    queryset = User.objects.all()
    permission_classes = [
        permissions.IsAuthenticated,
    ]
    serializer_class = FollowSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(following__user=user)


class UserViewSet(DjoserUserViewSet):
    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
            "follows": set(
                Follow.objects.filter(user_id=self.request.user).values_list(
                    "author_id", flat=True
                ) if self.request.user.is_authenticated else set()
            ),
        }


class SubsribeView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = FollowSerializer

    def get_serializer_context(self):
        return {
            "request": self.request,
            "format": self.format_kwarg,
            "view": self,
            "follows": set(
                Follow.objects.filter(user_id=self.request.user).values_list(
                    "author_id", flat=True
                )
            ),
        }

    def post(self, request, pk):
        user = request.user
        author = get_object_or_404(User, id=pk)
        serializer = FollowSerializer(
            author, data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        Follow.objects.get_or_create(user=user, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        user = request.user
        author = get_object_or_404(User, id=pk)
        get_object_or_404(Follow, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
