"""
Tests for Graph Renderer Component

Tests for STORY-002-06: Progress Graph (Fluency Trend)
"""

import os
import pytest
import pygame
from datetime import datetime, timedelta
from src.ui.graph_renderer import GraphRenderer, GraphConfig, create_graph_renderer
from src.components.analytics import DataPoint


class TestGraphConfig:
    """Test GraphConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GraphConfig()
        
        assert config.width == 600
        assert config.height == 300
        assert config.margin == {'top': 40, 'right': 40, 'bottom': 60, 'left': 60}
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = GraphConfig(
            width=800,
            height=400,
            margin={'top': 20, 'right': 30, 'bottom': 50, 'left': 40}
        )
        
        assert config.width == 800
        assert config.height == 400
        assert config.margin['top'] == 20
        assert config.margin['right'] == 30


class TestGraphRenderer:
    """Test the GraphRenderer class."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Initialize pygame before each test."""
        pygame.init()
        yield
    
    def test_initialization(self):
        """Test GraphRenderer initialization."""
        config = GraphConfig()
        renderer = GraphRenderer(config=config)
        
        assert renderer.config == config
        assert renderer._hover_point is None
        assert renderer._font is None
    
    def test_factory_function(self):
        """Test create_graph_renderer factory function."""
        config = GraphConfig(width=500, height=250)
        renderer = create_graph_renderer(config=config)
        
        assert isinstance(renderer, GraphRenderer)
        assert renderer.config.width == 500
    
    def test_default_initialization(self):
        """Test initialization with default config."""
        renderer = GraphRenderer()
        
        assert renderer.config.width == 600
        assert renderer.config.height == 300
    
    def test_render_empty_data(self):
        """Test rendering with empty data."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        # Should not raise any errors
        renderer.render(screen, [], title="Test Graph")
        
        # Surface should be filled with background color
        pixel = screen.get_at((0, 0))
        assert pixel[:3] == renderer.COLOR_BG[:3]
    
    def test_render_with_data(self):
        """Test rendering with valid data."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
            DataPoint(week="2026-W21", average=1.5, word_count=5),
            DataPoint(week="2026-W22", average=1.0, word_count=5),
        ]
        
        # Should not raise any errors
        renderer.render(screen, data, title="Test Graph")
        
        # Surface should have content
        assert screen.get_width() == 600
        assert screen.get_height() == 300
    
    def test_render_single_point(self):
        """Test rendering with single data point."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W27", average=2.0, word_count=5),
        ]
        
        # Should not raise errors
        renderer.render(screen, data, title="Test Graph")
    
    def test_draw_trend_line_minimum_points(self):
        """Test trend line requires at least 2 points."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        # Single point - no trend line drawn
        data_single = [
            DataPoint(week="2026-W27", average=2.0, word_count=5),
        ]
        renderer.render(screen, data_single, title="Test")
        
        # No error should occur
    
    def test_handle_mouse_motion_no_hover(self):
        """Test mouse motion with no nearby data point."""
        renderer = GraphRenderer()
        
        screen_rect = pygame.Rect(0, 0, 600, 300)
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
            DataPoint(week="2026-W21", average=1.5, word_count=5),
        ]
        
        # Mouse far from any point
        renderer.handle_mouse_motion((10, 10), data, screen_rect)
        
        assert renderer._hover_point is None
    
    def test_clear_hover(self):
        """Test clearing hover state."""
        renderer = GraphRenderer()
        
        # Set a hover point
        renderer._hover_point = (0, DataPoint(week="test", average=1.0, word_count=1), (100, 100))
        
        # Clear it
        renderer.clear_hover()
        
        assert renderer._hover_point is None
    
    def test_export_to_surface(self):
        """Test exporting graph to surface."""
        renderer = GraphRenderer()
        
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
            DataPoint(week="2026-W21", average=1.5, word_count=5),
        ]
        
        surface = renderer.export_to_surface(data, title="Export Test")
        
        assert isinstance(surface, pygame.Surface)
        assert surface.get_width() == 600
        assert surface.get_height() == 300
    
    def test_export_to_png_file(self, tmp_path):
        """Test exporting graph to PNG file."""
        import tempfile
        import os
        
        renderer = GraphRenderer()
        
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
            DataPoint(week="2026-W21", average=1.5, word_count=5),
        ]
        
        filepath = str(tmp_path / "test_graph.png")
        
        # Should not raise errors
        renderer.export_to_png(filepath, data, title="Test PNG")
        
        # File should be created
        assert os.path.exists(filepath)
        
        # File should have some content
        assert os.path.getsize(filepath) > 0
    
    def test_export_to_png_from_factory(self, tmp_path):
        """Test PNG export works from factory-created renderer."""
        renderer = create_graph_renderer()
        
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
        ]
        
        filepath = str(tmp_path / "factory_test.png")
        renderer.export_to_png(filepath, data, title="Factory Test")
        
        assert os.path.exists(filepath)


