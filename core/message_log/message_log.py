import pygame

class MessageLog:
    """
    Class to manage and render a message log with a visual scrollbar.
    """

    def __init__(self, x, y, width, height, font, max_messages=100, visible_messages=10, bg_color=(50, 50, 50), default_text_color=(255, 255, 255)):
        """
        Initialize the message log.
        :param x: X-coordinate of the log UI.
        :param y: Y-coordinate of the log UI.
        :param width: Width of the log UI.
        :param height: Height of the log UI.
        :param font: Pygame font for rendering messages.
        :param max_messages: Maximum number of messages to retain in the log.
        :param visible_messages: Number of messages visible at one time.
        :param bg_color: Background color of the log.
        :param default_text_color: Default text color for messages.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.max_messages = max_messages
        self.visible_messages = visible_messages
        self.bg_color = bg_color
        self.default_text_color = default_text_color
        self.messages = []  # List of tuples: (message text, color)
        self.scroll_offset = 0  # Offset to determine which messages are visible
        self.active = True

        # Scrollbar dimensions
        self.scrollbar_width = 15
        self.scrollbar_x = self.x + self.width - self.scrollbar_width
        self.scrollbar_color = (100, 100, 100)
        self.scrollbar_thumb_color = (200, 200, 200)

    def toggle(self):
        self.active = not self.active

    def add_message(self, message, color=None):
        """
        Add a new message to the log, aggregating consecutive identical messages.

        Args:
            message (str): The message string to add.
            color (tuple, optional): The color of the message (default is the log's default text color).
        """
        if color is None:
            color = self.default_text_color

        # Check if the last message in the log is the same as the new message
        if self.messages and self.messages[0][0].startswith(message):
            # Increment the count in the last message
            count_start = self.messages[0][0].rfind("(")  # Find the count start, e.g., "(x3)"
            if count_start != -1 and self.messages[0][0].endswith(")"):
                # Update existing count
                count = int(self.messages[0][0][count_start + 2 : -1]) + 1
                self.messages[0] = (f"{message} (x{count})", color)
            else:
                # Add a new count
                self.messages[0] = (f"{message} (x2)", color)
        else:
            # Add the new message as usual
            self.messages.insert(0, (message, color))

        # Remove the oldest message if over the limit
        if len(self.messages) > self.max_messages:
            self.messages.pop()

        # Automatically scroll to the top when a new message is added
        self.scroll_offset = 0


    def scroll(self, direction):
        """
        Scroll through the log.
        :param direction: -1 to scroll up, 1 to scroll down.
        """
        max_offset = max(0, len(self.messages) - self.visible_messages)
        self.scroll_offset = max(0, min(self.scroll_offset + direction, max_offset))

    def render(self, screen):
        """
        Render the message log and its scrollbar on the screen.
        :param screen: The Pygame screen to render to.
        """
        if not self.active:
            return

        # Draw the background
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, self.height), 3)  # Border

        # Render the visible messages
        padding = 10
        line_height = self.font.get_height() + 8
        max_lines = (self.height - 2 * padding) // line_height

        start_index = self.scroll_offset
        end_index = min(start_index + max_lines, len(self.messages))

        for i, (message, color) in enumerate(self.messages[start_index:end_index]):
            text_surface = self.font.render(message, True, color)
            y_position = self.y + padding + i * line_height
            screen.blit(text_surface, (self.x + padding, y_position))

        # Draw the scrollbar
        self.render_scrollbar(screen, len(self.messages), max_lines)

    def wrap_text(self, text, max_width):
        """
        Wrap text into multiple lines if it exceeds the maximum width.
        :param text: The text to wrap.
        :param max_width: The maximum width for a line.
        :return: A list of strings, each fitting within the max_width.
        """
        words = text.split(' ')
        wrapped_lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                wrapped_lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            wrapped_lines.append(current_line.strip())

        return wrapped_lines

    def render_scrollbar(self, screen, total_lines, visible_lines):
        """
        Render the scrollbar to indicate scrolling position.
        :param screen: The Pygame screen to render to.
        :param total_lines: Total number of lines in the log.
        :param visible_lines: Number of visible lines at a time.
        """
        pygame.draw.rect(screen, self.scrollbar_color, (self.scrollbar_x, self.y, self.scrollbar_width, self.height))

        if total_lines > visible_lines:
            thumb_height = max(int(self.height * (visible_lines / total_lines)), 20)  # Minimum size
            thumb_y = self.y + int(self.scroll_offset * (self.height / total_lines))
            thumb_y = min(thumb_y, self.y + self.height - thumb_height)
            pygame.draw.rect(screen, self.scrollbar_thumb_color, (self.scrollbar_x, thumb_y, self.scrollbar_width, thumb_height))
