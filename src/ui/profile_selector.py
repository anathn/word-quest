"""
Profile Selector Component (STORY-003-02)

List view for displaying and selecting student profiles.
"""

import pygame
from typing import Tuple, Optional, List, Callable
from datetime import datetime
from src.profiles.profile_manager import ProfileManager
from src.models.student_profile import StudentProfile


class ProfileSelector:
    """
    UI component for displaying and selecting student profiles.
    
    Shows a list of all student profiles with avatars, names,
    and last played dates. Supports navigation and selection.
    
    Attributes:
        profile_manager: ProfileManager instance for accessing profiles
    """
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BG_COLOR = (26, 26, 62)  # Deep space blue
    PROFILE_BG = (40, 40, 60)
    PROFILE_HOVER = (60, 60, 90)
    PROFILE_SELECTED = (76, 175, 80, 50)  # Semi-transparent green
    TEXT_COLOR = (220, 220, 220)
    MUTE_COLOR = (150, 150, 150)
    AVATAR_COLOR = (100, 149, 237)
    EDITS_COLOR = (220, 220, 50)
    DELETE_COLOR = (244, 67, 54)
    
    # Avatar colors (matching ProfileManager)
    AVATAR_PALETTE = {
        "astronaut": (100, 149, 237),
        "alien": (152, 255, 152),
        "rocket": (255, 99, 71),
        "planet": (255, 165, 0),
        "star": (255, 215, 0),
        "moon": (169, 169, 169),
        "robot": (147, 112, 219),
        "cat": (255, 105, 180),
    }
    
    # Layout
    PROFILE_HEIGHT = 80
    PROFILE_SPACING = 15
    PADDING = 20
    AVATAR_SIZE = 50
    BUTTON_SIZE = 36
    
    def __init__(
        self,
        profile_manager: ProfileManager,
        screen_width: int = 800,
        screen_height: int = 600,
        position: Tuple[int, int] = (0, 0),
        size: Tuple[int, int] = (600, 400)
    ):
        """
        Initialize the profile selector.
        
        Args:
            profile_manager: ProfileManager instance
            screen_width: Parent screen width
            screen_height: Parent screen height
            position: Top-left position of the selector
            size: Width and height of the selector
        """
        self.profile_manager = profile_manager
        self.position = position
        self.size = size
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # State
        self.profiles: List[StudentProfile] = []
        self.hovered_index: Optional[int] = None
        self.selected_index: Optional[int] = None
        self.selected_profile: Optional[StudentProfile] = None
        
        # Scroll state
        self.scroll_y = 0
        self.scroll_speed = 10
        self.max_scroll = 0
        
        # Callbacks
        self.on_select: Optional[Callable[[StudentProfile], None]] = None
        self.on_edit: Optional[Callable[[str], None]] = None
        self.on_delete: Optional[Callable[[str], None]] = None
        self.on_close: Optional[Callable[[], None]] = None
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.name_font = pygame.font.Font(None, 28)
        self.detail_font = pygame.font.Font(None, 22)
        
        # Calculate dimensions
        self._calculate_layout()
        
        # Load profiles
        self.refresh_profiles()
    
    def _calculate_layout(self):
        """Calculate layout dimensions and button positions."""
        self.rect = pygame.Rect(self.position, self.size)
        
        # Header area
        self.header_height = 60
        
        # Content area (for profiles list)
        self.content_rect = pygame.Rect(
            self.position[0] + self.PADDING,
            self.position[1] + self.header_height + self.PADDING,
            self.size[0] - 2 * self.PADDING,
            self.size[1] - self.header_height - 2 * self.PADDING - self.BUTTON_SIZE - self.PADDING
        )
        
        # Calculate max scroll
        total_profile_height = len(self.profiles) * (self.PROFILE_HEIGHT + self.PROFILE_SPACING)
        visible_height = self.content_rect.height
        self.max_scroll = max(0, total_profile_height - visible_height)
        
        # Close button
        self.close_button_rect = pygame.Rect(
            self.position[0] + self.size[0] - self.BUTTON_SIZE - 10,
            self.position[1] + 10,
            self.BUTTON_SIZE,
            self.BUTTON_SIZE
        )
        
        # Add button
        self.add_button_rect = pygame.Rect(
            self.position[0] + self.PADDING,
            self.position[1] + self.size[1] - self.BUTTON_SIZE - self.PADDING,
            self.BUTTON_SIZE,
            self.BUTTON_SIZE
        )
    
    def refresh_profiles(self):
        """Refresh the list of profiles from the manager."""
        self.profiles = self.profile_manager.get_all_profiles()
        # Recalculate max scroll
        total_profile_height = len(self.profiles) * (self.PROFILE_HEIGHT + self.PROFILE_SPACING)
        visible_height = self.content_rect.height
        self.max_scroll = max(0, total_profile_height - visible_height)
    
    def _get_profile_rect(self, index: int, scroll_y: int) -> Optional[pygame.Rect]:
        """
        Get the rectangle for a profile at the given index.
        
        Args:
            index: Profile index
            scroll_y: Current scroll offset
            
        Returns:
            Rectangle for the profile, or None if not visible
        """
        if index < 0 or index >= len(self.profiles):
            return None
        
        y = self.content_rect.top + index * (self.PROFILE_HEIGHT + self.PROFILE_SPACING) - scroll_y
        
        # Check if visible
        if y + self.PROFILE_HEIGHT < self.content_rect.top:
            return None
        if y > self.content_rect.bottom:
            return None
        
        return pygame.Rect(
            self.content_rect.x,
            y,
            self.content_rect.width,
            self.PROFILE_HEIGHT
        )
    
    def _get_profile_index_at(self, pos: Tuple[int, int]) -> Optional[int]:
        """
        Get the profile index at the given position.
        
        Args:
            pos: Mouse position
            
        Returns:
            Profile index or None
        """
        for i in range(len(self.profiles)):
            rect = self._get_profile_rect(i, self.scroll_y)
            if rect and rect.collidepoint(pos):
                return i
        return None
    
    def handle_event(self, event: pygame.event.EventType) -> Optional[str]:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            
        Returns:
            "select" if profile selected, "edit" if edit requested,
            "delete" if delete requested, "add" if add requested, "close" if closed
        """
        result = None
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check close button
                if self.close_button_rect.collidepoint(mouse_pos):
                    result = "close"
                    if self.on_close:
                        self.on_close()
                    return result
                
                # Check add button
                elif self.add_button_rect.collidepoint(mouse_pos):
                    result = "add"
                    return result
                
                # Check profiles
                else:
                    profile_index = self._get_profile_index_at(mouse_pos)
                    if profile_index is not None:
                        self.selected_index = profile_index
                        self.selected_profile = self.profiles[profile_index]
                        
                        # Determine if clicking on a button
                        rect = self._get_profile_rect(profile_index, self.scroll_y)
                        if rect:
                            # Edit button (pencil)
                            edit_button_rect = pygame.Rect(
                                rect.right - self.BUTTON_SIZE * 2 - 10,
                                rect.centery - self.BUTTON_SIZE // 2,
                                self.BUTTON_SIZE,
                                self.BUTTON_SIZE
                            )
                            
                            # Delete button (trash)
                            delete_button_rect = pygame.Rect(
                                rect.right - self.BUTTON_SIZE - 5,
                                rect.centery - self.BUTTON_SIZE // 2,
                                self.BUTTON_SIZE,
                                self.BUTTON_SIZE
                            )
                            
                            if edit_button_rect.collidepoint(mouse_pos):
                                result = "edit"
                                if self.on_edit and self.selected_profile:
                                    self.on_edit(self.selected_profile.id)
                            elif delete_button_rect.collidepoint(mouse_pos):
                                result = "delete"
                                if self.on_delete and self.selected_profile:
                                    self.on_delete(self.selected_profile.id)
                            elif self.on_select and self.selected_profile:
                                self.on_select(self.selected_profile)
                                result = "select"
            
            elif event.button == 4:  # Scroll up
                self.scroll_y = max(0, self.scroll_y - self.scroll_speed)
            elif event.button == 5:  # Scroll down
                self.scroll_y = min(self.max_scroll, self.scroll_y + self.scroll_speed)
        
        elif event.type == pygame.MOUSEMOTION:
            # Update hover state
            profile_index = self._get_profile_index_at(mouse_pos)
            self.hovered_index = profile_index
        
        return result
    
    def render(self, screen: pygame.Surface):
        """
        Render the profile selector.
        
        Args:
            screen: Pygame surface to render on
        """
        # Draw background
        pygame.draw.rect(screen, self.BG_COLOR, self.rect, border_radius=10)
        pygame.draw.rect(screen, self.WHITE, self.rect, 2, border_radius=10)
        
        # Draw title
        title = "Student Profiles"
        title_surface = self.title_font.render(title, True, self.WHITE)
        title_rect = title_surface.get_rect(
            left=self.position[0] + self.PADDING + self.BUTTON_SIZE + 10,
            centery=self.position[1] + 30
        )
        screen.blit(title_surface, title_rect)
        
        # Draw close button
        self._draw_close_button(screen)
        
        # Draw profile count
        count_text = f"{len(self.profiles)} profile(s)"
        count_surface = self.detail_font.render(count_text, True, self.MUTE_COLOR)
        count_rect = count_surface.get_rect(
            right=self.position[0] + self.size[0] - self.PADDING,
            centery=self.position[1] + 30
        )
        screen.blit(count_surface, count_rect)
        
        # Draw profiles
        self._render_profiles(screen)
        
        # Draw add button
        self._draw_add_button(screen)
    
    def _render_profiles(self, screen: pygame.Surface):
        """Render the list of profiles."""
        # Draw content area clip
        clipped_rect = self.content_rect.copy()
        screen.set_clip(clipped_rect)
        
        for i, profile in enumerate(self.profiles):
            rect = self._get_profile_rect(i, self.scroll_y)
            if rect is None:
                continue
            
            # Background
            is_hovered = i == self.hovered_index
            is_selected = i == self.selected_index
            
            if is_selected:
                # Semi-transparent green overlay
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((*self.PROFILE_SELECTED[:3], 100))
                screen.blit(overlay, rect)
            
            bg_color = self.PROFILE_HOVER if is_hovered else self.PROFILE_BG
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)
            
            # Avatar
            avatar_color = self.AVATAR_PALETTE.get(profile.avatar_id, self.AVATAR_COLOR)
            avatar_center = (rect.left + 30, rect.centery)
            pygame.draw.circle(screen, avatar_color, (int(avatar_center[0]), int(avatar_center[1])), 25)
            pygame.draw.circle(screen, self.WHITE, (int(avatar_center[0]), int(avatar_center[1])), 25, 2)
            
            # Initial
            initial_font = pygame.font.Font(None, 32)
            initial = profile.sanitized_name[0].upper() if profile.sanitized_name else "?"
            initial_surface = initial_font.render(initial, True, self.BLACK)
            initial_rect = initial_surface.get_rect(center=avatar_center)
            screen.blit(initial_surface, initial_rect)
            
            # Name
            name_surface = self.name_font.render(profile.sanitized_name, True, self.WHITE)
            name_rect = name_surface.get_rect(
                left=rect.left + 70,
                top=rect.top + 15
            )
            screen.blit(name_surface, name_rect)
            
            # Last played
            last_played_text = self._get_last_played_text(profile)
            last_played_surface = self.detail_font.render(last_played_text, True, self.MUTE_COLOR)
            last_played_rect = last_played_surface.get_rect(
                left=rect.left + 70,
                top=rect.top + 45
            )
            screen.blit(last_played_surface, last_played_rect)
            
            # Buttons
            button_y = rect.centery - self.BUTTON_SIZE // 2
            
            # Edit button (pencil icon - simplified as "E")
            edit_button_rect = pygame.Rect(
                rect.right - self.BUTTON_SIZE * 2 - 10,
                button_y,
                self.BUTTON_SIZE,
                self.BUTTON_SIZE
            )
            self._draw_button(screen, edit_button_rect, "E", self.EDITS_COLOR)
            
            # Delete button (trash icon - simplified as "X")
            delete_button_rect = pygame.Rect(
                rect.right - self.BUTTON_SIZE - 5,
                button_y,
                self.BUTTON_SIZE,
                self.BUTTON_SIZE
            )
            self._draw_button(screen, delete_button_rect, "X", self.DELETE_COLOR)
        
        screen.set_clip(None)
    
    def _get_last_played_text(self, profile: StudentProfile) -> str:
        """Get formatted last played text for a profile."""
        if not profile.last_played:
            return "Never played"
        
        now = datetime.now()
        delta = now - profile.last_played
        
        days = delta.days
        if days == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                minutes = delta.seconds // 60
                return f"Last played: {minutes}m ago"
            return f"Last played: {hours}h ago"
        elif days == 1:
            return "Last played: yesterday"
        elif days < 7:
            return f"Last played: {days} days ago"
        else:
            return f"Last played: {profile.last_played.strftime('%b %d')}"
    
    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str, color: Tuple[int, int, int]):
        """Draw a button with the given color."""
        pygame.draw.rect(screen, color, rect, border_radius=5)
        font = pygame.font.Font(None, 20)
        text_surface = font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
    
    def _draw_close_button(self, screen: pygame.Surface):
        """Draw the close button."""
        pygame.draw.rect(screen, self.DELETE_COLOR, self.close_button_rect, border_radius=5)
        font = pygame.font.Font(None, 24)
        text_surface = font.render("×", True, self.WHITE)
        text_rect = text_surface.get_rect(center=self.close_button_rect.center)
        screen.blit(text_surface, text_rect)
    
    def _draw_add_button(self, screen: pygame.Surface):
        """Draw the add student button."""
        pygame.draw.rect(screen, self.BUTTON_COLOR, self.add_button_rect, border_radius=5)
        font = pygame.font.Font(None, 28)
        text_surface = font.render("+", True, self.WHITE)
        text_rect = text_surface.get_rect(center=self.add_button_rect.center)
        screen.blit(text_surface, text_rect)
        
        # Label
        label = "Add Student"
        label_font = pygame.font.Font(None, 22)
        label_surface = label_font.render(label, True, self.BUTTON_COLOR)
        label_rect = label_surface.get_rect(
            left=self.add_button_rect.right + 10,
            centery=self.add_button_rect.centery
        )
        screen.blit(label_surface, label_rect)


def create_profile_selector(
    profile_manager: ProfileManager,
    position: Tuple[int, int] = (0, 0),
    size: Tuple[int, int] = (600, 400)
) -> ProfileSelector:
    """
    Factory function to create a ProfileSelector.
    
    Args:
        profile_manager: ProfileManager instance
        position: Top-left position
        size: Width and height
        
    Returns:
        Configured ProfileSelector instance
    """
    selector = ProfileSelector(
        profile_manager=profile_manager,
        position=position,
        size=size
    )
    return selector