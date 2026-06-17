"""
Musical context shared between all agents.
This represents the current state of the composition.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class MusicalContext:
    """
    Shared musical state that all agents read from and write to.

    Attributes:
        current_key: The current key (e.g., "C", "G", "Am")
        current_chord: The current chord being played (e.g., "C", "Am", "G7")
        current_chord_notes: List of note names in the current chord (e.g., ["C", "E", "G"])
        tempo: Beats per minute (60-120)
        time_signature: Tuple of (numerator, denominator) e.g., (4, 4)
        measure_position: Position within current measure (0.0 to 1.0)
        current_measure: Current measure number (0-indexed)
        intensity: Musical intensity/energy level (0.0 to 1.0)
        recent_notes: Last N notes played by all agents (for memory)
        harmonic_tension: Current harmonic tension (0.0=consonant, 1.0=dissonant)
    """

    # Musical state
    current_key: str = "C"
    current_chord: str = "C"
    current_chord_notes: List[str] = field(default_factory=lambda: ["C", "E", "G"])

    # Timing
    tempo: int = 90  # BPM
    time_signature: Tuple[int, int] = (4, 4)
    measure_position: float = 0.0  # 0.0 to 1.0
    current_measure: int = 0

    # Expression
    intensity: float = 0.5  # 0.0 to 1.0
    harmonic_tension: float = 0.0  # 0.0 to 1.0
    melodic_tension: float = 0.0  # 0.0 to 1.0 (ratio of non-chord tones)

    # Instruments (General MIDI program numbers)
    harmonic_instrument: int = 0  # Default: Acoustic Grand Piano
    melodic_instrument: int = 40  # Default: Violin

    # Memory
    recent_notes: List[dict] = field(default_factory=list)
    max_recent_notes: int = 32  # Keep last 32 notes

    def add_note(self, note: int, velocity: int, duration: float, agent: str):
        """
        Add a note to recent_notes memory.

        Args:
            note: MIDI note number (0-127)
            velocity: MIDI velocity (0-127)
            duration: Duration in beats
            agent: Name of the agent that played this note
        """
        note_info = {
            "note": note,
            "velocity": velocity,
            "duration": duration,
            "agent": agent,
            "measure": self.current_measure,
            "position": self.measure_position
        }
        self.recent_notes.append(note_info)

        # Keep only the most recent notes
        if len(self.recent_notes) > self.max_recent_notes:
            self.recent_notes = self.recent_notes[-self.max_recent_notes:]

    def advance_time(self, beats: float):
        """
        Advance time by a number of beats.

        Args:
            beats: Number of beats to advance
        """
        beats_per_measure = self.time_signature[0]
        self.measure_position += beats / beats_per_measure

        # Handle measure overflow
        while self.measure_position >= 1.0:
            self.measure_position -= 1.0
            self.current_measure += 1

    def reset(self):
        """Reset the context to initial state."""
        self.current_key = "C"
        self.current_chord = "C"
        self.current_chord_notes = ["C", "E", "G"]
        self.tempo = 90
        self.time_signature = (4, 4)
        self.measure_position = 0.0
        self.current_measure = 0
        self.intensity = 0.5
        self.harmonic_tension = 0.0
        self.recent_notes = []

    def __repr__(self) -> str:
        return (
            f"MusicalContext(measure={self.current_measure}, "
            f"position={self.measure_position:.2f}, "
            f"chord={self.current_chord}, "
            f"tempo={self.tempo}, "
            f"intensity={self.intensity:.2f})"
        )
