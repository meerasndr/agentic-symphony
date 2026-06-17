"""
Textural Agent - Manages dynamics, voice density, and musical texture.
"""

import random
from typing import List, Dict, Any
from agents.base import MusicalAgent
from core.context import MusicalContext


class TexturalAgent(MusicalAgent):
    """
    Agent responsible for controlling musical texture and dynamics.

    Manages:
    - Dynamics (MIDI velocity levels)
    - Voice density (how many agents should be active)
    - Strategic pauses and rests
    - Intensity arcs across the composition
    """

    # Instrument palettes based on intensity
    # General MIDI program numbers
    INSTRUMENT_PALETTES = {
        "soft": {
            "harmonic": 52,  # Choir Aahs (ethereal, soft)
            "melodic": 73,   # Flute (light, airy)
        },
        "medium": {
            "harmonic": 0,   # Acoustic Grand Piano (balanced)
            "melodic": 40,   # Violin (expressive)
        },
        "bright": {
            "harmonic": 48,  # String Ensemble (full, rich)
            "melodic": 56,   # Trumpet (bright, bold)
        },
        "dark": {
            "harmonic": 19,  # Church Organ (solemn, deep)
            "melodic": 42,   # Cello (warm, dark)
        }
    }

    def __init__(self, objectives: Dict[str, Any] = None):
        """
        Initialize the Textural Agent.

        Args:
            objectives: Agent objectives, including:
                - dynamic_range: (min, max) velocity multiplier (default (0.5, 1.2))
                - pause_probability: Probability of suggesting pause (default 0.05)
                - voice_density_control: Enable voice density management (default True)
                - crescendo_rate: How quickly dynamics build (default 0.05)
                - enable_instrument_selection: Let agent choose instruments (default True)
        """
        super().__init__(role="textural", objectives=objectives)

        self.dynamic_range = self.objectives.get("dynamic_range", (0.5, 1.2))
        self.pause_probability = self.objectives.get("pause_probability", 0.05)
        self.voice_density_control = self.objectives.get("voice_density_control", True)
        self.crescendo_rate = self.objectives.get("crescendo_rate", 0.05)
        self.enable_instrument_selection = self.objectives.get("enable_instrument_selection", True)

        # Track dynamics evolution
        self.current_dynamic_level = 0.7  # Start at medium-low (mf)
        self.target_dynamic_level = 0.7

        # Track current instruments
        self.current_harmonic_instrument = 0  # Start with piano
        self.current_melodic_instrument = 40  # Start with violin

    def listen(self, context: MusicalContext) -> Dict[str, Any]:
        """
        Analyze the current musical state for textural decisions.

        Args:
            context: The shared musical context

        Returns:
            Dictionary with:
                - intensity: Current intensity level
                - harmonic_tension: Harmonic tension
                - measure: Current measure
                - recent_notes_count: Number of recent notes
        """
        return {
            "intensity": context.intensity,
            "harmonic_tension": context.harmonic_tension,
            "measure": context.current_measure,
            "position": context.measure_position,
            "recent_notes_count": len(context.recent_notes),
            "current_dynamic": self.current_dynamic_level
        }

    def decide(self, analysis: Dict[str, Any], context: MusicalContext) -> Dict[str, Any]:
        """
        Decide textural and dynamic modifications.

        Args:
            analysis: Analyzed features
            context: Musical context

        Returns:
            Decision dictionary with:
                - dynamic_multiplier: Velocity multiplier (0.0-1.5)
                - voice_density: Number of voices to activate (1-4)
                - suggest_pause: Whether to suggest a pause
                - dynamic_marking: Dynamic level name (pp, p, mp, mf, f, ff)
        """
        intensity = analysis["intensity"]
        tension = analysis["harmonic_tension"]
        measure = analysis["measure"]

        # Calculate target dynamic level based on intensity and tension
        # Higher intensity = louder dynamics
        target_dynamic = 0.3 + (intensity * 0.7)  # Range: 0.3 to 1.0

        # Harmonic tension also influences dynamics (tension = louder)
        target_dynamic += tension * 0.2

        # Clamp to valid range
        target_dynamic = max(0.3, min(1.2, target_dynamic))

        # Move current dynamic toward target (gradual crescendo/diminuendo)
        dynamic_diff = target_dynamic - self.current_dynamic_level
        if abs(dynamic_diff) > self.crescendo_rate:
            self.current_dynamic_level += self.crescendo_rate if dynamic_diff > 0 else -self.crescendo_rate
        else:
            self.current_dynamic_level = target_dynamic

        # Determine voice density based on intensity
        # Low intensity = fewer voices, high intensity = more voices
        if intensity < 0.3:
            voice_density = 1  # Solo voice
        elif intensity < 0.5:
            voice_density = 2  # Two voices
        elif intensity < 0.7:
            voice_density = 3  # Three voices
        else:
            voice_density = 4  # Full ensemble

        # Decide on strategic pause
        # More likely at low intensity, or after high tension resolves
        suggest_pause = False
        if intensity < 0.25 and random.random() < self.pause_probability:
            suggest_pause = True
        # Also consider pauses after tension resolution
        if tension < 0.1 and intensity < 0.4 and random.random() < self.pause_probability * 2:
            suggest_pause = True

        # Map dynamic level to musical marking
        if self.current_dynamic_level < 0.4:
            dynamic_marking = "pp"  # pianissimo
        elif self.current_dynamic_level < 0.55:
            dynamic_marking = "p"   # piano
        elif self.current_dynamic_level < 0.7:
            dynamic_marking = "mp"  # mezzo-piano
        elif self.current_dynamic_level < 0.85:
            dynamic_marking = "mf"  # mezzo-forte
        elif self.current_dynamic_level < 1.0:
            dynamic_marking = "f"   # forte
        else:
            dynamic_marking = "ff"  # fortissimo

        # Select instruments based on intensity and tension (EMERGENT!)
        harmonic_instrument = self.current_harmonic_instrument
        melodic_instrument = self.current_melodic_instrument
        instrument_change = False

        if self.enable_instrument_selection:
            # Choose palette based on intensity and tension
            if intensity < 0.3:
                palette = "soft"
            elif tension > 0.7:
                palette = "dark"  # High tension → darker timbres
            elif intensity > 0.75:
                palette = "bright"  # High intensity → bright timbres
            else:
                palette = "medium"  # Balanced

            # Get instruments from palette
            new_harmonic = self.INSTRUMENT_PALETTES[palette]["harmonic"]
            new_melodic = self.INSTRUMENT_PALETTES[palette]["melodic"]

            # Only change if different
            if new_harmonic != self.current_harmonic_instrument or new_melodic != self.current_melodic_instrument:
                instrument_change = True
                harmonic_instrument = new_harmonic
                melodic_instrument = new_melodic
                self.current_harmonic_instrument = new_harmonic
                self.current_melodic_instrument = new_melodic

        decision = {
            "dynamic_multiplier": self.current_dynamic_level,
            "voice_density": voice_density,
            "suggest_pause": suggest_pause,
            "dynamic_marking": dynamic_marking,
            "harmonic_instrument": harmonic_instrument,
            "melodic_instrument": melodic_instrument,
            "instrument_change": instrument_change,
            "measure": measure,
            "intensity": intensity
        }

        return decision

    def act(self, decision: Dict[str, Any], context: MusicalContext) -> List[Dict[str, Any]]:
        """
        Apply textural decisions to the context.

        The textural agent doesn't generate its own notes - it modifies
        the context so other agents will respond to its textural decisions.

        Args:
            decision: Decision from decide()
            context: Musical context (will be updated)

        Returns:
            Empty list (no MIDI events generated directly)
        """
        # Store textural decisions in context for other agents to use
        # We'll add these as custom attributes to the context

        # Dynamic multiplier for velocity adjustments
        context.dynamic_multiplier = decision["dynamic_multiplier"]

        # Voice density suggestion
        context.voice_density = decision["voice_density"]

        # Pause suggestion
        context.suggest_pause = decision["suggest_pause"]

        # Instrument selections (emergent behavior!)
        context.harmonic_instrument = decision["harmonic_instrument"]
        context.melodic_instrument = decision["melodic_instrument"]

        # No MIDI events generated by textural agent
        # It influences how OTHER agents generate their events
        return []

    def reset(self):
        """Reset the agent to initial state."""
        super().reset()
        self.current_dynamic_level = 0.7
        self.target_dynamic_level = 0.7


