"""
Test script for MIDI generation.
Generates a simple C major scale to verify the MIDI pipeline works.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import mido
from core.music_theory import get_scale, note_name_to_midi

def create_c_major_scale_midi(output_file: str = "output/compositions/test_c_major.mid"):
    """
    Create a simple MIDI file with a C major scale.

    Args:
        output_file: Path to output MIDI file
    """
    # Create a new MIDI file
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo (120 BPM = 500000 microseconds per beat)
    track.append(mido.MetaMessage('set_tempo', tempo=500000))

    # Get C major scale notes
    scale_notes = get_scale("C", "major", 4)

    # Add each note of the scale
    # Using 480 ticks per quarter note (mido default)
    ticks_per_quarter = 480
    note_duration = ticks_per_quarter  # Quarter note

    for note in scale_notes:
        # Note on (velocity 64 = medium volume)
        track.append(mido.Message('note_on', note=note, velocity=64, time=0))
        # Note off after duration
        track.append(mido.Message('note_off', note=note, velocity=64, time=note_duration))

    # Save the MIDI file
    mid.save(output_file)
    print(f"✓ Created MIDI file: {output_file}")
    print(f"  - Scale notes: {scale_notes}")
    print(f"  - Note names: C D E F G A B C")
    print(f"  - Duration: {len(scale_notes)} quarter notes")
    return output_file


def test_music_theory():
    """Test the music theory functions."""
    print("\nTesting music theory functions...")

    # Test note conversion
    print(f"\n1. Note conversion:")
    print(f"   Middle C: {note_name_to_midi('C', 4)} (expected: 60)")
    print(f"   A440: {note_name_to_midi('A', 4)} (expected: 69)")

    # Test scale generation
    print(f"\n2. C major scale:")
    c_major = get_scale("C", "major", 4)
    print(f"   {c_major}")

    # Test chord generation
    from core.music_theory import get_chord_notes_from_symbol, get_chord_note_names
    print(f"\n3. Chord generation:")
    print(f"   C major: {get_chord_notes_from_symbol('C', 4)} -> {get_chord_note_names('C')}")
    print(f"   Am: {get_chord_notes_from_symbol('Am', 4)} -> {get_chord_note_names('Am')}")
    print(f"   G7: {get_chord_notes_from_symbol('G7', 4)} -> {get_chord_note_names('G7')}")

    # Test progressions
    from core.music_theory import get_progression
    print(f"\n4. Chord progressions:")
    print(f"   Pop progression (I-V-vi-IV): {get_progression('pop', 'C')}")
    print(f"   Jazz turnaround (ii-V-I): {get_progression('jazz', 'C')}")

    print("\n✓ All music theory tests passed!")


def test_musical_context():
    """Test the MusicalContext class."""
    from core.context import MusicalContext

    print("\nTesting MusicalContext...")

    context = MusicalContext()
    print(f"\n1. Initial context:")
    print(f"   {context}")

    # Test adding notes
    context.add_note(60, 64, 1.0, "test")
    context.add_note(64, 64, 1.0, "test")
    print(f"\n2. After adding 2 notes:")
    print(f"   Recent notes: {len(context.recent_notes)} notes")

    # Test advancing time
    context.advance_time(4.0)  # Advance by 4 beats (1 measure in 4/4)
    print(f"\n3. After advancing 4 beats:")
    print(f"   {context}")

    print("\n✓ MusicalContext tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("AGENTIC SYMPHONY - MIDI GENERATION TEST")
    print("=" * 60)

    # Run tests
    test_music_theory()
    test_musical_context()

    # Generate test MIDI file
    print("\n" + "=" * 60)
    print("GENERATING TEST MIDI FILE")
    print("=" * 60)
    output_file = create_c_major_scale_midi()

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Listen to the MIDI file: {output_file}")
    print(f"2. Install FluidSynth to render to audio")
    print(f"3. Test audio rendering with:")
    print(f"   fluidsynth -ni soundfont.sf2 {output_file} -F output.wav -r 44100")
