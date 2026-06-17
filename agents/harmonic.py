"""
Harmonic Agent - Generates chord progressions using weighted Markov chains.
"""

import random
from typing import List, Dict, Any
from agents.base import MusicalAgent
from core.context import MusicalContext
from core.music_theory import (
    get_chord_notes_from_symbol,
    get_chord_note_names,
    parse_chord_symbol
)


class HarmonicAgent(MusicalAgent):
    """
    Agent responsible for generating chord progressions.

    Uses weighted Markov chains to create musically coherent progressions
    that follow common harmonic patterns while allowing for variation.
    """

    # Chord transition probability table
    # Format: {current_chord_degree: {next_chord_degree: weight}}
    # Higher weights = more likely transitions
    TRANSITION_WEIGHTS = {
        1: {1: 10, 2: 20, 3: 10, 4: 40, 5: 50, 6: 30},  # I can go anywhere, but V and IV are common
        2: {5: 70, 1: 10, 4: 15, 6: 5},                  # ii usually goes to V (ii-V-I)
        3: {6: 50, 4: 30, 2: 10, 5: 10},                 # iii to vi is common
        4: {5: 50, 1: 30, 2: 15, 6: 5},                  # IV to V or I
        5: {1: 80, 6: 15, 4: 5},                          # V strongly resolves to I
        6: {4: 50, 2: 30, 5: 15, 3: 5},                  # vi to IV or ii
    }

    # Chord degree to chord symbol in C major
    DEGREE_TO_SYMBOL = {
        1: "C",     # I - tonic major
        2: "Dm",    # ii - supertonic minor
        3: "Em",    # iii - mediant minor
        4: "F",     # IV - subdominant major
        5: "G",     # V - dominant major
        6: "Am",    # vi - submediant minor
        7: "Bdim",  # vii° - leading tone diminished (rarely used)
    }

    def __init__(self, objectives: Dict[str, Any] = None):
        """
        Initialize the Harmonic Agent.

        Args:
            objectives: Agent objectives, including:
                - key: Musical key (default "C")
                - surprise_rate: Probability of unexpected chord (default 0.1)
                - chord_duration: Duration of each chord in beats (default 4.0)
                - voicing: "block" or "arpeggio" (default "block")
        """
        super().__init__(role="harmonic", objectives=objectives)

        self.key = self.objectives.get("key", "C")
        self.surprise_rate = self.objectives.get("surprise_rate", 0.1)
        self.chord_duration = self.objectives.get("chord_duration", 4.0)
        self.voicing = self.objectives.get("voicing", "block")

        # Current position in progression
        self.current_degree = 1  # Start on I chord

        # Track last instrument sent (to avoid duplicate program changes)
        self.last_instrument = None

    def listen(self, context: MusicalContext) -> Dict[str, Any]:
        """
        Analyze the current harmonic state.

        Args:
            context: The shared musical context

        Returns:
            Dictionary with:
                - current_measure: Current measure number
                - position_in_measure: Position within measure
                - intensity: Current intensity level
                - recent_chords: Recently played chords
        """
        # Get recent chord history from memory
        recent_chords = [d.get("degree") for d in self.get_recent_memory(4) if "degree" in d]

        return {
            "current_measure": context.current_measure,
            "position_in_measure": context.measure_position,
            "intensity": context.intensity,
            "recent_chords": recent_chords,
            "current_degree": self.current_degree
        }

    def decide(self, analysis: Dict[str, Any], context: MusicalContext) -> Dict[str, Any]:
        """
        Decide which chord to play next using weighted Markov chain.

        Args:
            analysis: Analyzed features
            context: Musical context

        Returns:
            Decision dictionary with:
                - degree: Chord degree (1-7)
                - chord_symbol: Chord symbol (e.g., "C", "Am")
                - duration: Duration in beats
                - is_surprise: Whether this was a surprising choice
                - feedback_response: Type of feedback response (if any)
        """
        current_degree = self.current_degree
        is_surprise = False
        feedback_response = None

        # FEEDBACK LOOP: React to melodic tension from previous bar
        if context.melodic_tension > 0.6:
            # High melodic tension: Force resolution to tonic (negative feedback)
            next_degree = 1  # Resolve to I chord
            feedback_response = "resolve"
            print(f"  🔄 FEEDBACK: Harmonic agent resolving high melodic tension ({context.melodic_tension:.2f}) → I")
        elif context.melodic_tension > 0.4 and random.random() < 0.5:
            # Moderate melodic tension: Acknowledge with subdominant (positive feedback)
            # This creates a "conversation" - melody explores, harmony responds
            next_degree = 4  # Move to IV chord to support exploration
            feedback_response = "adapt"
            print(f"  🔄 FEEDBACK: Harmonic agent adapting to melodic exploration ({context.melodic_tension:.2f}) → IV")
        # Small chance of a surprising chord
        elif random.random() < self.surprise_rate:
            # Pick a less common chord
            next_degree = random.choice([2, 3, 6])
            is_surprise = True
        else:
            # Use weighted Markov chain
            transitions = self.TRANSITION_WEIGHTS.get(current_degree, {1: 100})
            next_degree = self._weighted_choice(transitions)

        # Get chord symbol
        chord_symbol = self.DEGREE_TO_SYMBOL[next_degree]

        # Duration based on intensity (higher intensity = shorter chords)
        duration = self.chord_duration
        if context.intensity > 0.7:
            duration = self.chord_duration / 2  # Half duration for high intensity

        decision = {
            "degree": next_degree,
            "chord_symbol": chord_symbol,
            "duration": duration,
            "is_surprise": is_surprise,
            "feedback_response": feedback_response,
            "measure": context.current_measure
        }

        return decision

    def act(self, decision: Dict[str, Any], context: MusicalContext) -> List[Dict[str, Any]]:
        """
        Generate MIDI events for the chosen chord and update context.

        Args:
            decision: Decision from decide()
            context: Musical context (will be updated)

        Returns:
            List of MIDI events
        """
        chord_symbol = decision["chord_symbol"]
        duration = decision["duration"]

        # Update context with new chord
        context.current_chord = chord_symbol
        context.current_chord_notes = get_chord_note_names(chord_symbol)

        # Calculate harmonic tension (based on degree)
        degree = decision["degree"]
        tension_map = {1: 0.0, 2: 0.3, 3: 0.4, 4: 0.2, 5: 0.6, 6: 0.3, 7: 0.9}
        context.harmonic_tension = tension_map.get(degree, 0.5)

        # Update current degree for next decision
        self.current_degree = degree

        # Check if instrument has changed and send program_change if needed
        events = []
        current_instrument = context.harmonic_instrument
        if current_instrument != self.last_instrument:
            events.append({
                "type": "program_change",
                "program": current_instrument,
                "time": 0.0,
                "channel": 0
            })
            self.last_instrument = current_instrument

        # Generate MIDI events based on voicing
        if self.voicing == "arpeggio":
            note_events = self._generate_arpeggio(chord_symbol, duration, context)
        else:
            note_events = self._generate_block_chord(chord_symbol, duration, context)

        events.extend(note_events)

        # Advance time
        context.advance_time(duration)

        return events

    def _generate_block_chord(
        self,
        chord_symbol: str,
        duration: float,
        context: MusicalContext
    ) -> List[Dict[str, Any]]:
        """
        Generate MIDI events for a block chord (all notes at once).

        Args:
            chord_symbol: Chord symbol (e.g., "C", "Am")
            duration: Duration in beats
            context: Musical context

        Returns:
            List of MIDI events
        """
        # Get chord notes (MIDI numbers)
        chord_notes = get_chord_notes_from_symbol(chord_symbol, octave=3)

        # Create note on/off events for all notes
        events = []

        # All notes start at time 0 (now)
        for note in chord_notes:
            velocity = int(60 + context.intensity * 40)  # 60-100 based on intensity
            events.append({
                "type": "note_on",
                "note": note,
                "velocity": velocity,
                "time": 0.0,
                "duration": duration,
                "channel": 0
            })
            # Add to context memory
            context.add_note(note, velocity, duration, self.role)

        return events

    def _generate_arpeggio(
        self,
        chord_symbol: str,
        duration: float,
        context: MusicalContext
    ) -> List[Dict[str, Any]]:
        """
        Generate MIDI events for an arpeggiated chord.

        Args:
            chord_symbol: Chord symbol
            duration: Total duration in beats
            context: Musical context

        Returns:
            List of MIDI events
        """
        chord_notes = get_chord_notes_from_symbol(chord_symbol, octave=3)

        events = []
        note_duration = duration / len(chord_notes)

        for i, note in enumerate(chord_notes):
            velocity = int(60 + context.intensity * 40)
            events.append({
                "type": "note_on",
                "note": note,
                "velocity": velocity,
                "time": i * note_duration,
                "duration": note_duration,
                "channel": 0
            })
            context.add_note(note, velocity, note_duration, self.role)

        return events

    def _weighted_choice(self, choices: Dict[int, float]) -> int:
        """
        Make a weighted random choice.

        Args:
            choices: Dictionary of {choice: weight}

        Returns:
            Selected choice
        """
        total = sum(choices.values())
        r = random.uniform(0, total)
        cumulative = 0

        for choice, weight in choices.items():
            cumulative += weight
            if r <= cumulative:
                return choice

        # Fallback (shouldn't reach here)
        return list(choices.keys())[0]

    def reset(self):
        """Reset the agent to initial state."""
        super().reset()
        self.current_degree = 1
