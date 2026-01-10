"""Emergent god system for Living Chronicle."""

from dataclasses import dataclass
from typing import Optional
import random

from ..data.models import DOMAINS, GodRow
from ..data.database import Database
from .entities import God, Citizen


# Thresholds for god emergence and fading
BELIEF_THRESHOLD = 0.6  # minimum aggregate belief to birth a god
COHERENCE_THRESHOLD = 0.5  # minimum coherence (agreement) among believers
CONSECUTIVE_DAYS_BIRTH = 5  # days above threshold to birth
CONSECUTIVE_DAYS_FADE = 7  # days below threshold to fade
FADE_THRESHOLD = 0.3  # belief below this starts fade counter


@dataclass
class BeliefAggregation:
    """Aggregated belief data for a domain."""
    domain: str
    total_belief: float
    believer_count: int
    average_belief: float
    coherence: float  # how consistent beliefs are (low variance = high coherence)


class GodSystem:
    """Manages emergent god creation and fading."""

    def __init__(self, db: Database, rng: random.Random):
        self.db = db
        self.rng = rng
        # Track consecutive days for proto-gods (domains approaching godhood)
        self._proto_god_days: dict[str, int] = {domain: 0 for domain in DOMAINS}

    def aggregate_beliefs(self, citizens: list[Citizen]) -> dict[str, BeliefAggregation]:
        """Calculate aggregate belief for each domain."""
        aggregations = {}

        for domain in DOMAINS:
            beliefs = [c.row.belief_vector.get(domain, 0.0) for c in citizens]
            if not beliefs:
                aggregations[domain] = BeliefAggregation(
                    domain=domain,
                    total_belief=0.0,
                    believer_count=0,
                    average_belief=0.0,
                    coherence=0.0,
                )
                continue

            total = sum(beliefs)
            avg = total / len(beliefs)

            # Coherence: inverse of variance (normalized)
            variance = sum((b - avg) ** 2 for b in beliefs) / len(beliefs)
            coherence = max(0.0, 1.0 - variance * 4)  # scale variance to 0-1

            # Count believers (those with belief > 0.3)
            believer_count = sum(1 for b in beliefs if b > 0.3)

            aggregations[domain] = BeliefAggregation(
                domain=domain,
                total_belief=total,
                believer_count=believer_count,
                average_belief=avg,
                coherence=coherence,
            )

        return aggregations

    def process_gods(
        self,
        citizens: list[Citizen],
        current_day: int
    ) -> tuple[list[God], list[God]]:
        """
        Process god births and deaths for this tick.
        Returns (newly_born_gods, newly_faded_gods).
        """
        aggregations = self.aggregate_beliefs(citizens)
        born = []
        faded = []

        # Check existing gods for fading
        existing_gods = [God(row) for row in self.db.get_all_gods(alive_only=True)]
        for god in existing_gods:
            agg = aggregations[god.row.domain]
            god.update_strength(agg.average_belief, agg.coherence)

            if agg.average_belief < FADE_THRESHOLD:
                god.row.consecutive_weak_days += 1
                god.row.consecutive_strong_days = 0
                if god.row.consecutive_weak_days >= CONSECUTIVE_DAYS_FADE:
                    god.fade(current_day)
                    faded.append(god)
            else:
                god.row.consecutive_weak_days = 0
                god.row.consecutive_strong_days += 1

            self.db.save_god(god.row)

        # Check for new god births
        living_domains = {g.row.domain for g in existing_gods if g.row.alive}

        for domain, agg in aggregations.items():
            if domain in living_domains:
                self._proto_god_days[domain] = 0
                continue

            if agg.average_belief >= BELIEF_THRESHOLD and agg.coherence >= COHERENCE_THRESHOLD:
                self._proto_god_days[domain] += 1
                if self._proto_god_days[domain] >= CONSECUTIVE_DAYS_BIRTH:
                    god = God.birth(
                        domain=domain,
                        belief_strength=agg.average_belief,
                        coherence=agg.coherence,
                        day=current_day,
                        rng=self.rng
                    )
                    self.db.save_god(god.row)
                    born.append(god)
                    self._proto_god_days[domain] = 0
            else:
                self._proto_god_days[domain] = 0

        return born, faded

    def force_belief_for_domain(
        self,
        citizens: list[Citizen],
        domain: str,
        belief_level: float
    ) -> None:
        """Force beliefs for testing god emergence."""
        for citizen in citizens:
            citizen.row.belief_vector[domain] = belief_level
