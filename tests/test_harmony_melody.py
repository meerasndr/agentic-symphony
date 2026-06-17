"""
Test script for Harmonic + Melodic agents working together.
Generates a composition with both harmony and melody.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import random
import mido
from core.context import MusicalContext
from agents.harmonic import HarmonicAgent
from agents.melodic import MelodicAgent


def events_to_midi(events: list, tempo: int = 90) -> mido.MidiFile:
    """
    Convert agent events to a MIDI file.

    Args:
        events: List of event dictionaries from agents
        tempo: Tempo in BPM

    Returns:
        MIDI file object
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    microseconds_per_beat = int(60_000_000 / tempo)
    track.append(mido.MetaMessage('set_tempo', tempo=microseconds_per_beat))

    # Convert agent events to MIDI messages with absolute times
    ticks_per_beat = 480
    midi_messages = []

    for event in events:
        event_type = event.get("type")
        event_time = event.get("time", 0)
        note = event.get("note")
        velocity = event.get("velocity", 64)
        duration = event.get("duration", 1.0)
        channel = event.get("channel", 0)

        if event_type == "note_on":
            # Create note_on message
            midi_messages.append({
                "type": "note_on",
                "note": note,
                "velocity": velocity,
                "channel": channel,
                "abs_time": event_time
            })

            # Create note_off message
            midi_messages.append({
                "type": "note_off",
                "note": note,
                "velocity": 0,
                "channel": channel,
                "abs_time": event_time + duration
            })

    # Sort by absolute time, then by type (note_off before note_on for same time)
    midi_messages.sort(key=lambda m: (m["abs_time"], 0 if m["type"] == "note_off" else 1))

    # Convert absolute times to delta times
    current_time = 0.0
    for msg in midi_messages:
        abs_time = msg["abs_time"]
        delta_time = abs_time - current_time
        delta_ticks = int(delta_time * ticks_per_beat)

        # Ensure non-negative delta time
        delta_ticks = max(0, delta_ticks)

        track.append(mido.Message(
            msg["type"],
            note=msg["note"],
            velocity=msg["velocity"],
            channel=msg["channel"],
            time=delta_ticks
        ))

        current_time = abs_time

    return mid


def test_harmony_and_melody(
    num_bars: int = 16,
    output_file: str = "output/compositions/test_harmony_melody.mid"
):
    """
    Test harmonic and melodic agents working together.

    Args:
        num_bars: Number of bars to generate
        output_file: Output MIDI file path
    """
    print("=" * 70)
    print("HARMONIC + MELODIC AGENTS TEST")
    print("=" * 70)

    # Set random seed for reproducibility
    random.seed(42)

    # Create context
    context = MusicalContext()
    context.tempo = 90  # Match other tests
    context.intensity = 0.3  # Match other tests

    # Create agents
    harmonic_agent = HarmonicAgent(objectives={
        "key": "C",
        "surprise_rate": 0.1,
        "chord_duration": 4.0,
        "voicing": "block"
    })

    melodic_agent = MelodicAgent(objectives={
        "octave": 5,
        "motif_length": 4,
        "variation_rate": 0.6,
        "chord_tone_bias": 0.75
    })

    print(f"\nGenerating {num_bars}-bar composition...")
    print(f"Key: {context.current_key}")
    print(f"Tempo: {context.tempo} BPM")
    print(f"Time signature: {context.time_signature[0]}/{context.time_signature[1]}")
    print()
    print("-" * 70)
    print(f"{'Bar':>3} | {'Chord':<8} | {'Tension':<15} | {'Melody':<30}")
    print("-" * 70)

    all_events = []
    progression = []
    current_absolute_time = 0.0

    for bar in range(num_bars):
        # Save the measure number before agents act
        measure_num = context.current_measure

        # 1. Harmonic agent decides chord
        harmonic_events = harmonic_agent.step(context)

        # Reset context time for melodic agent (they play simultaneously)
        saved_measure = context.current_measure
        saved_position = context.measure_position
        context.current_measure = measure_num
        context.measure_position = 0.0

        # 2. Melodic agent creates melody over the chord
        melodic_events = melodic_agent.step(context)

        # Restore context to where harmonic agent left it
        context.current_measure = saved_measure
        context.measure_position = saved_position

        # Convert relative times to absolute times
        for event in harmonic_events:
            event["time"] = event.get("time", 0) + current_absolute_time

        for event in melodic_events:
            event["time"] = event.get("time", 0) + current_absolute_time

        all_events.extend(harmonic_events)
        all_events.extend(melodic_events)

        # Track progression
        chord = context.current_chord
        tension = context.harmonic_tension
        progression.append(chord)

        # Get melody info from last decision
        melody_info = ""
        if melodic_agent.memory:
            last_decision = melodic_agent.memory[-1]
            var_type = last_decision.get("variation_type", "")
            is_new = last_decision.get("is_new_motif", False)
            if is_new:
                melody_info = "NEW MOTIF"
            else:
                melody_info = f"Variation: {var_type}"

        # Display progress
        tension_bar = "█" * int(tension * 10)
        print(f"{measure_num:3d} | {chord:<8} | {tension_bar:<10} {tension:.2f} | {melody_info:<30}")

        # Update absolute time
        current_absolute_time += 4.0

    print("-" * 70)
    print()
    print("=" * 70)
    print("COMPOSITION SUMMARY")
    print("=" * 70)
    print(f"Chord progression: {' → '.join(progression)}")
    print(f"Total MIDI events: {len(all_events)}")
    print(f"  - Harmonic events: {len([e for e in all_events if e.get('channel') == 0])}")
    print(f"  - Melodic events: {len([e for e in all_events if e.get('channel') == 1])}")
    print(f"Final measure: {context.current_measure}")

    # Convert to MIDI
    print(f"\nConverting to MIDI: {output_file}")
    mid = events_to_midi(all_events, tempo=context.tempo)
    mid.save(output_file)
    print(f"✓ MIDI file saved: {output_file}")

    # Analysis
    print()
    print("=" * 70)
    print("MUSICAL ANALYSIS")
    print("=" * 70)

    unique_chords = len(set(progression))
    print(f"Unique chords: {unique_chords}")
    print(f"Most common chord: {max(set(progression), key=progression.count)}")

    # Melodic analysis
    new_motifs = sum(1 for d in melodic_agent.memory if d.get("is_new_motif"))
    variations = sum(1 for d in melodic_agent.memory if not d.get("is_new_motif"))
    print(f"\nMelodic development:")
    print(f"  - New motifs: {new_motifs}")
    print(f"  - Variations: {variations}")

    # Count variation types
    var_types = {}
    for d in melodic_agent.memory:
        if not d.get("is_new_motif"):
            vt = d.get("variation_type", "unknown")
            var_types[vt] = var_types.get(vt, 0) + 1

    if var_types:
        print(f"  - Variation techniques used:")
        for vt, count in sorted(var_types.items(), key=lambda x: x[1], reverse=True):
            print(f"      {vt}: {count}x")

    return output_file


if __name__ == "__main__":
    import sys

    # Allow custom bar count from command line
    num_bars = int(sys.argv[1]) if len(sys.argv) > 1 else 16

    output_file = test_harmony_and_melody(num_bars)

    print()
    print("=" * 70)
    print("✓ TEST COMPLETE")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"1. Listen to MIDI: open {output_file}")
    print(f"2. Render to audio:")
    print(f"   fluidsynth -ni -F output/audio/test_harmony_melody.wav -r 44100 \\")
    print(f"      soundfonts/default.sf2 {output_file}")
    print(f"3. Play audio:")
    print(f"   afplay output/audio/test_harmony_melody.wav")
