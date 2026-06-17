"""
Music theory helper functions for the Agentic Symphony system.
Provides utilities for scales, chords, progressions, and MIDI note conversion.
"""

from typing import List, Dict, Tuple

# MIDI note constants
MIDDLE_C = 60
OCTAVE = 12

# Note names to chromatic offsets from C
NOTE_TO_OFFSET = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11
}

# Chromatic offsets to note names (using sharps)
OFFSET_TO_NOTE = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
}

# Major scale intervals (in semitones from root)
MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]  # W-W-H-W-W-W-H
MINOR_SCALE_INTERVALS = [0, 2, 3, 5, 7, 8, 10]  # W-H-W-W-H-W-W

# Chord intervals (in semitones from root)
CHORD_INTERVALS = {
    "major": [0, 4, 7],           # Root, major third, perfect fifth
    "minor": [0, 3, 7],           # Root, minor third, perfect fifth
    "dim": [0, 3, 6],             # Diminished
    "aug": [0, 4, 8],             # Augmented
    "7": [0, 4, 7, 10],           # Dominant 7th
    "maj7": [0, 4, 7, 11],        # Major 7th
    "min7": [0, 3, 7, 10],        # Minor 7th
}

# Roman numeral to scale degree mapping (1-indexed)
ROMAN_TO_DEGREE = {
    "I": 1, "ii": 2, "iii": 3, "IV": 4,
    "V": 5, "vi": 6, "vii": 7, "vii°": 7
}

# Scale degrees in major key and their qualities
MAJOR_KEY_CHORDS = {
    1: "major",   # I
    2: "minor",   # ii
    3: "minor",   # iii
    4: "major",   # IV
    5: "major",   # V
    6: "minor",   # vi
    7: "dim",     # vii°
}

# Common chord progressions (as scale degrees)
PROGRESSIONS = {
    "pop": [1, 5, 6, 4],              # I-V-vi-IV (very common)
    "jazz": [2, 5, 1],                 # ii-V-I (turnaround)
    "classical": [1, 4, 5, 1],         # I-IV-V-I (basic cadence)
    "emotional": [1, 6, 4, 5],         # I-vi-IV-V (50s progression)
    "blues": [1, 1, 1, 1, 4, 4, 1, 1, 5, 4, 1, 1],  # 12-bar blues
}


def note_name_to_midi(note_name: str, octave: int = 4) -> int:
    """
    Convert a note name and octave to MIDI note number.

    Args:
        note_name: Note name (e.g., "C", "F#", "Bb")
        octave: Octave number (4 = middle C octave)

    Returns:
        MIDI note number (0-127)

    Example:
        >>> note_name_to_midi("C", 4)
        60  # Middle C
    """
    if note_name not in NOTE_TO_OFFSET:
        raise ValueError(f"Invalid note name: {note_name}")

    offset = NOTE_TO_OFFSET[note_name]
    midi_note = (octave + 1) * OCTAVE + offset
    return max(0, min(127, midi_note))


