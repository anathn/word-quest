"""
Map State Models

Data models for space map state management.
Used for tracking planet states (locked, visited, completed, current)
and managing the progression through the galaxy.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class PlanetState(Enum):
    """Status of a planet in the space map."""
    LOCKED = "locked"
    VISITED = "visited"
    COMPLETED = "completed"
    CURRENT = "current"


@dataclass
class PlanetNode:
    """Represents a single planet in the space map."""
    planet_id: str
    planet_name: str
    planet_number: int
    position: Tuple[int, int]  # (x, y) screen coordinates
    state: PlanetState = PlanetState.LOCKED
    words_mastered: int = 0
    total_attempts: int = 0
    accuracy: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'planet_id': self.planet_id,
            'planet_name': self.planet_name,
            'planet_number': self.planet_number,
            'position': self.position,
            'state': self.state.value,
            'words_mastered': self.words_mastered,
            'total_attempts': self.total_attempts,
            'accuracy': self.accuracy
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlanetNode':
        """Create from dictionary."""
        return cls(
            planet_id=data['planet_id'],
            planet_name=data['planet_name'],
            planet_number=data['planet_number'],
            position=tuple(data['position']),
            state=PlanetState(data.get('state', 'locked')),
            words_mastered=data.get('words_mastered', 0),
            total_attempts=data.get('total_attempts', 0),
            accuracy=data.get('accuracy', 0.0)
        )


@dataclass
class SpaceMapState:
    """Complete state of the space map."""
    planets: List[PlanetNode] = field(default_factory=list)
    current_planet_id: Optional[str] = None
    selected_planet_id: Optional[str] = None
    
    def get_current_planet(self) -> Optional[PlanetNode]:
        """Get the current planet node."""
        if self.current_planet_id:
            return self.get_planet(self.current_planet_id)
        return None
    
    def get_selected_planet(self) -> Optional[PlanetNode]:
        """Get the currently selected planet (for details view)."""
        if self.selected_planet_id:
            return self.get_planet(self.selected_planet_id)
        return None
    
    def get_planet(self, planet_id: str) -> Optional[PlanetNode]:
        """Get a planet by ID."""
        for planet in self.planets:
            if planet.planet_id == planet_id:
                return planet
        return None
    
    def get_planet_by_number(self, planet_number: int) -> Optional[PlanetNode]:
        """Get a planet by its number."""
        for planet in self.planets:
            if planet.planet_number == planet_number:
                return planet
        return None
    
    def set_planet_state(self, planet_id: str, state: PlanetState):
        """Update the state of a planet."""
        planet = self.get_planet(planet_id)
        if planet:
            planet.state = state
    
    def get_unlocked_planets(self) -> List[PlanetNode]:
        """Get all planets that are unlocked (not locked)."""
        return [p for p in self.planets if p.state != PlanetState.LOCKED]
    
    def get_visible_planets(self) -> List[PlanetNode]:
        """Get all visible planets (not locked)."""
        return self.get_unlocked_planets()
    
    def get_completed_planets(self) -> List[PlanetNode]:
        """Get all completed planets."""
        return [p for p in self.planets if p.state == PlanetState.COMPLETED]
    
    def get_visited_planets(self) -> List[PlanetNode]:
        """Get all visited planets (visited or completed)."""
        return [p for p in self.planets if p.state in (PlanetState.VISITED, PlanetState.COMPLETED)]
    
    def next_planet(self) -> Optional[PlanetNode]:
        """Get the next planet in sequence from current position."""
        current = self.get_current_planet()
        if not current:
            return self.get_planet_by_number(1)  # Start with first planet
        
        next_number = current.planet_number + 1
        return self.get_planet_by_number(next_number)
    
    def previous_planet(self) -> Optional[PlanetNode]:
        """Get the previous planet in sequence from current position."""
        current = self.get_current_planet()
        if not current:
            return None
        
        prev_number = current.planet_number - 1
        if prev_number < 1:
            return None
        return self.get_planet_by_number(prev_number)
    
    def move_to_next(self):
        """Move current position to next unlocked planet."""
        next_planet = self.next_planet()
        if next_planet and next_planet.state != PlanetState.LOCKED:
            self.current_planet_id = next_planet.planet_id
    
    def move_to_previous(self):
        """Move current position to previous planet."""
        prev_planet = self.previous_planet()
        if prev_planet:
            self.current_planet_id = prev_planet.planet_id
    
    def update_from_progress(self, completed_planets: List[str], visited_planets: List[str], current_planet_id: Optional[str]):
        """Update planet states based on progress data."""
        for planet in self.planets:
            if planet.planet_id in completed_planets:
                planet.state = PlanetState.COMPLETED
            elif planet.planet_id in visited_planets:
                planet.state = PlanetState.VISITED
            elif planet.planet_id == current_planet_id:
                planet.state = PlanetState.CURRENT
            else:
                # Check if this planet is unlocked (any previous planet completed)
                if any(prev_id in completed_planets for prev_id in self._get_previous_planet_ids(planet.planet_id)):
                    planet.state = PlanetState.LOCKED  # Actually unlocked but not visited
                else:
                    planet.state = PlanetState.LOCKED
        
        self.current_planet_id = current_planet_id
    
    def _get_previous_planet_ids(self, planet_id: str) -> List[str]:
        """Get IDs of all planets before this one."""
        planet = self.get_planet(planet_id)
        if not planet:
            return []
        
        return [p.planet_id for p in self.planets if p.planet_number < planet.planet_number]


# Factory functions
def create_planet_node(
    planet_id: str,
    planet_name: str,
    planet_number: int,
    position: Tuple[int, int],
    state: PlanetState = PlanetState.LOCKED
) -> PlanetNode:
    """Create a PlanetNode instance."""
    return PlanetNode(
        planet_id=planet_id,
        planet_name=planet_name,
        planet_number=planet_number,
        position=position,
        state=state
    )


def create_space_map_state() -> SpaceMapState:
    """Create a SpaceMapState instance."""
    return SpaceMapState()