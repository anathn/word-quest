"""
Avatar Selector Component (STORY-003-02)

Dialog for selecting an avatar from predefined options.
"""

import pygame
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class AvatarOption:
    """Represents an avatar option with its display properties."""
    id: str
    label: str
    color: Tuple[int, int, int]  # Background color for the avatar placeholder


class AvatarSelector:
    """
    Renders an avatar selection dialog with a grid of avatar options.
    
    Displays a 4x2 grid of selectable circular avatar placeholders
    with friendly labels. Supports keyboard and mouse navigation.
    
    Attributes:
        avatar_options: List of available avatar options
        selected_avatar: Currently selected avatar ID (None if none selected)
    """
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    SELECTED_BORDER = (76, 175, 80)  # Green for selection
    HOVER_COLOR = (100, 100, 100)  # Grey for hover
    AVATAR_COLORS = [
        (100, 149, 237),  # Cornflower blue - astronaut
        (152, 255, 152),  # Light green - alien
        (255, 99, 71),    # Tomato - rocket
        (255, 165, 0),    # Orange - planet
        (255, 215, 0),    # Gold - star
        (169, 169, 169),  # Dark grey - moon
        (147, 112, 219),  # Purple - robot
        (255, 105, 180),  # Hot pink - cat
    ]
    BG_COLOR = (26, 26, 62)  # Deep space blue
    LABEL_COLOR = (255, 255, 255)
    
    # Layout
    GRID_COLS = 4
    GRID_ROWS = 2
    AVATAR_RADIUS = 40
    AVATAR_SPACING = 20
    PADDING = 20
    
    def __init__(
        self,
        avatar_ids: Optional[List[str]] = None,
        center_position: Optional[Tuple[int, int]] = None
    ):
        """
        Initialize the avatar selector.
        
        Args:
            avatar_ids: List of avatar IDs to display. Uses all if None.
            center_position: Center position for the dialog, (x, y)
        """
        # Initialize avatar options
        self.avatar_options = self._create_avatar_options(avatar_ids)
        self.selected_avatar: Optional[str] = None
        self.center_position = center_position or (400, 300)
        
        # Hover state
        self.hovered_avatar: Optional[str] = None
        
        # Font
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
        
        # Calculate dialog dimensions
        self._calculate_dimensions()
    
    def _create_avatar_options(self, avatar_ids: Optional[List[str]]) -> List[AvatarOption]:
        """Create avatar option objects."""
        # Map avatar IDs to their display properties
        avatar_info = {
            "astronaut": "Astronaut",
            "alien": "Alien",
            "rocket": "Rocket",
            "planet": "Planet",
            "star": "Star",
            "moon": "Moon",
            "robot": "Robot",
            "cat": "Cat"
        }
        
        # Use provided IDs or all options
        ids = avatar_ids or list(avatar_info.keys())
        
        options = []
        for i, avatar_id in enumerate(ids[:8]):  # Limit to 8
            color = self.AVATAR_COLORS[i % len(self.AVATAR_COLORS)]
            options.append(AvatarOption(
                id=avatar_id,
                label=avatar_info.get(avatar_id, avatar_id.title()),
                color=color
            ))
        
        return options
    
    def _calculate_dimensions(self):
        """Calculate dialog dimensions based on avatar count."""
        self.avatar_width = self.AVATAR_RADIUS * 2
        self.avatar_height = self.AVATAR_RADIUS * 2 + 30  # +30 for label
        
        grid_width = (
            self.GRID_COLS * (self.avatar_width + self.AVATAR_SPACING) -
            self.AVATAR_SPACING
        )
        grid_height = (
            self.GRID_ROWS * (self.avatar_height + self.AVATAR_SPACING) -
            self.AVATAR_SPACING
        )
        
        self.dialog_width = grid_width + 2 * self.PADDING
        self.dialog_height = grid_height + 2 * self.PADDING
        
        self.top_left = (
            self.center_position[0] - self.dialog_width // 2,
            self.center_position[1] - self.dialog_height // 2
        )
    
    def get_avatar_bounds(self, avatar_id: str) -> pygame.Rect:
        """
        Get the bounding rectangle for an avatar.
        
        Args:
            avatar_id: The avatar ID to get bounds for
            
        Returns:
            pygame.Rect for the avatar area
        """
        # Find the avatar's position in the grid
        for i, option in enumerate(self.avatar_options):
            if option.id == avatar_id:
                row = i // self.GRID_COLS
                col = i % self.GRID_COLS
                
                x = self.top_left[0] + self.PADDING + col * (self.avatar_width + self.AVATAR_SPACING)
                y = self.top_left[1] + self.PADDING + row * (self.avatar_height + self.AVATAR_SPACING)
                
                return pygame.Rect(x, y, self.avatar_width, self.avatar_height)
        
        return pygame.Rect(0, 0, 0, 0)
    
    def handle_event(self, event: pygame.Event) -> Optional[str]:
        """
        Handle mouse events for avatar selection.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            Selected avatar ID if clicked, None otherwise
        """
        selected = None
        
        if event.type == pygame.MOUSEMOTION:
            # Check for hover
            self.hovered_avatar = None
            mouse_pos = event.pos
            for option in self.avatar_options:
                bounds = self.get_avatar_bounds(option.id)
                if bounds.collidepoint(mouse_pos):
                    self.hovered_avatar = option.id
                    break
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for option in self.avatar_options:
                    bounds = self.get_avatar_bounds(option.id)
                    if bounds.collidepoint(mouse_pos):
                        self.selected_avatar = option.id
                        selected = option.id
                        break
        
        return selected
    
    def handle_key_event(self, event: pygame.Event) -> Optional[str]:
        """
        Handle keyboard events for avatar selection.
        
        Args:
            event: Pygame key event
            
        Returns:
            Selected avatar ID if Enter pressed and one selected, None otherwise
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                if self.selected_avatar:
                    return self.selected_avatar
        return None
    
    def render(self, screen: pygame.Surface, title: str = "Choose an Avatar"):
        """
        Render the avatar selector dialog.
        
        Args:
            screen: Pygame surface to render on
            title: Dialog title text
        """
        # Draw background
        bg_rect = pygame.Rect(
            self.top_left[0] - 10,
            self.top_left[1] - 10,
            self.dialog_width + 20,
            self.dialog_height + 20
        )
        pygame.draw.rect(screen, (40, 40, 60), bg_rect, border_radius=10)
        pygame.draw.rect(screen, self.WHITE, bg_rect, 2, border_radius=10)
        
        # Draw title
        title_surface = self.font.render(title, True, self.WHITE)
        title_rect = title_surface.get_rect(
            center=(self.center_position[0], self.top_left[1] + 15)
        )
        screen.blit(title_surface, title_rect)
        
        # Draw avatars
        for option in self.avatar_options:
            self._render_avatar(screen, option)
    
    def _render_avatar(self, screen: pygame.Surface, option: AvatarOption):
        """
        Render a single avatar option.
        
        Args:
            screen: Pygame surface to render on
            option: AvatarOption to render
        """
        bounds = self.get_avatar_bounds(option.id)
        center = (bounds.centerx, bounds.centery)
        
        # Determine color state
        is_selected = option.id == self.selected_avatar
        is_hovered = option.id == self.hovered_avatar
        
        # Draw avatar circle
        if is_selected:
            # Draw selected border
            pygame.draw.circle(screen, self.SELECTED_BORDER, center, self.AVATAR_RADIUS + 4)
        
        if is_hovered and not is_selected:
            # Draw hover effect
            pygame.draw.circle(screen, self.HOVER_COLOR, center, self.AVATAR_RADIUS + 2)
        
        # Draw avatar background
        pygame.draw.circle(screen, option.color, center, self.AVATAR_RADIUS)
        
        # Draw avatar border
        border_color = self.WHITE if not is_hovered else self.HOVER_COLOR
        pygame.draw.circle(screen, border_color, center, self.AVATAR_RADIUS, 2)
        
        # Render avatar icon placeholder (simple letter/emoji representation)
        label = option.label[0].upper()  # First letter as placeholder
        icon_surface = self.small_font.render(label, True, self.BLACK)
        icon_rect = icon_surface.get_rect(center=center)
        screen.blit(icon_surface, icon_rect)
        
        # Draw label below avatar
        label_surface = self.small_font.render(option.label, True, self.LABEL_COLOR)
        label_rect = label_surface.get_rect(
            centerx=center[0],
            top=bounds.bottom + 5
        )
        screen.blit(label_surface, label_rect)


def create_avatar_selector(
    avatar_ids: Optional[List[str]] = None,
    center_position: Optional[Tuple[int, int]] = None
) -> AvatarSelector:
    """
    Factory function to create an AvatarSelector.
    
    Args:
        avatar_ids: List of avatar IDs to display
        center_position: Center position for the dialog
        
    Returns:
        Configured AvatarSelector instance
    """
    return AvatarSelector(avatar_ids=avatar_ids, center_position=center_position)