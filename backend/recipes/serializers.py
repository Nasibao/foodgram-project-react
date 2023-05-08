from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from users.models import Follow
from .models import (
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Tag,
    Favorite,
)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "color", "slug")
        model = Tag
        read_only_fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "measurement_unit")
        model = Ingredient
        read_only_fields = ("id", "name", "measurement_unit")


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        return obj.id in self.context["follows"]

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
        )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")
        validators = [
            UniqueTogetherValidator(
                queryset=IngredientRecipe.objects.all(),
                fields=("ingredient", "recipe"),
            )
        ]


class IngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = IngredientRecipe
        fields = ("id", "amount")


class RecipeListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(source="ingredient_to_recipe", many=True)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_is_favorited(self, obj):
        return obj.id in self.context["favorites"]

    def get_is_in_shopping_cart(self, obj):
        return obj.id in self.context['carts']

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    ingredients = IngredientCreateSerializer(many=True)

    def to_representation(self, instance):
        serializer = RecipeListSerializer(
            instance, context=self.context
        )
        return serializer.data

    @transaction.atomic
    def create(self, validated_data):
        ingredients = (
            validated_data.pop("ingredients")
            if "ingredients" in validated_data
            else {}
        )
        tags = validated_data.pop("tags") if "tags" in validated_data else {}
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            IngredientRecipe.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = (
            validated_data.pop("ingredients")
            if "ingredients" in validated_data
            else {}
        )
        tags = validated_data.pop("tags") if "tags" in validated_data else {}
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.tags.set(tags)
        instance.image = validated_data.get("image", instance.image)
        instance.ingredients.clear()
        for ingredient in ingredients:
            IngredientRecipe.objects.get_or_create(
                recipe=instance,
                ingredient=ingredient["ingredient"],
                amount=ingredient["amount"],
            )
        return super().update(instance, validated_data)

    def validate(self, data):
        ingredient_data = self.initial_data.get("ingridients")
        ingredient_in_recipe = set()
        for ingredient in ingredient_data:
            ingredient_obj = get_object_or_404(Ingredient, id=ingredient["id"])
            if ingredient_obj in ingredient_in_recipe:
                raise serializers.ValidationError("Дубликат ингредиента")
            ingredient_in_recipe.add(ingredient_obj)
        return data

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )


class FollowRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "cooking_time",
        )


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = (
            "user",
            "recipe",
        )

    def validate(self, data):
        user = data["user"]
        if user.favorites_user.filter(recipe=data["recipe"]).exists():
            raise serializers.ValidationError(
                "Рецепт уже добавлен в избранное."
            )
        return data

    def to_representation(self, instance):
        return FollowRecipeSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = (
            "user",
            "recipe",
        )

    def validate(self, data):
        user = data["user"]
        if user.carts.filter(recipe=data["recipe"]).exists():
            raise serializers.ValidationError("Рецепт уже добавлен в корзину")
        return data

    def to_representation(self, instance):
        return FollowRecipeSerializer(
            instance.recipe, context={"request": self.context.get("request")}
        ).data