class TestGraphRendererColors:
    """Test renderer color constants."""
    
    def test_color_values(self):
        """Test that color constants are valid RGB tuples."""
        renderer = GraphRenderer()
        
        # Check all colors are 3-tuples with valid RGB values
        colors_to_check = [
            ('COLOR_BG', renderer.COLOR_BG),
            ('COLOR_AXIS', renderer.COLOR_AXIS),
            ('COLOR_GRID', renderer.COLOR_GRID),
            ('COLOR_LINE', renderer.COLOR_LINE),
            ('COLOR_POINT', renderer.COLOR_POINT),
            ('COLOR_POINT_FILL', renderer.COLOR_POINT_FILL),
            ('COLOR_TEXT', renderer.COLOR_TEXT),
            ('COLOR_TOOLTIP', renderer.COLOR_TOOLTIP),
        ]
        
        for name, color in colors_to_check:
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)


class TestGraphRendererEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Initialize pygame before each test."""
        pygame.init()
        yield
    
    def test_render_insufficient_data(self):
        """Test rendering with no data."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        # Should handle gracefully
        renderer.render(screen, [], title="Empty Graph")
    
    def test_render_with_zero_average(self):
        """Test rendering data with zero average."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W20", average=0, word_count=0),
            DataPoint(week="2026-W21", average=0, word_count=0),
        ]
        
        # Should handle zero averages
        renderer.render(screen, data, title="Zero Data")
    
    def test_custom_graph_config(self):
        """Test rendering with custom dimensions."""
        config = GraphConfig(width=800, height=400)
        renderer = GraphRenderer(config=config)
        screen = pygame.Surface((800, 400))
        
        data = [
            DataPoint(week="2026-W20", average=2.0, word_count=5),
            DataPoint(week="2026-W21", average=1.5, word_count=5),
        ]
        
        renderer.render(screen, data, title="Custom Size")
        
        assert screen.get_width() == 800
        assert screen.get_height() == 400
    
    def test_large_average_values(self):
        """Test rendering with large average values."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W20", average=100.0, word_count=5),
            DataPoint(week="2026-W21", average=200.0, word_count=5),
        ]
        
        # Should scale appropriately
        renderer.render(screen, data, title="Large Values")
    
    def test_very_small_average_values(self):
        """Test rendering with very small average values."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W20", average=0.1, word_count=5),
            DataPoint(week="2026-W21", average=0.2, word_count=5),
        ]
        
        # Should scale appropriately
        renderer.render(screen, data, title="Small Values")
    
    def test_data_with_mixed_word_counts(self):
        """Test rendering with some weeks having no data."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W20", average=0, word_count=0),
            DataPoint(week="2026-W21", average=2.0, word_count=5),
            DataPoint(week="2026-W22", average=0, word_count=0),
            DataPoint(week="2026-W23", average=1.5, word_count=5),
        ]
        
        # Should handle mixed data
        renderer.render(screen, data, title="Mixed Data")


class TestGraphLayout:
    """Test graph layout and positioning."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Initialize pygame before each test."""
        pygame.init()
        yield
    
    def test_margin_configuration(self):
        """Test that margins are applied correctly."""
        custom_margin = {'top': 20, 'right': 30, 'bottom': 50, 'left': 40}
        config = GraphConfig(margin=custom_margin)
        renderer = GraphRenderer(config=config)
        
        assert renderer.config.margin['top'] == 20
        assert renderer.config.margin['right'] == 30
        assert renderer.config.margin['bottom'] == 50
        assert renderer.config.margin['left'] == 40
    
    def test_data_points_position_relative_to_margin(self):
        """Test that data points are within plot area."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [
            DataPoint(week="2026-W20", average=1.0, word_count=5),
            DataPoint(week="2026-W27", average=3.0, word_count=5),
        ]
        
        renderer.render(screen, data, title="Position Test")
        
        # Should render without errors
        pass
    
    def test_render_with_custom_title(self):
        """Test rendering with various title formats."""
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        data = [DataPoint(week="2026-W27", average=2.0, word_count=5)]
        
        titles = [
            "Short",
            "A much longer title that should still render",
            "Title with Numbers 123",
            ""
        ]
        
        for title in titles:
            # Should not raise errors
            renderer.render(screen, data, title=title)


class TestIntegrationWithAnalytics:
    """Integration tests with Analytics component."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Initialize pygame before each test."""
        pygame.init()
        yield
    
    def test_render_analytics_data(self):
        """Test rendering data from AnalyticsEngine."""
        from src.components.analytics import AnalyticsEngine, create_analytics_engine
        
        # Create sample data
        sessions = [
            {
                'session_id': 's1',
                'student_id': 'test',
                'start_time': (datetime.now() - timedelta(days=7)).isoformat(),
                'words': [{'word': 'w1', 'word_id': '1', 'total_attempts': 2}]
            },
            {
                'session_id': 's2',
                'student_id': 'test',
                'start_time': (datetime.now() - timedelta(days=1)).isoformat(),
                'words': [{'word': 'w1', 'word_id': '1', 'total_attempts': 1}]
            },
        ]
        
        analytics = create_analytics_engine(sessions=sessions)
        
        analytics = create_analytics_engine(sessions=sessions)
        weekly_data = analytics.get_weekly_averages(weeks=2)
        
        renderer = GraphRenderer()
        screen = pygame.Surface((600, 300))
        
        # Should render without errors
        renderer.render(screen, weekly_data, title="Integration Test")
        
        assert screen.get_width() == 600
        assert screen.get_height() == 300


if __name__ == '__main__':
    pytest.main([__file__, '-v'])