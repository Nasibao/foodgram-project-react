from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import IngredientViewSet, RecipeViewSet, TagViewSet

app_name = "recipes"

router = SimpleRouter()
router.register("ingredients", IngredientViewSet)
router.register("tags", TagViewSet)
router.register("recipes", RecipeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
