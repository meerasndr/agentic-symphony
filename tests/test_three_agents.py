"""
Test script for Harmonic + Melodic + Rhythmic agents working together.
Generates a composition with all three agents collaborating.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import random
import mido
import math
from core.context import MusicalContext
from agents.harmonic import HarmonicAgent
from agents.melodic import MelodicAgent
from agents.rhythmic import RhythmicAgent


def events_to_midi(events: list, tempo_changes: list = None) -> mido.MidiFile:
    """
    Convert agent events to a MIDI file with tempo changes.

    Args:
        events: List of event dictionaries from agents
        tempo_changes: List of (time_in_beats, tempo_bpm) tuples

    Returns:
        MIDI file object
    """
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set initial tempo (will be updated with tempo changes)
    initial_tempo = tempo_changes[0][1] if tempo_changes else 90
    microseconds_per_beat = int(60_000_000 / initial_tempo)
    track.append(mido.MetaMessage('set_tempo', tempo=microseconds_per_beat))

    # Convert agent events to MIDI messages with absolute times
    ticks_per_beat = 480
    midi_messages = []

    # Add tempo change messages
    if tempo_changes:
        for time_beats, tempo_bpm in tempo_changes[1:]:  # Skip first (already set)
            midi_messages.append({
                "type": "tempo",
                "tempo": int(60_000_000 / tempo_bpm),
                "abs_time": time_beats
            })

    # Add note events
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

    # Sort by absolute time, then by type (tempo first, then note_off, then note_on)
    def sort_key(m):
        type_order = {"tempo": 0, "note_off": 1, "note_on": 2}
        return (m["abs_time"], type_order.get(m["type"], 3))

    midi_messages.sort(key=sort_key)

    # Convert absolute times to delta times
    current_time = 0.0
    for msg in midi_messages:
        abs_time = msg["abs_time"]
        delta_time = abs_time - current_time
        delta_ticks = int(delta_time * ticks_per_beat)

        # Ensure non-negative delta time
        delta_ticks = max(0, delta_ticks)

        if msg["type"] == "tempo":
            track.append(mido.MetaMessage(
                'set_tempo',
                tempo=msg["tempo"],
                time=delta_ticks
            ))
        else:
            track.append(mido.Message(
                msg["type"],
                note=msg["note"],
                velocity=msg["velocity"],
                channel=msg["channel"],
                time=delta_ticks
            ))

        current_time = abs_time

    return mid


def calculate_intensity_arc(measure: int, total_measures: int) -> float:
    """
    Calculate intensity for a given measure using a dramatic arc.

    Creates an arc: low → build → climax → resolution

    Args:
        measure: Current measure number
        total_measures: Total number of measures

    Returns:
        Intensity value (0.0 to 1.0)
    """
    if total_measures <= 1:
        return 0.5

    # Normalize position (0.0 to 1.0)
    position = measure / (total_measures - 1)

    # Create a bell curve with peak around 0.7
    if position < 0.7:
        # Build up: quadratic growth
        intensity = 0.3 + (position / 0.7) * 0.6
    else:
        # Resolution: quick decay
        decay = (position - 0.7) / 0.3
        intensity = 0.9 - decay * 0.5

    # Add slight randomness
    import random
    intensity += random.uniform(-0.05, 0.05)

    return max(0.2, min(1.0, intensity))


def test_three_agents(
    num_bars: int = 16,
    output_file: str = "output/compositions/test_three_agents.mid"
):
    """
    Test harmonic, melodic, and rhythmic agents working together.

    Args:
        num_bars: Number of bars to generate
        output_file: Output MIDI file path
    """
    print("=" * 70)
    print("HARMONIC + MELODIC + RHYTHMIC AGENTS TEST")
    print("=" * 70)

    # Set random seed for reproducibility
    random.seed(42)

    # Create context
    context = MusicalContext()
    context.tempo = 90
    context.intensity = 0.3  # Start low

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

    rhythmic_agent = RhythmicAgent(objectives={
        "base_tempo": 90,
        "tempo_range": (75, 110),
        "tempo_sensitivity": 0.7,
        "add_percussion": False  # Keep it simple for now
    })

    print(f"\nGenerating {num_bars}-bar composition...")
    print(f"Key: {context.current_key}")
    print(f"Initial tempo: {context.tempo} BPM")
    print(f"Time signature: {context.time_signature[0]}/{context.time_signature[1]}")
    print()
    print("-" * 70)
    print(f"{'Bar':>3} | {'Tempo':>5} | {'Int':>4} | {'Chord':<8} | {'Tension':<15}")
    print("-" * 70)

    all_events = []
    tempo_changes = [(0, context.tempo)]  # Track tempo changes
    current_absolute_time = 0.0

    for bar in range(num_bars):
        # Update intensity based on dramatic arc
        context.intensity = calculate_intensity_arc(bar, num_bars)

        measure_num = context.current_measure

        # 1. Harmonic agent decides chord
        harmonic_events = harmonic_agent.step(context)

        # 2. Reset context time for melodic agent (they play simultaneously)
        saved_measure = context.current_measure
        saved_position = context.measure_position
        context.current_measure = measure_num
        context.measure_position = 0.0

        # 3. Melodic agent creates melody over the chord
        melodic_events = melodic_agent.step(context)

        # Restore context
        context.current_measure = measure_num
        context.measure_position = 0.0

        # 4. Rhythmic agent adjusts tempo
        rhythmic_events = rhythmic_agent.step(context)

        # Record tempo change
        if bar > 0:  # Skip first bar (already have initial tempo)
            tempo_changes.append((current_absolute_time, context.tempo))

        # Convert relative times to absolute times
        for event in harmonic_events:
            event["time"] = event.get("time", 0) + current_absolute_time

        for event in melodic_events:
            event["time"] = event.get("time", 0) + current_absolute_time

        for event in rhythmic_events:
            event["time"] = event.get("time", 0) + current_absolute_time

        all_events.extend(harmonic_events)
        all_events.extend(melodic_events)
        all_events.extend(rhythmic_events)

        # Restore context to where harmonic agent left it
        context.current_measure = saved_measure
        context.measure_position = saved_position

        # Display progress
        chord = context.current_chord
        tension = context.harmonic_tension
        tempo = context.tempo
        intensity = context.intensity

        tension_bar = "█" * int(tension * 10)
        print(f"{measure_num:3d} | {tempo:5d} | {intensity:4.2f} | {chord:<8} | {tension_bar:<10} {tension:.2f}")

        # Update absolute time
        current_absolute_time += 4.0

    print("-" * 70)
    print()
    print("=" * 70)
    print("COMPOSITION SUMMARY")
    print("=" * 70)

    # Tempo analysis
    tempos = [t[1] for t in tempo_changes]
    print(f"Tempo evolution:")
    print(f"  - Start: {tempos[0]} BPM")
    print(f"  - End: {tempos[-1]} BPM")
    print(f"  - Min: {min(tempos)} BPM")
    print(f"  - Max: {max(tempos)} BPM")
    print(f"  - Average: {sum(tempos) / len(tempos):.1f} BPM")

    print(f"\nTotal MIDI events: {len(all_events)}")
    print(f"  - Harmonic events: {len([e for e in all_events if e.get('channel') == 0])}")
    print(f"  - Melodic events: {len([e for e in all_events if e.get('channel') == 1])}")
    print(f"  - Rhythmic events: {len([e for e in all_events if e.get('channel') == 9])}")

    # Convert to MIDI
    print(f"\nConverting to MIDI: {output_file}")
    mid = events_to_midi(all_events, tempo_changes)
    mid.save(output_file)
    print(f"✓ MIDI file saved: {output_file}")

    return output_file


if __name__ == "__main__":
    import sys

    # Allow custom bar count from command line
    num_bars = int(sys.argv[1]) if len(sys.argv) > 1 else 16

    output_file = test_three_agents(num_bars)

    print()
    print("=" * 70)
    print("✓ TEST COMPLETE")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"1. Render to audio:")
    print(f"   python3 render_audio.py")
    print(f"2. Play audio:")
    print(f"   afplay output/audio/test_three_agents.wav")
