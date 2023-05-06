from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.validators import ValidationError
from rest_framework import serializers, status

from recipes.serializers import FollowRecipeSerializer

from .models import Follow

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return obj.id in self.context["follows"]

    class Meta:
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "password",
            "is_subscribed",
        )
        extra_kwargs = {
            "password": {
                "write_only": True,
            },
        }
        model = User

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class FollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="recipes.count", read_only=True
    )

    def validate(self, data):
        author = self.instance
        user = self.context.get("request").user
        if author == user:
            raise ValidationError(
                {
                    "errors": "Вы не можете подписываться/отписывать на/от самого себя"
                }
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                {"errors": "Вы уже подписаны на данного пользователя"}
            )
        return data

    def get_recipes(self, obj):
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        author = get_object_or_404(User, id=obj.pk)
        recipes = author.recipes.all()
        if limit:
            recipes = recipes[: int(limit)]
        serializer = FollowRecipeSerializer(
            recipes,
            many=True,
            context={
                "request": request,
            },
        )
        return serializer.data

    def get_is_subscribed(self, obj):
        return obj.id in self.context["follows"]

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("email", "username", "first_name", "last_name")
