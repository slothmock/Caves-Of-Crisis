from core import logging


class Inventory:
    def __init__(self, max_weight=20):
        """
        Initialize the inventory with a max size and an empty dictionary of items.
        """
        self.max_weight = max_weight
        self.items = {}  # Dictionary with item names as keys and a list of (Item, quantity) tuples as values

    def add_item(self, item, quantity=1):
        """
        Add an item to the inventory. Stack items if possible, or create a new stack if the current stack is full.

        Args:
            item (Item): The item to add.
            quantity (int): The quantity to add.

        Returns:
            int: The quantity of items that could not be added (0 if all items were added).
        """
        def available_capacity():
            """Calculate the remaining space in the inventory."""
            current_count = sum(quantity for stacks in self.items.values() for _, quantity in stacks)
            return self.max_weight - current_count

        remaining_capacity = available_capacity()
        if remaining_capacity <= 0:
            return quantity  # Inventory is full, none can be added

        # Adjust quantity to fit within available capacity
        quantity = min(quantity, remaining_capacity)

        # Check if the item exists in inventory
        if item.name in self.items:
            stacks = self.items[item.name]

            # Try to stack onto an existing stack
            for i, (existing_item, current_quantity) in enumerate(stacks):
                if existing_item.stackable and current_quantity < existing_item.max_stack:
                    available_space = existing_item.max_stack - current_quantity
                    amount_to_add = min(quantity, available_space)
                    stacks[i] = (existing_item, current_quantity + amount_to_add)
                    quantity -= amount_to_add

                    # If all items were added, return 0
                    if quantity == 0:
                        return 0

            # If there is remaining quantity, create a new stack
            stacks.append((item, quantity))
            return 0

        else:
            # Add as a new item entry
            self.items[item.name] = [(item, quantity)]
            return 0

    def remove_item(self, item_name, quantity=1):
        """
        Remove a specific quantity of an item. Remove stacks if quantity reaches 0.

        Args:
            item_name (str): The name of the item to remove.
            quantity (int): The quantity to remove.

        Returns:
            bool: True if the item was successfully removed, False if not enough quantity or item not found.
        """
        if item_name in self.items:
            stacks = self.items[item_name]

            for i, (item, current_quantity) in enumerate(stacks):
                if current_quantity > quantity:
                    stacks[i] = (item, current_quantity - quantity)
                    return True
                elif current_quantity == quantity:
                    stacks.pop(i)
                    if not stacks:
                        del self.items[item_name]  # Remove the entry if no stacks remain
                    return True
                else:
                    quantity -= current_quantity
                    stacks.pop(i)

            # If we reach here, there wasn't enough quantity to remove
            if not self.items[item_name]:
                del self.items[item_name]  # Clean up empty entries
            return quantity == 0  # False if there's still quantity to remove

        return False  # Item not found

    def find_item(self, item_name):
        """
        Find an item in the inventory by name.

        Args:
            item_name (str): The name of the item to find.

        Returns:
            list[tuple]: A list of (Item, quantity) stacks for the item, or None if not found.
        """
        return self.items.get(item_name)

    def list_items(self):
        """
        List all items in the inventory.

        Returns:
            list[str]: A list of strings describing each item and its stacks.
        """
        return [
            f"{item.name} x{quantity}" for stacks in self.items.values() for item, quantity in stacks
        ]

    def is_full(self):
        """
        Check if the inventory is full.

        Returns:
            bool: True if the inventory is full, False otherwise.
        """
        total_items = sum(quantity for stacks in self.items.values() for _, quantity in stacks)
        logging.logger.debug(f"Total items: {total_items}, Max size: {self.max_weight}")
        return total_items >= self.max_weight

