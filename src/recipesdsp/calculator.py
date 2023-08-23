from itertools import chain

import pandas as pd

from .products import game_items
from .recipes import game_recipes


def format_in_out(list_elem):
    return {str(product): qte for product, qte in zip(list_elem[::2], list_elem[1::2])}

def get_game_recipes():
    return [
        {
            **r,
            "outputs": format_in_out(r["outputs"]),
            "inputs": format_in_out(r["inputs"]),
        }
        for r in game_recipes
    ]


def get_recipes(product, excluded_recipes):
    return [
        recipe
        for recipe in get_game_recipes()
        if (
            product in recipe["outputs"].keys() and recipe["id"] not in excluded_recipes
        )
    ]


def add_product_name(list_elem):
    return [
        {
            **elem,
            "product": game_items[elem["product"]]["name"]
            if "product" in elem
            else None,
        }
        for elem in list_elem
    ]


def get_product_name(product):
    return game_items[product]["name"]


def resume_recipe(recipe):
    recipe_id = recipe["id"]
    recipe_name = recipe["name"]
    recipe_type = recipe["type"]
    seconds = recipe["seconds"]
    inputs = " + ".join(
        [f"{v} {get_product_name(k)}" for k, v in recipe["inputs"].items()]
    )
    outputs = " + ".join(
        [f"{v} {get_product_name(k)}" for k, v in recipe["outputs"].items()]
    )
    return f"{recipe_type} - {recipe_name} (id:{recipe_id}) : {inputs} -> {outputs} (in {seconds}s)"


def iterate_product(product, qte_s, **kwargs):
    # print(f"Iterate {product} for {qte_s}/s")
    recipes = get_recipes(product, kwargs.get("excluded_recipes", []))

    if len(recipes) == 0 or (
        kwargs.get("stop_when_can_mining", True) and game_items[product].get("mining_from")
    ):
        return [{"type": "product", "product": product, "qte_s": qte_s}]
    # assert len(recipes) <= 1, "Too much recipes !"
    if len(recipes) > 1:
        print("---------------------------------------------------------")
        print(f"Too much recipes for {get_product_name(product)}")
        for recipe in recipes:
            print(resume_recipe(recipe))
        print("---------------------------------------------------------")

    recipe = recipes[0]
    output_qte_s = float(recipe["outputs"][product]) / float(recipe["seconds"])
    nb_machine = float(qte_s) / float(output_qte_s)
    # recipe_name = f"{recipe['type']} - {recipe['name']}"
    recipe_name = resume_recipe(recipe)
    additional_products = [
        {"type": "product", "product": key, "qte_s": -nb_machine * value / float(recipe["seconds"])}
        for key, value in recipe["outputs"].items()
        if key != product
    ]

    return list(
        chain(
            *[
                iterate_product(
                    input_product,
                    nb_machine * float(input_qte) / float(recipe["seconds"]),
                    **kwargs
                )
                for input_product, input_qte in recipe["inputs"].items()
            ]
        )
    ) + additional_products + [{"type": "recipe", "recipe": recipe_name, "nb_machine": nb_machine}]


def to_grouped_df(list_elem) -> (pd.DataFrame, pd.DataFrame):
    list_products = [e for e in list_elem if e["type"] == "product"]
    list_recipes = [e for e in list_elem if e["type"] == "recipe"]
    df_products = pd.DataFrame(list_products)
    df_recipes = pd.DataFrame(list_recipes)

    # print(df_products[df_products["qte_s"] < 0].groupby("product").qte_s.sum().reset_index())
    return (
        df_products.groupby("product").qte_s.sum().reset_index(),
        df_recipes.groupby("recipe").nb_machine.sum().reset_index(),
    )


def recipes_details_report(product, qte_s, excluded_recipes_ids):
    """
    A function to print the report to how produce the chosen product with the corresponding consumption.
    :param product: id of the product to produce (see id in products.py)
    :param qte_s: quantity per of product sec to produce
    :param excluded_recipes_ids: list of recipe id to exclude (see id in recipes.py)
    :return:
    """
    list_elem = add_product_name(
        iterate_product(product, qte_s, excluded_recipes=excluded_recipes_ids)
    )
    df_products, df_recipes = to_grouped_df(list_elem)
    print(" Products to use ".center(60, "#"))
    print(df_products)
    print(" Machines to use ".center(60, "#"))
    for index, elem in df_recipes.iterrows():
        print(f"{elem['nb_machine']} machines : {elem['recipe']}")
    print(" End ".center(60, "#"))
