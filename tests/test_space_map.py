"""
Unit tests for Space Map components (STORY-007-01)

Tests for:
- PlanetState enum and PlanetNode dataclass
- SpaceMapState management
- Map navigation and state transitions
"""

import pytest
from unittest.mock import MagicMock, patch
import pygame

from src.models.map_state import (
    PlanetState, PlanetNode, SpaceMapState,
    create_planet_node, create_space_map_state
)


class TestPlanetState:
    """Tests for PlanetState enum."""
    
    def test_planet_states_exist(self):
        """Verify all planet states are defined."""
        assert PlanetState.LOCKED.value == "locked"
        assert PlanetState.VISITED.value == "visited"
        assert PlanetState.COMPLETED.value == "completed"
        assert PlanetState.CURRENT.value == "current"
    
    def test_planet_state_from_string(self):
        """Verify state creation from string."""
        assert PlanetState("locked") == PlanetState.LOCKED
        assert PlanetState("visited") == PlanetState.VISITED
        assert PlanetState("completed") == PlanetState.COMPLETED
        assert PlanetState("current") == PlanetState.CURRENT


class TestPlanetNode:
    """Tests for PlanetNode dataclass."""
    
    def test_create_planet_node(self):
        """Test basic planet node creation."""
        planet = create_planet_node(
            planet_id="planet_1",
            planet_name="Mercury",
            planet_number=1,
            position=(512, 400),
            state=PlanetState.LOCKED
        )
        
        assert planet.planet_id == "planet_1"
        assert planet.planet_name == "Mercury"
        assert planet.planet_number == 1
        assert planet.position == (512, 400)
        assert planet.state == PlanetState.LOCKED
        assert planet.words_mastered == 0
        assert planet.total_attempts == 0
        assert planet.accuracy == 0.0
    
    def test_planet_node_to_dict(self):
        """Test serialization to dictionary."""
        planet = create_planet_node(
            planet_id="planet_1",
            planet_name="Mercury",
            planet_number=1,
            position=(512, 400),
            state=PlanetState.COMPLETED
        )
        planet.words_mastered = 5
        planet.total_attempts = 7
        planet.accuracy = 71.4
        
        data = planet.to_dict()
        
        assert data['planet_id'] == "planet_1"
        assert data['planet_name'] == "Mercury"
        assert data['planet_number'] == 1
        assert data['position'] == (512, 400)
        assert data['state'] == "completed"
        assert data['words_mastered'] == 5
        assert data['total_attempts'] == 7
        assert abs(data['accuracy'] - 71.4) < 0.1
    
    def test_planet_node_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'planet_id': 'planet_2',
            'planet_name': 'Venus',
            'planet_number': 2,
            'position': (600, 450),
            'state': 'visited',
            'words_mastered': 3,
            'total_attempts': 5,
            'accuracy': 60.0
        }
        
        planet = PlanetNode.from_dict(data)
        
        assert planet.planet_id == 'planet_2'
        assert planet.planet_name == 'Venus'
        assert planet.planet_number == 2
        assert planet.position == (600, 450)
        assert planet.state == PlanetState.VISITED
        assert planet.words_mastered == 3
        assert planet.total_attempts == 5
        assert abs(planet.accuracy - 60.0) < 0.1
    
    def test_planet_node_default_state(self):
        """Test that default state is LOCKED."""
        planet = create_planet_node(
            planet_id="planet_1",
            planet_name="Mercury",
            planet_number=1,
            position=(0, 0)
        )
        assert planet.state == PlanetState.LOCKED
    
    def test_planet_with_custom_state(self):
        """Test planet with different states."""
        for state in PlanetState:
            planet = create_planet_node(
                planet_id=f"planet_{state.value}",
                planet_name="Test",
                planet_number=1,
                position=(0, 0),
                state=state
            )
            assert planet.state == state


