import yaml
from core.items.item import Item
from core.items.item_list import ItemList  # Enum for item names

class ItemFactory:
    ITEM_DATA = {}

    @staticmethod
    def load_items_from_yaml(file_path: str):
        """
        Load item definitions from a YAML file.

        Args:
            file_path (str): Path to the YAML file containing item definitions.
        """
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        ItemFactory.ITEM_DATA = data.get("items", {})

    @staticmethod
    def create_item_instance(item_enum: ItemList) -> Item:
        """
        Create a new item instance from the loaded YAML data.

        Args:
            item_enum (ItemList): The item to create (based on its enum).

        Returns:
            Item: A new item instance.
        """
        item_data = ItemFactory.ITEM_DATA.get(item_enum.name)
        if not item_data:
            raise ValueError(f"Item '{item_enum.name}' is not defined in the item data.")

        return Item(
            name=item_data["name"],
            icon_path=item_data["icon_path"],
            description=item_data["description"],
            stackable=item_data["stackable"],
            max_stack=item_data["max_stack"],
            effects=item_data.get("effects", {}),
            rarity=item_data.get("rarity", "common")
        )
