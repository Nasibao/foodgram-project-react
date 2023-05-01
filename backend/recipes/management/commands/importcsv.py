import csv

from django.core.management.base import BaseCommand

from foodgram.settings import BASE_DIR
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        Ingredient.objects.all().delete()
        ingredient = f"{BASE_DIR}/data/ingredients.csv"
        with open(ingredient) as file:
            reader = csv.reader(file)
            counter = 0
            for row in reader:
                print(row[0])
                Ingredient.objects.create(name=row[0], measurement_unit=row[1])
                counter += 1

        print(f"в базу данных успешно добавлены ингредиенты - {counter} шт. ✅")