def apply_textural_modifications(events: List[Dict[str, Any]], context: MusicalContext) -> List[Dict[str, Any]]:
    """
    Helper function to apply textural modifications to generated events.

    This should be called AFTER agents generate their events to apply
    dynamics and voice density controls.

    Args:
        events: List of MIDI events from agents
        context: Musical context with textural settings

    Returns:
        Modified list of events
    """
    if not events:
        return events

    # Get textural parameters from context
    dynamic_multiplier = getattr(context, "dynamic_multiplier", 1.0)
    voice_density = getattr(context, "voice_density", 4)
    suggest_pause = getattr(context, "suggest_pause", False)

    # If pause is suggested, skip all events
    if suggest_pause:
        return []

    # Apply voice density control
    # Group events by channel (each agent typically uses a different channel)
    channel_events = {}
    for event in events:
        channel = event.get("channel", 0)
        if channel not in channel_events:
            channel_events[channel] = []
        channel_events[channel].append(event)

    # Select which channels to keep based on voice density
    active_channels = sorted(channel_events.keys())[:voice_density]

    # Apply dynamic multiplier to selected channels
    modified_events = []
    for channel in active_channels:
        for event in channel_events[channel]:
            # Modify velocity
            if "velocity" in event:
                original_velocity = event["velocity"]
                new_velocity = int(original_velocity * dynamic_multiplier)
                # Clamp to MIDI range with some headroom
                new_velocity = max(20, min(120, new_velocity))
                event["velocity"] = new_velocity

            modified_events.append(event)

    return modified_events
