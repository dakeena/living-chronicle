"""Maps simulation state to 64x64 LED grid."""

from dataclasses import dataclass
from typing import Any
import statistics

from chronicle.sim.ages import Age
from chronicle.data.models import DOMAINS

# Domain color mappings (RGB values 0-255)
DOMAIN_COLORS = {
    "river": (100, 150, 255),    # Blue tones - renewal, flow
    "flame": (255, 80, 40),       # Red/orange - destruction, passion
    "sky": (200, 200, 240),       # Pale blue/white - fate, distance
    "war": (180, 40, 40),         # Dark red - conflict, blood
    "harvest": (80, 200, 100),    # Green - abundance, growth
    "memory": (160, 100, 200),    # Violet - archives, past
}


@dataclass
class GridCell:
    """Represents a single LED cell in the 64x64 grid."""
    x: int
    y: int
    domain: str
    color: tuple[int, int, int]  # RGB
    brightness: float  # 0.0-1.0
    flicker_intensity: float  # 0.0-1.0
    is_scar: bool = False


class GridMapper:
    """
    Maps simulation state to 64x64 grid.

    Strategy:
    - Divide 64x64 grid into 8x8 regions (64 regions total)
    - Each region represents one cultural influence zone
    - Each region is 8x8 cells (64 cells per region)
    - Sample citizen beliefs to determine region's dominant domain
    - Calculate brightness from belief coherence
    - Calculate flicker from age and local conflict
    """

    GRID_SIZE = 64
    REGION_SIZE = 8  # 8x8 regions
    CELLS_PER_REGION = 8  # Each region is 8x8 cells

    def __init__(self):
        self.rng_seed = 0

    def map_state_to_grid(
        self,
        citizens: list[dict[str, Any]],
        gods: list[dict[str, Any]],
        factions: list[dict[str, Any]],
        age: Age,
        historical_scars: dict[tuple[int, int], dict[str, Any]]
    ) -> list[list[GridCell]]:
        """
        Map simulation state to 64x64 grid.

        Returns 2D array of GridCell objects.
        """
        # Initialize grid
        grid = [[None for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]

        # Create region map (8x8 regions)
        regions = self._create_region_map(citizens, factions)

        # Fill grid based on regions
        for region_x in range(self.REGION_SIZE):
            for region_y in range(self.REGION_SIZE):
                region_key = (region_x, region_y)
                region_data = regions.get(region_key, {
                    "domain": "memory",
                    "brightness": 0.1,
                    "coherence": 0.0,
                })

                # Fill 8x8 cells for this region
                start_x = region_x * self.CELLS_PER_REGION
                start_y = region_y * self.CELLS_PER_REGION

                for dx in range(self.CELLS_PER_REGION):
                    for dy in range(self.CELLS_PER_REGION):
                        cell_x = start_x + dx
                        cell_y = start_y + dy

                        # Check if this is a historical scar
                        is_scar = (cell_x, cell_y) in historical_scars

                        # Calculate flicker based on age and coherence
                        flicker = self._calculate_flicker(
                            age,
                            region_data["coherence"],
                            is_scar
                        )

                        # Adjust brightness for age effects
                        brightness = self._adjust_brightness_for_age(
                            age,
                            region_data["brightness"],
                            is_scar
                        )

                        domain = region_data["domain"]
                        color = DOMAIN_COLORS[domain]

                        grid[cell_y][cell_x] = GridCell(
                            x=cell_x,
                            y=cell_y,
                            domain=domain,
                            color=color,
                            brightness=brightness,
                            flicker_intensity=flicker,
                            is_scar=is_scar,
                        )

        return grid

    def _create_region_map(
        self,
        citizens: list[dict[str, Any]],
        factions: list[dict[str, Any]]
    ) -> dict[tuple[int, int], dict[str, Any]]:
        """
        Create region map from citizen beliefs.

        Strategy: Assign citizens to regions spatially, aggregate beliefs.
        """
        regions = {}

        # Handle empty citizen list
        if not citizens:
            # Return default regions with low memory belief
            for region_x in range(self.REGION_SIZE):
                for region_y in range(self.REGION_SIZE):
                    regions[(region_x, region_y)] = {
                        "domain": "memory",
                        "brightness": 0.1,
                        "coherence": 0.0,
                    }
            return regions

        citizen_count = len(citizens)
        citizens_per_region = max(1, citizen_count // (self.REGION_SIZE ** 2))

        for region_x in range(self.REGION_SIZE):
            for region_y in range(self.REGION_SIZE):
                region_key = (region_x, region_y)

                # Get citizens for this region (spatially distributed)
                start_idx = (region_y * self.REGION_SIZE + region_x) * citizens_per_region
                end_idx = min(start_idx + citizens_per_region, citizen_count)
                region_citizens = citizens[start_idx:end_idx]

                if not region_citizens:
                    # Empty region - default to low memory
                    regions[region_key] = {
                        "domain": "memory",
                        "brightness": 0.1,
                        "coherence": 0.0,
                    }
                    continue

                # Aggregate beliefs across all domains
                domain_totals = {d: 0.0 for d in DOMAINS}
                for citizen in region_citizens:
                    for domain, belief in citizen["beliefs"].items():
                        domain_totals[domain] += belief

                # Find dominant domain
                dominant_domain = max(domain_totals.items(), key=lambda x: x[1])[0]
                total_belief = domain_totals[dominant_domain]
                avg_belief = total_belief / len(region_citizens)

                # Calculate coherence (how unified beliefs are)
                # Coherence = 1 - variance (scaled)
                beliefs_in_domain = [
                    c["beliefs"].get(dominant_domain, 0.0)
                    for c in region_citizens
                ]

                if len(beliefs_in_domain) > 1:
                    variance = statistics.variance(beliefs_in_domain)
                    coherence = max(0.0, 1.0 - variance * 4)
                else:
                    coherence = 1.0

                regions[region_key] = {
                    "domain": dominant_domain,
                    "brightness": min(1.0, avg_belief),
                    "coherence": coherence,
                }

        return regions

    def _calculate_flicker(
        self,
        age: Age,
        coherence: float,
        is_scar: bool
    ) -> float:
        """
        Calculate flicker intensity for a cell.

        Flicker represents instability and ideological conflict.

        Base flicker by age:
        - Emergence: 0.15 (minimal, optimistic)
        - Order: 0.05 (very stable)
        - Strain: 0.4 (increasing tension)
        - Collapse: 0.8 (chaotic)
        - Silence: 0.1 (stillness)
        - Rebirth: 0.3 (growing rhythm)

        Low coherence increases flicker (+0.2 max)
        """
        if is_scar and age == Age.SILENCE:
            return 0.2  # Persistent faint flicker on scars

        base_flicker = {
            Age.EMERGENCE: 0.15,
            Age.ORDER: 0.05,
            Age.STRAIN: 0.4,
            Age.COLLAPSE: 0.8,
            Age.SILENCE: 0.1,
            Age.REBIRTH: 0.3,
        }[age]

        # Low coherence increases flicker
        coherence_factor = (1.0 - coherence) * 0.2

        return min(1.0, base_flicker + coherence_factor)

    def _adjust_brightness_for_age(
        self,
        age: Age,
        base_brightness: float,
        is_scar: bool
    ) -> float:
        """
        Adjust brightness based on age.

        Age modifiers:
        - Collapse: Grid dims to 40% (world darkens)
        - Silence: Dims to 10% except scars which stay at 30%
        - Rebirth: Scars glow brighter at 150%
        """
        brightness = base_brightness

        if age == Age.COLLAPSE:
            # Grid darkens during collapse
            return brightness * 0.4

        if age == Age.SILENCE:
            # Most of grid goes dark, scars remain faintly visible
            if is_scar:
                return max(brightness, 0.3)
            return brightness * 0.1

        if age == Age.REBIRTH and is_scar:
            # Scars glow brighter during rebirth
            return min(1.0, brightness * 1.5)

        return brightness

    def grid_to_json(self, grid: list[list[GridCell]]) -> list[list[dict[str, Any]]]:
        """Convert grid to JSON-serializable format."""
        return [
            [
                {
                    "x": cell.x,
                    "y": cell.y,
                    "domain": cell.domain,
                    "color": list(cell.color),  # Convert tuple to list for JSON
                    "brightness": cell.brightness,
                    "flicker": cell.flicker_intensity,
                    "is_scar": cell.is_scar,
                }
                for cell in row
            ]
            for row in grid
        ]