def midi_to_note_name(midi_note: int) -> Tuple[str, int]:
    """
    Convert MIDI note number to note name and octave.

    Args:
        midi_note: MIDI note number (0-127)

    Returns:
        Tuple of (note_name, octave)

    Example:
        >>> midi_to_note_name(60)
        ("C", 4)
    """
    octave = (midi_note // OCTAVE) - 1
    offset = midi_note % OCTAVE
    note_name = OFFSET_TO_NOTE[offset]
    return note_name, octave


def get_scale(root: str, scale_type: str = "major", octave: int = 4) -> List[int]:
    """
    Get MIDI note numbers for a scale.

    Args:
        root: Root note name (e.g., "C", "G")
        scale_type: "major" or "minor"
        octave: Starting octave

    Returns:
        List of MIDI note numbers for the scale

    Example:
        >>> get_scale("C", "major", 4)
        [60, 62, 64, 65, 67, 69, 71, 72]  # C major scale
    """
    root_midi = note_name_to_midi(root, octave)
    intervals = MAJOR_SCALE_INTERVALS if scale_type == "major" else MINOR_SCALE_INTERVALS
    return [root_midi + interval for interval in intervals] + [root_midi + 12]


def get_chord_notes(root: str, chord_type: str = "major", octave: int = 4) -> List[int]:
    """
    Get MIDI note numbers for a chord.

    Args:
        root: Root note name (e.g., "C", "G")
        chord_type: Chord quality ("major", "minor", "7", etc.)
        octave: Root note octave

    Returns:
        List of MIDI note numbers for the chord

    Example:
        >>> get_chord_notes("C", "major", 4)
        [60, 64, 67]  # C major triad (C-E-G)
    """
    if chord_type not in CHORD_INTERVALS:
        chord_type = "major"  # Default to major

    root_midi = note_name_to_midi(root, octave)
    intervals = CHORD_INTERVALS[chord_type]
    return [root_midi + interval for interval in intervals]


def parse_chord_symbol(chord_symbol: str) -> Tuple[str, str]:
    """
    Parse a chord symbol into root and quality.

    Args:
        chord_symbol: Chord symbol (e.g., "C", "Am", "G7", "Dm7")

    Returns:
        Tuple of (root_note, chord_type)

    Example:
        >>> parse_chord_symbol("Am")
        ("A", "minor")
        >>> parse_chord_symbol("G7")
        ("G", "7")
    """
    # Simple parsing logic
    if len(chord_symbol) == 1:
        return chord_symbol, "major"

    root = chord_symbol[0]
    if len(chord_symbol) > 1 and chord_symbol[1] in ["#", "b"]:
        root = chord_symbol[:2]
        suffix = chord_symbol[2:]
    else:
        suffix = chord_symbol[1:]

    # Map common suffixes to chord types
    suffix_map = {
        "m": "minor",
        "min": "minor",
        "7": "7",
        "maj7": "maj7",
        "m7": "min7",
        "dim": "dim",
        "°": "dim",
        "aug": "aug",
        "+": "aug",
    }

    chord_type = suffix_map.get(suffix, "major")
    return root, chord_type


def roman_to_chord(roman: str, key: str = "C") -> str:
    """
    Convert a Roman numeral to a chord symbol in a given key.

    Args:
        roman: Roman numeral (e.g., "I", "ii", "V")
        key: Key signature (e.g., "C", "G")

    Returns:
        Chord symbol (e.g., "C", "Dm", "G")

    Example:
        >>> roman_to_chord("I", "C")
        "C"
        >>> roman_to_chord("ii", "C")
        "Dm"
    """
    if roman not in ROMAN_TO_DEGREE:
        raise ValueError(f"Invalid Roman numeral: {roman}")

    degree = ROMAN_TO_DEGREE[roman]
    scale = get_scale(key, "major", 4)
    root_midi = scale[degree - 1]
    root_name, _ = midi_to_note_name(root_midi)

    chord_quality = MAJOR_KEY_CHORDS[degree]
    suffix = "" if chord_quality == "major" else "m" if chord_quality == "minor" else "dim"

    return root_name + suffix


def get_progression(progression_name: str, key: str = "C") -> List[str]:
    """
    Get a chord progression as chord symbols in a given key.

    Args:
        progression_name: Name of progression ("pop", "jazz", "classical", etc.)
        key: Key signature

    Returns:
        List of chord symbols

    Example:
        >>> get_progression("pop", "C")
        ["C", "G", "Am", "F"]
    """
    if progression_name not in PROGRESSIONS:
        raise ValueError(f"Unknown progression: {progression_name}")

    scale = get_scale(key, "major", 4)
    degrees = PROGRESSIONS[progression_name]
    chords = []

    for degree in degrees:
        root_midi = scale[degree - 1]
        root_name, _ = midi_to_note_name(root_midi)
        chord_quality = MAJOR_KEY_CHORDS[degree]
        suffix = "" if chord_quality == "major" else "m" if chord_quality == "minor" else "dim"
        chords.append(root_name + suffix)

    return chords


def get_chord_notes_from_symbol(chord_symbol: str, octave: int = 4) -> List[int]:
    """
    Get MIDI notes for a chord given its symbol.

    Args:
        chord_symbol: Chord symbol (e.g., "C", "Am", "G7")
        octave: Root octave

    Returns:
        List of MIDI note numbers

    Example:
        >>> get_chord_notes_from_symbol("Am", 4)
        [69, 72, 76]  # A-C-E
    """
    root, chord_type = parse_chord_symbol(chord_symbol)
    return get_chord_notes(root, chord_type, octave)


def get_chord_note_names(chord_symbol: str) -> List[str]:
    """
    Get note names for a chord.

    Args:
        chord_symbol: Chord symbol (e.g., "C", "Am", "G7")

    Returns:
        List of note names

    Example:
        >>> get_chord_note_names("C")
        ["C", "E", "G"]
    """
    root, chord_type = parse_chord_symbol(chord_symbol)
    midi_notes = get_chord_notes(root, chord_type, 4)
    return [midi_to_note_name(note)[0] for note in midi_notes]
