import csv
import os


calories_path = os.path.join(os.path.dirname(__file__), "../../calories.csv")
with open(calories_path, "r") as f:
    reader = csv.DictReader(f)
    calories = {row["FoodItem"]: row["Cals_per100grams"] for row in reader}
