"""
Rhythmic Agent - Controls tempo and rhythmic feel of the composition.
"""

import random
from typing import List, Dict, Any
from agents.base import MusicalAgent
from core.context import MusicalContext


class RhythmicAgent(MusicalAgent):
    """
    Agent responsible for controlling tempo and rhythmic elements.

    Manages tempo changes (accelerando/ritardando) based on musical intensity
    and can add percussive rhythmic patterns for emphasis.
    """

    def __init__(self, objectives: Dict[str, Any] = None):
        """
        Initialize the Rhythmic Agent.

        Args:
            objectives: Agent objectives, including:
                - base_tempo: Base tempo in BPM (default 90)
                - tempo_range: (min_tempo, max_tempo) (default (70, 120))
                - tempo_sensitivity: How much intensity affects tempo (default 0.5)
                - add_percussion: Whether to add percussion (default False)
        """
        super().__init__(role="rhythmic", objectives=objectives)

        self.base_tempo = self.objectives.get("base_tempo", 90)
        self.tempo_range = self.objectives.get("tempo_range", (70, 120))
        self.tempo_sensitivity = self.objectives.get("tempo_sensitivity", 0.5)
        self.add_percussion = self.objectives.get("add_percussion", False)

        # Tempo evolution tracking
        self.target_tempo = self.base_tempo
        self.tempo_change_rate = 2  # BPM change per step

    def listen(self, context: MusicalContext) -> Dict[str, Any]:
        """
        Analyze the current musical state for rhythmic decisions.

        Args:
            context: The shared musical context

        Returns:
            Dictionary with:
                - current_tempo: Current tempo
                - intensity: Musical intensity
                - harmonic_tension: Harmonic tension level
                - measure: Current measure
        """
        return {
            "current_tempo": context.tempo,
            "intensity": context.intensity,
            "harmonic_tension": context.harmonic_tension,
            "measure": context.current_measure,
            "position": context.measure_position
        }

    def decide(self, analysis: Dict[str, Any], context: MusicalContext) -> Dict[str, Any]:
        """
        Decide tempo and rhythmic modifications.

        Args:
            analysis: Analyzed features
            context: Musical context

        Returns:
            Decision dictionary with:
                - target_tempo: Desired tempo
                - tempo_change: Change from current tempo
                - add_accent: Whether to add rhythmic accent
        """
        intensity = analysis["intensity"]
        tension = analysis["harmonic_tension"]
        current_tempo = analysis["current_tempo"]

        # Calculate target tempo based on intensity and tension
        # Higher intensity + tension = faster tempo
        intensity_factor = intensity * self.tempo_sensitivity
        tension_factor = tension * (1 - self.tempo_sensitivity)

        combined_energy = (intensity_factor + tension_factor)

        # Map energy (0.0-1.0) to tempo range
        min_tempo, max_tempo = self.tempo_range
        target_tempo = min_tempo + (max_tempo - min_tempo) * combined_energy

        # Add slight randomness for organic feel
        target_tempo += random.uniform(-3, 3)
        target_tempo = max(min_tempo, min(max_tempo, target_tempo))

        self.target_tempo = target_tempo

        # Gradual tempo change (don't jump immediately)
        tempo_diff = target_tempo - current_tempo
        if abs(tempo_diff) > self.tempo_change_rate:
            tempo_change = self.tempo_change_rate if tempo_diff > 0 else -self.tempo_change_rate
        else:
            tempo_change = tempo_diff

        new_tempo = int(current_tempo + tempo_change)

        # Decide whether to add accent (high intensity moments)
        add_accent = intensity > 0.7 and random.random() < 0.3

        decision = {
            "target_tempo": int(target_tempo),
            "new_tempo": new_tempo,
            "tempo_change": tempo_change,
            "add_accent": add_accent,
            "measure": context.current_measure
        }

        return decision

    def act(self, decision: Dict[str, Any], context: MusicalContext) -> List[Dict[str, Any]]:
        """
        Apply tempo changes and generate rhythmic events if needed.

        Args:
            decision: Decision from decide()
            context: Musical context (will be updated)

        Returns:
            List of MIDI events (percussion if enabled)
        """
        # Update tempo in context
        new_tempo = decision["new_tempo"]
        context.tempo = new_tempo

        events = []

        # Add percussion accent if enabled and decided
        if self.add_percussion and decision["add_accent"]:
            # Add a percussion hit (e.g., kick drum or hand clap)
            events.append({
                "type": "note_on",
                "note": 36,  # MIDI 36 = Bass Drum 1 (GM standard)
                "velocity": 90,
                "time": 0.0,
                "duration": 0.25,
                "channel": 9  # Channel 10 (index 9) is percussion in GM
            })

        return events

    def reset(self):
        """Reset the agent to initial state."""
        super().reset()
        self.target_tempo = self.base_tempo


class PercussionPattern:
    """
    Helper class for generating percussion patterns.
    (Optional - can be used for more complex rhythmic elements)
    """

    # Common percussion patterns (GM MIDI percussion notes)
    KICK = 36
    SNARE = 38
    CLOSED_HI_HAT = 42
    OPEN_HI_HAT = 46
    CRASH = 49

    @staticmethod
    def basic_beat(measure_position: float, intensity: float = 0.5) -> List[Dict[str, Any]]:
        """
        Generate a basic 4/4 beat pattern.

        Args:
            measure_position: Current position in measure (0.0-1.0)
            intensity: How strong the beat should be

        Returns:
            List of percussion MIDI events
        """
        events = []

        # Kick on beats 1 and 3
        if measure_position < 0.1 or (0.49 < measure_position < 0.51):
            events.append({
                "type": "note_on",
                "note": PercussionPattern.KICK,
                "velocity": int(80 + intensity * 20),
                "time": 0.0,
                "duration": 0.25,
                "channel": 9
            })

        # Snare on beats 2 and 4
        if (0.24 < measure_position < 0.26) or (0.74 < measure_position < 0.76):
            events.append({
                "type": "note_on",
                "note": PercussionPattern.SNARE,
                "velocity": int(70 + intensity * 20),
                "time": 0.0,
                "duration": 0.25,
                "channel": 9
            })

        # Hi-hat on every eighth note (if high intensity)
        if intensity > 0.6:
            eighth_positions = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
            for pos in eighth_positions:
                if abs(measure_position - pos) < 0.05:
                    events.append({
                        "type": "note_on",
                        "note": PercussionPattern.CLOSED_HI_HAT,
                        "velocity": int(50 + intensity * 20),
                        "time": 0.0,
                        "duration": 0.125,
                        "channel": 9
                    })
                    break

        return events