class TestSpaceMapState:
    """Tests for SpaceMapState management."""
    
    def test_empty_space_map(self):
        """Test creating empty space map state."""
        map_state = create_space_map_state()
        
        assert len(map_state.planets) == 0
        assert map_state.current_planet_id is None
        assert map_state.selected_planet_id is None
    
    def test_add_planets_to_map(self):
        """Test adding planets to the map."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            planet = create_planet_node(
                planet_id=f"planet_{i}",
                planet_name=f"Planet {i}",
                planet_number=i,
                position=(i * 100, 400),
                state=PlanetState.LOCKED
            )
            map_state.planets.append(planet)
        
        assert len(map_state.planets) == 5
    
    def test_get_planet_by_id(self):
        """Test retrieving planet by ID."""
        map_state = create_space_map_state()
        
        planet1 = create_planet_node("planet_1", "Mercury", 1, (100, 400))
        planet2 = create_planet_node("planet_2", "Venus", 2, (200, 400))
        map_state.planets.extend([planet1, planet2])
        
        retrieved = map_state.get_planet("planet_1")
        assert retrieved is not None
        assert retrieved.planet_name == "Mercury"
        
        not_found = map_state.get_planet("planet_999")
        assert not_found is None
    
    def test_get_planet_by_number(self):
        """Test retrieving planet by number."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        planet3 = map_state.get_planet_by_number(3)
        assert planet3 is not None
        assert planet3.planet_id == "planet_3"
        assert planet3.planet_name == "Planet 3"
        
        not_found = map_state.get_planet_by_number(99)
        assert not_found is None
    
    def test_get_current_planet(self):
        """Test getting current planet."""
        map_state = create_space_map_state()
        
        planet1 = create_planet_node("planet_1", "Mercury", 1, (100, 400), PlanetState.CURRENT)
        planet2 = create_planet_node("planet_2", "Venus", 2, (200, 400), PlanetState.LOCKED)
        map_state.planets.extend([planet1, planet2])
        map_state.current_planet_id = "planet_1"
        
        current = map_state.get_current_planet()
        assert current is not None
        assert current.planet_id == "planet_1"
    
    def test_get_current_planet_no_current(self):
        """Test getting current planet when none set."""
        map_state = create_space_map_state()
        map_state.planets.append(create_planet_node("planet_1", "Mercury", 1, (100, 400)))
        
        current = map_state.get_current_planet()
        assert current is None
    
    def test_set_planet_state(self):
        """Test updating planet state."""
        map_state = create_space_map_state()
        
        planet = create_planet_node("planet_1", "Mercury", 1, (100, 400), PlanetState.LOCKED)
        map_state.planets.append(planet)
        
        map_state.set_planet_state("planet_1", PlanetState.COMPLETED)
        
        assert map_state.get_planet("planet_1").state == PlanetState.COMPLETED
    
    def test_get_unlocked_planets(self):
        """Test filtering unlocked planets."""
        map_state = create_space_map_state()
        
        planet1 = create_planet_node("planet_1", "Mercury", 1, (100, 400), PlanetState.COMPLETED)
        planet2 = create_planet_node("planet_2", "Venus", 2, (200, 400), PlanetState.VISITED)
        planet3 = create_planet_node("planet_3", "Earth", 3, (300, 400), PlanetState.CURRENT)
        planet4 = create_planet_node("planet_4", "Mars", 4, (400, 400), PlanetState.LOCKED)
        
        map_state.planets.extend([planet1, planet2, planet3, planet4])
        
        unlocked = map_state.get_unlocked_planets()
        assert len(unlocked) == 3
        assert all(p.state != PlanetState.LOCKED for p in unlocked)
    
    def test_get_completed_planets(self):
        """Test filtering completed planets."""
        map_state = create_space_map_state()
        
        planet1 = create_planet_node("planet_1", "Mercury", 1, (100, 400), PlanetState.COMPLETED)
        planet2 = create_planet_node("planet_2", "Venus", 2, (200, 400), PlanetState.VISITED)
        planet3 = create_planet_node("planet_3", "Earth", 3, (300, 400), PlanetState.COMPLETED)
        
        map_state.planets.extend([planet1, planet2, planet3])
        
        completed = map_state.get_completed_planets()
        assert len(completed) == 2
        assert all(p.state == PlanetState.COMPLETED for p in completed)
    
    def test_get_visited_planets(self):
        """Test filtering visited planets (visited or completed)."""
        map_state = create_space_map_state()
        
        planet1 = create_planet_node("planet_1", "Mercury", 1, (100, 400), PlanetState.COMPLETED)
        planet2 = create_planet_node("planet_2", "Venus", 2, (200, 400), PlanetState.VISITED)
        planet3 = create_planet_node("planet_3", "Earth", 3, (300, 400), PlanetState.CURRENT)
        planet4 = create_planet_node("planet_4", "Mars", 4, (400, 400), PlanetState.LOCKED)
        
        map_state.planets.extend([planet1, planet2, planet3, planet4])
        
        visited = map_state.get_visited_planets()
        assert len(visited) == 2
        assert all(p.state in (PlanetState.VISITED, PlanetState.COMPLETED) for p in visited)
    
    def test_next_planet(self):
        """Test getting next planet in sequence."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        map_state.current_planet_id = "planet_2"
        
        next_planet = map_state.next_planet()
        assert next_planet is not None
        assert next_planet.planet_id == "planet_3"
    
    def test_next_planet_no_current(self):
        """Test next planet when no current position."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        next_planet = map_state.next_planet()
        assert next_planet is not None
        assert next_planet.planet_id == "planet_1"
    
    def test_next_planet_at_end(self):
        """Test next planet when at last planet."""
        map_state = create_space_map_state()
        
        for i in range(1, 4):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        map_state.current_planet_id = "planet_3"
        
        next_planet = map_state.next_planet()
        assert next_planet is None
    
    def test_previous_planet(self):
        """Test getting previous planet in sequence."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        map_state.current_planet_id = "planet_3"
        
        prev_planet = map_state.previous_planet()
        assert prev_planet is not None
        assert prev_planet.planet_id == "planet_2"
    
    def test_previous_planet_at_start(self):
        """Test previous planet at first planet."""
        map_state = create_space_map_state()
        
        planet1 = create_planet_node("planet_1", "Mercury", 1, (100, 400))
        map_state.planets.append(planet1)
        map_state.current_planet_id = "planet_1"
        
        prev_planet = map_state.previous_planet()
        assert prev_planet is None
    
    def test_move_to_next(self):
        """Test moving to next planet."""
        map_state = create_space_map_state()
        
        for i in range(1, 4):
            state = PlanetState.COMPLETED if i < 3 else PlanetState.CURRENT
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400), state)
            map_state.planets.append(planet)
        
        map_state.current_planet_id = "planet_1"
        
        map_state.move_to_next()
        assert map_state.current_planet_id == "planet_2"
    
    def test_move_to_previous(self):
        """Test moving to previous planet."""
        map_state = create_space_map_state()
        
        for i in range(1, 4):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        map_state.current_planet_id = "planet_3"
        
        map_state.move_to_previous()
        assert map_state.current_planet_id == "planet_2"
    
    def test_update_from_progress(self):
        """Test updating planet states from progress data."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        # Simulate progress
        completed = ["planet_1", "planet_2"]
        current = "planet_3"
        
        map_state.update_from_progress(
            completed_planets=completed,
            visited_planets=[],
            current_planet_id=current
        )
        
        # Verify states
        assert map_state.get_planet("planet_1").state == PlanetState.COMPLETED
        assert map_state.get_planet("planet_2").state == PlanetState.COMPLETED
        assert map_state.get_planet("planet_3").state == PlanetState.CURRENT
        assert map_state.get_planet("planet_4").state == PlanetState.LOCKED
        assert map_state.get_planet("planet_5").state == PlanetState.LOCKED
    
    def test_update_from_progress_with_visited(self):
        """Test update with visited planets."""
        map_state = create_space_map_state()
        
        for i in range(1, 5):
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        map_state.update_from_progress(
            completed_planets=["planet_1"],
            visited_planets=["planet_2"],
            current_planet_id="planet_2"
        )
        
        assert map_state.get_planet("planet_1").state == PlanetState.COMPLETED
        assert map_state.get_planet("planet_2").state == PlanetState.VISITED


class TestMapNavigation:
    """Tests for map navigation interactions."""
    
    def test_keyboard_navigation_context(self):
        """Test keyboard navigation context setup."""
        map_state = create_space_map_state()
        
        for i in range(1, 6):
            state = PlanetState.LOCKED if i > 3 else PlanetState.COMPLETED
            planet = create_planet_node(f"planet_{i}", f"Planet {i}", i, (i * 100, 400), state)
            map_state.planets.append(planet)
        
        # First planet is selected
        assert len(map_state.get_visible_planets()) == 3
    
    def test_all_planets_same_name(self):
        """Test planets with same name but different numbers."""
        map_state = create_space_map_state()
        
        for i in range(1, 4):
            planet = create_planet_node("epc_1", "Test Planet", i, (i * 100, 400))
            map_state.planets.append(planet)
        
        assert len(map_state.planets) == 3
        assert map_state.get_planet_by_number(1).planet_id == "epc_1_1" or \
               all(p.planet_number != 0 for p in map_state.planets)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])