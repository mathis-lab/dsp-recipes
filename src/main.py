from recipesdsp.calculator import recipes_details_report

def main():
    product = "1501"  # Product id to produce
    qte_s = 60  # Quantity per s to produce
    excluded_recipes = [33, 31, 68, 28, 58]  # Recipes to not use
    recipes_details_report(product, qte_s, excluded_recipes)


if __name__ == "__main__":
    main()
