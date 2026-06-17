"""
Test script for the Harmonic Agent.
Generates a 16-bar chord progression and outputs to MIDI.
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

        if event_type == "note_on":
            # Create note_on message
            midi_messages.append({
                "type": "note_on",
                "note": note,
                "velocity": velocity,
                "abs_time": event_time
            })

            # Create note_off message
            midi_messages.append({
                "type": "note_off",
                "note": note,
                "velocity": 0,
                "abs_time": event_time + duration
            })

    # Sort by absolute time
    midi_messages.sort(key=lambda m: m["abs_time"])

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
            time=delta_ticks
        ))

        current_time = abs_time

    return mid


def test_harmonic_agent(num_bars: int = 16, output_file: str = "output/compositions/test_harmonic.mid"):
    """
    Test the harmonic agent by generating a chord progression.

    Args:
        num_bars: Number of bars to generate
        output_file: Output MIDI file path
    """
    print("=" * 60)
    print("HARMONIC AGENT TEST")
    print("=" * 60)

    # Set random seed for reproducibility
    random.seed(42)

    # Create context
    context = MusicalContext()
    context.tempo = 90

    # Create harmonic agent
    agent = HarmonicAgent(objectives={
        "key": "C",
        "surprise_rate": 0.1,  # 10% chance of surprise (matches other tests)
        "chord_duration": 4.0,   # 4 beats per chord (one bar in 4/4)
        "voicing": "block"       # Block chords
    })

    print(f"\nGenerating {num_bars}-bar chord progression...")
    print(f"Key: {context.current_key}")
    print(f"Tempo: {context.tempo} BPM")
    print(f"Time signature: {context.time_signature[0]}/{context.time_signature[1]}")
    print()

    # Generate progression
    all_events = []
    progression = []
    current_absolute_time = 0.0

    for bar in range(num_bars):
        # Agent takes a step
        events = agent.step(context)

        # Convert relative times to absolute times
        for event in events:
            event["time"] = event.get("time", 0) + current_absolute_time

        all_events.extend(events)

        # Update absolute time (assuming 4 beats per chord)
        current_absolute_time += 4.0

        # Track the progression
        chord = context.current_chord
        measure = context.current_measure - 1  # -1 because context advances after act
        tension = context.harmonic_tension
        progression.append(chord)

        # Print progress
        surprise_marker = "(!)" if agent.memory[-1].get("is_surprise") else ""
        tension_bar = "█" * int(tension * 10)
        print(f"Bar {measure:2d}: {chord:6s} {surprise_marker:3s} | Tension: {tension_bar} {tension:.2f}")

    print()
    print("=" * 60)
    print("PROGRESSION SUMMARY")
    print("=" * 60)
    print(f"Chords played: {' → '.join(progression)}")
    print(f"Total events: {len(all_events)}")
    print(f"Final measure: {context.current_measure}")

    # Convert to MIDI
    print(f"\nConverting to MIDI: {output_file}")
    mid = events_to_midi(all_events, tempo=context.tempo)
    mid.save(output_file)
    print(f"✓ MIDI file saved: {output_file}")

    # Analysis
    print()
    print("=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    unique_chords = len(set(progression))
    print(f"Unique chords used: {unique_chords}")
    print(f"Most common chord: {max(set(progression), key=progression.count)} ({progression.count(max(set(progression), key=progression.count))} times)")

    # Count transitions
    transitions = {}
    for i in range(len(progression) - 1):
        trans = f"{progression[i]} → {progression[i+1]}"
        transitions[trans] = transitions.get(trans, 0) + 1

    print(f"\nCommon transitions:")
    for trans, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {trans}: {count} times")

    return output_file


if __name__ == "__main__":
    import sys

    # Allow custom bar count from command line
    num_bars = int(sys.argv[1]) if len(sys.argv) > 1 else 16

    output_file = test_harmonic_agent(num_bars)

    print()
    print("=" * 60)
    print("✓ TEST COMPLETE")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Listen to the MIDI: open {output_file}")
    print(f"2. Render to audio:")
    print(f"   fluidsynth -ni -F output/audio/test_harmonic.wav -r 44100 soundfonts/default.sf2 {output_file}")
    print(f"3. Play audio:")
    print(f"   afplay output/audio/test_harmonic.wav")
