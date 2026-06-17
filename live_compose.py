"""
Live Terminal UI for Agentic Symphony Composition

Creates a real-time terminal visualization showing agent decisions
as the composition is being generated.
"""

import mido
import random
import argparse
import json
import time
import subprocess
from pathlib import Path
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.console import Group, Console
from rich.text import Text
from rich import box
from rich.progress import Progress, BarColumn, TextColumn

from core.context import MusicalContext
from agents.harmonic import HarmonicAgent
from agents.melodic import MelodicAgent
from agents.rhythmic import RhythmicAgent
from agents.textural import TexturalAgent, apply_textural_modifications


def load_preset(preset_name: str) -> dict:
    """Load configuration preset from JSON file."""
    presets_file = Path("config/presets.json")
    if not presets_file.exists():
        return {}

    with open(presets_file) as f:
        data = json.load(f)
        return data.get("presets", {}).get(preset_name, {})


def events_to_midi(events: list, tempo_changes: list = None) -> mido.MidiFile:
    """Convert agent events to a MIDI file with tempo changes."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    initial_tempo = tempo_changes[0][1] if tempo_changes else 90
    microseconds_per_beat = int(60_000_000 / initial_tempo)
    track.append(mido.MetaMessage('set_tempo', tempo=microseconds_per_beat))

    ticks_per_beat = 480
    midi_messages = []

    if tempo_changes:
        for time_beats, tempo_bpm in tempo_changes[1:]:
            midi_messages.append({
                "type": "tempo",
                "tempo": int(60_000_000 / tempo_bpm),
                "abs_time": time_beats
            })

    for event in events:
        event_type = event.get("type")
        event_time = event.get("time", 0)
        note = event.get("note")
        velocity = event.get("velocity", 64)
        duration = event.get("duration", 1.0)
        channel = event.get("channel", 0)

        if event_type == "program_change":
            midi_messages.append({
                "type": "program_change",
                "program": event.get("program", 0),
                "channel": channel,
                "abs_time": event_time
            })
        elif event_type == "note_on":
            midi_messages.append({
                "type": "note_on",
                "note": note,
                "velocity": velocity,
                "channel": channel,
                "abs_time": event_time
            })
            midi_messages.append({
                "type": "note_off",
                "note": note,
                "velocity": 0,
                "channel": channel,
                "abs_time": event_time + duration
            })

    def sort_key(m):
        type_order = {"tempo": 0, "program_change": 1, "note_off": 2, "note_on": 3}
        return (m["abs_time"], type_order.get(m["type"], 4))

    midi_messages.sort(key=sort_key)

    current_time = 0.0
    for msg in midi_messages:
        abs_time = msg["abs_time"]
        delta_time = abs_time - current_time
        delta_ticks = int(delta_time * ticks_per_beat)
        delta_ticks = max(0, delta_ticks)

        if msg["type"] == "tempo":
            track.append(mido.MetaMessage('set_tempo', tempo=msg["tempo"], time=delta_ticks))
        elif msg["type"] == "program_change":
            track.append(mido.Message('program_change', program=msg["program"],
                                     channel=msg["channel"], time=delta_ticks))
        else:
            track.append(mido.Message(msg["type"], note=msg["note"],
                                     velocity=msg["velocity"], channel=msg["channel"],
                                     time=delta_ticks))

        current_time = abs_time

    return mid


def calculate_intensity_arc(measure: int, total_measures: int) -> float:
    """Calculate intensity for a given measure using a dramatic arc."""
    if total_measures <= 1:
        return 0.5

    position = measure / (total_measures - 1)

    if position < 0.7:
        intensity = 0.3 + (position / 0.7) * 0.6
    else:
        decay = (position - 0.7) / 0.3
        intensity = 0.9 - decay * 0.5

    intensity += random.uniform(-0.05, 0.05)
    return max(0.2, min(1.0, intensity))


def create_intensity_graph(intensity_history: list, current_bar: int, total_bars: int) -> str:
    """Create ASCII art graph of intensity arc."""
    width = min(50, total_bars * 2)
    height = 8

    # Create empty graph
    graph = [[" " for _ in range(width)] for _ in range(height)]

    # Plot intensity values
    for i, intensity in enumerate(intensity_history):
        x = int((i / (total_bars - 1)) * (width - 1)) if total_bars > 1 else 0
        y = height - 1 - int(intensity * (height - 1))
        if 0 <= x < width and 0 <= y < height:
            graph[y][x] = "●"

    # Convert to string
    lines = []
    levels = ["1.0", "0.8", "0.6", "0.4", "0.2", "0.0"]
    for i, row in enumerate(graph):
        if i < len(levels):
            level = levels[i]
            lines.append(f"{level} │{''.join(row)}")
        else:
            lines.append(f"     │{''.join(row)}")

    lines.append(f"     └{'─' * width}")

    return "\n".join(lines)


def create_voice_density_bar(density: int, max_density: int = 4) -> str:
    """Create visual bar for voice density."""
    filled = "▓" * density
    empty = "░" * (max_density - density)
    return f"[{filled}{empty}]"


def create_piano_roll(context: MusicalContext, window_beats: int = 8) -> str:
    """
    Create a mini piano roll visualization from recent notes.

    Args:
        context: Musical context with recent_notes
        window_beats: How many beats to show (width of display)

    Returns:
        Formatted piano roll string
    """
    from core.music_theory import midi_to_note_name

    # Get recent notes (last window_beats worth)
    recent = context.recent_notes[-20:] if context.recent_notes else []

    if not recent:
        return "  [No notes yet]"

    # Find note range for vertical axis
    midi_notes = [n["note"] for n in recent]
    min_note = max(min(midi_notes) - 1, 48)  # C3 minimum
    max_note = min(max(midi_notes) + 1, 84)  # C6 maximum

    # Limit to one octave + a bit for display
    if max_note - min_note > 13:
        # Center around most recent note
        center = recent[-1]["note"]
        min_note = max(center - 6, 48)
        max_note = min(center + 6, 84)

    # Create grid
    width = 40  # Characters wide
    lines = []

    # Calculate time window (last 4 beats)
    if recent:
        latest_time = context.current_measure * 4 + context.measure_position
        earliest_time = max(0, latest_time - 4.0)
    else:
        earliest_time = 0
        latest_time = 4.0

    # Build piano roll from bottom (low notes) to top (high notes)
    for midi_note in range(max_note, min_note - 1, -1):
        note_name_tuple = midi_to_note_name(midi_note)
        note_name = f"{note_name_tuple[0]}{note_name_tuple[1]}"  # e.g. "C4"

        # Create timeline for this note
        timeline = [' '] * width

        # Plot notes
        for note_event in recent:
            if note_event["note"] == midi_note:
                # Calculate position in timeline
                note_time = note_event["measure"] * 4 + note_event.get("position", 0)
                note_duration = note_event.get("duration", 0.5)

                # Skip if outside window
                if note_time < earliest_time or note_time > latest_time:
                    continue

                # Map time to x position
                time_range = latest_time - earliest_time
                if time_range > 0:
                    x_start = int(((note_time - earliest_time) / time_range) * width)
                    x_end = int(((note_time + note_duration - earliest_time) / time_range) * width)

                    # Draw note block (color by agent)
                    agent = note_event.get("agent", "")
                    if "melodic" in agent.lower():
                        char = "▓"  # Melodic notes
                    else:
                        char = "█"  # Harmonic notes

                    for x in range(max(0, x_start), min(width, x_end)):
                        timeline[x] = char

        # Format line
        line_str = ''.join(timeline)

        # Color code by agent (if any notes on this line)
        if '▓' in line_str:
            # Melodic notes - magenta
            line_str = f"[magenta]{line_str}[/]"
        elif '█' in line_str:
            # Harmonic notes - cyan
            line_str = f"[cyan]{line_str}[/]"
        else:
            # Empty line - dim
            line_str = f"[dim]{line_str}[/]"

        lines.append(f"{note_name:>4} │{line_str}")

    return "\n".join(lines)


def make_display(
    bar: int,
    total_bars: int,
    context: MusicalContext,
    harmonic_decision: dict,
    melodic_decision: dict,
    rhythmic_decision: dict,
    textural_decision: dict,
    intensity_history: list,
    llm_stats: dict,
    is_pause: bool = False
) -> Layout:
    """Create the rich display layout."""

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=5),
        Layout(name="agents", size=20),
        Layout(name="piano_roll", size=15),  # NEW: Piano roll section
        Layout(name="graph", size=12),
        Layout(name="stats", size=5)
    )

    # Header with progress bar
    progress_bar = '█' * bar + '░' * (total_bars - bar)
    progress_text = f"{progress_bar} {bar}/{total_bars} measures"

    header_content = Group(
        Text("🎵 AGENTIC SYMPHONY - LIVE GENERATION 🎵", style="bold yellow", justify="center"),
        Text(progress_text, style="bold cyan", justify="center")
    )

    header = Panel(
        header_content,
        box=box.DOUBLE,
        style="bold blue"
    )
    layout["header"].update(header)

    # Agents section
    agents_layout = Layout()
    agents_layout.split_column(
        Layout(name="harmonic", size=5),
        Layout(name="melodic", size=5),
        Layout(name="rhythmic", size=5),
        Layout(name="textural", size=5)
    )

    # Harmonic Agent Panel
    if is_pause:
        harmonic_content = Text("  [PAUSE - No chord progression]", style="dim")
    else:
        chord = harmonic_decision.get("chord_symbol", context.current_chord if context.current_chord else "?")
        tension = context.harmonic_tension
        surprise = harmonic_decision.get("is_surprise", False)
        feedback_response = harmonic_decision.get("feedback_response")
        surprise_text = " ⚡" if surprise else ""
        tension_bar = "●" * int(tension * 5) + "○" * (5 - int(tension * 5))

        # Build content with optional feedback indicator
        content_lines = [
            f"  Current: [bold cyan]{chord}[/]{surprise_text}",
            f"  Tension: {tension_bar} ({tension:.2f})"
        ]

        # Add feedback indicator if responding to melodic tension
        if feedback_response == "resolve":
            content_lines.append(f"  [bold yellow]🔄 Resolving melodic tension[/]")
        elif feedback_response == "adapt":
            content_lines.append(f"  [bold green]🔄 Adapting to melody[/]")

        harmonic_content = Text.from_markup("\n".join(content_lines))

    agents_layout["harmonic"].update(Panel(
        harmonic_content,
        title="[bold]🎹 HARMONIC AGENT[/]",
        border_style="cyan",
        box=box.ROUNDED
    ))

    # Melodic Agent Panel
    if is_pause:
        melodic_content = Text("  [PAUSE - No melody]", style="dim")
    else:
        action = melodic_decision.get("action", "?")
        source = melodic_decision.get("source", "rule")
        reasoning = melodic_decision.get("reasoning", "")
        melodic_tension = context.melodic_tension

        if source == "llm":
            source_icon = "🤖"
            source_color = "blue"
        else:
            source_icon = "📏"
            source_color = "green"

        # Format reasoning text (shorter to make room for tension)
        reasoning_text = f"{reasoning[:40]}..." if len(reasoning) > 40 else reasoning

        # Build content with melodic tension indicator
        content_lines = [
            f"  Action: [{source_color}]{source_icon} {action}[/{source_color}]",
            f"  {reasoning_text}"
        ]

        # Add melodic tension indicator if significant
        if melodic_tension > 0.4:
            tension_color = "yellow" if melodic_tension > 0.6 else "dim"
            content_lines.append(f"  [{ tension_color}]Melodic tension: {melodic_tension:.2f}[/]")

        melodic_content = Text.from_markup("\n".join(content_lines))

    agents_layout["melodic"].update(Panel(
        melodic_content,
        title="[bold]🎵 MELODIC AGENT[/]",
        border_style="green" if melodic_decision.get("source") == "rule" else "blue",
        box=box.ROUNDED
    ))

    # Rhythmic Agent Panel
    tempo = rhythmic_decision.get("tempo", context.tempo)
    tempo_change = rhythmic_decision.get("change", 0)
    arrow = "↑" if tempo_change > 0 else ("↓" if tempo_change < 0 else "→")
    intensity = context.intensity
    intensity_bar = "●" * int(intensity * 10) + "○" * (10 - int(intensity * 10))

    rhythmic_content = Text.from_markup(
        f"  Tempo: [bold]{tempo} BPM[/] {arrow}\n"
        f"  Intensity: {intensity_bar} ({intensity:.2f})"
    )

    agents_layout["rhythmic"].update(Panel(
        rhythmic_content,
        title="[bold]⏱️  RHYTHMIC AGENT[/]",
        border_style="yellow",
        box=box.ROUNDED
    ))

    # Textural Agent Panel
    if is_pause:
        textural_content = Text("  [STRATEGIC PAUSE]", style="bold red")
    else:
        dynamic = textural_decision.get("dynamic_marking", "mf")
        voices = textural_decision.get("voice_density", 2)
        voice_bar = create_voice_density_bar(voices)
        instruments = textural_decision.get("instruments", {})
        inst_text = ", ".join([f"{k}: {v}" for k, v in list(instruments.items())[:2]]) if instruments else "Piano"

        textural_content = Text.from_markup(
            f"  Dynamic: [bold]{dynamic}[/]   Voices: {voice_bar} ({voices})\n"
            f"  Instruments: {inst_text[:40]}..."
        )

    agents_layout["textural"].update(Panel(
        textural_content,
        title="[bold]🎨 TEXTURAL AGENT[/]",
        border_style="magenta",
        box=box.ROUNDED
    ))

    layout["agents"].update(agents_layout)

    # Piano Roll section
    piano_roll_text = create_piano_roll(context)
    piano_roll_panel = Panel(
        Text.from_markup(piano_roll_text),
        title="[bold]🎹 PIANO ROLL[/] ([cyan]█[/] Harmony  [magenta]▓[/] Melody)",
        border_style="yellow",
        box=box.ROUNDED
    )
    layout["piano_roll"].update(piano_roll_panel)

    # Intensity graph
    graph_text = create_intensity_graph(intensity_history, bar, total_bars)
    graph_panel = Panel(
        graph_text,
        title="[bold]INTENSITY ARC[/]",
        border_style="red",
        box=box.ROUNDED
    )
    layout["graph"].update(graph_panel)

    # Statistics
    llm_calls = llm_stats.get("calls", 0)
    llm_success = llm_stats.get("success", 0)
    llm_fail = llm_stats.get("fail", 0)
    llm_pct = (llm_success / llm_calls * 100) if llm_calls > 0 else 0

    stats_table = Table(show_header=False, box=None, padding=(0, 1))
    stats_table.add_column(style="cyan")
    stats_table.add_column(style="white")

    stats_table.add_row("LLM Calls:", f"[bold]{llm_calls}[/] ({llm_success} ✓, {llm_fail} ✗) - {llm_pct:.0f}% success")
    stats_table.add_row("Measures:", f"[bold]{bar}/{total_bars}[/]")
    stats_table.add_row("Current Key:", f"[bold]{context.current_key}[/]")

    layout["stats"].update(Panel(
        stats_table,
        title="[bold]📊 STATISTICS[/]",
        border_style="white",
        box=box.ROUNDED
    ))

    return layout


def live_compose(
    num_bars: int = 16,
    preset_name: str = "default",
    output_file: str = None,
    seed: int = None
):
    """
    Generate composition with live terminal visualization.

    Args:
        num_bars: Number of bars to generate
        preset_name: Configuration preset name
        output_file: Output MIDI file path
        seed: Random seed for reproducibility
    """

    if seed is not None:
        random.seed(seed)

    # Load preset configuration
    config = load_preset(preset_name)

    # Get composition settings
    comp_settings = config.get("composition", {})
    num_bars = comp_settings.get("num_bars", num_bars)
    initial_tempo = comp_settings.get("tempo", 90)

    # Get agent settings
    agent_settings = config.get("agents", {})
    llm_settings = config.get("llm", {})

    # Generate output filename if not provided
    if output_file is None:
        output_file = f"output/compositions/live_{preset_name}_{num_bars}bars.mid"
        if seed is not None:
            output_file = f"output/compositions/live_{preset_name}_{num_bars}bars_seed{seed}.mid"

    # Create context
    context = MusicalContext()
    context.tempo = initial_tempo
    context.intensity = 0.3
    context.dynamic_multiplier = 0.7
    context.voice_density = 2
    context.suggest_pause = False

    # Create agents with preset configurations
    textural_config = agent_settings.get("textural", {})
    textural_agent = TexturalAgent(objectives={
        "dynamic_range": textural_config.get("dynamic_range", (0.5, 1.2)),
        "pause_probability": textural_config.get("pause_probability", 0.08),
        "voice_density_control": True,
        "crescendo_rate": textural_config.get("crescendo_rate", 0.05),
        "enable_instrument_selection": textural_config.get("enable_instrument_selection", True)
    })

    harmonic_config = agent_settings.get("harmonic", {})
    harmonic_agent = HarmonicAgent(objectives={
        "key": harmonic_config.get("key", "C"),
        "surprise_rate": harmonic_config.get("surprise_rate", 0.1),
        "chord_duration": harmonic_config.get("chord_duration", 4.0),
        "voicing": harmonic_config.get("voicing", "block")
    })

    melodic_config = agent_settings.get("melodic", {})
    melodic_llm_freq = llm_settings.get("melodic_frequency", 0.3) if llm_settings.get("enabled", True) else 0.0

    melodic_agent = MelodicAgent(objectives={
        "octave": melodic_config.get("octave", 5),
        "motif_length": melodic_config.get("motif_length", 4),
        "variation_rate": melodic_config.get("variation_rate", 0.6),
        "chord_tone_bias": melodic_config.get("chord_tone_bias", 0.75),
        "llm_frequency": melodic_llm_freq
    })

    rhythmic_config = agent_settings.get("rhythmic", {})
    rhythmic_agent = RhythmicAgent(objectives={
        "base_tempo": rhythmic_config.get("base_tempo", initial_tempo),
        "tempo_range": rhythmic_config.get("tempo_range", (75, 110)),
        "tempo_sensitivity": rhythmic_config.get("tempo_sensitivity", 0.7),
        "add_percussion": rhythmic_config.get("add_percussion", False)
    })

    # Initialize tracking variables
    all_events = []
    tempo_changes = [(0, context.tempo)]
    current_absolute_time = 0.0
    intensity_history = []
    llm_stats = {"calls": 0, "success": 0, "fail": 0}

    # Create live display
    with Live(make_display(
        0, num_bars, context,
        {}, {}, {}, {},
        [], llm_stats
    ), refresh_per_second=10) as live:

        for bar in range(num_bars):
            # Update intensity
            context.intensity = calculate_intensity_arc(bar, num_bars)
            intensity_history.append(context.intensity)

            measure_num = context.current_measure

            # Textural agent decides
            textural_agent.step(context)
            textural_decision = textural_agent.memory[-1] if textural_agent.memory else {}

            # Check for pause
            is_pause = context.suggest_pause

            if is_pause:
                # Display pause
                live.update(make_display(
                    bar + 1, num_bars, context,
                    {"chord": "PAUSE"},
                    {"action": "pause", "source": "rule"},
                    {"tempo": context.tempo, "change": 0},
                    textural_decision,
                    intensity_history,
                    llm_stats,
                    is_pause=True
                ))

                current_absolute_time += 4.0
                context.advance_time(4.0)
                continue

            # Harmonic agent decides
            harmonic_events = harmonic_agent.step(context)
            harmonic_decision = harmonic_agent.memory[-1] if harmonic_agent.memory else {}

            # Melodic agent decides
            saved_measure = context.current_measure
            saved_position = context.measure_position
            context.current_measure = measure_num
            context.measure_position = 0.0

            # Track LLM calls
            before_calls = melodic_agent.llm_call_count
            before_success = melodic_agent.llm_success_count
            before_fail = melodic_agent.llm_failure_count

            melodic_events = melodic_agent.step(context)
            melodic_decision = melodic_agent.memory[-1] if melodic_agent.memory else {}

            # Update LLM stats
            after_calls = melodic_agent.llm_call_count
            after_success = melodic_agent.llm_success_count
            after_fail = melodic_agent.llm_failure_count

            llm_stats["calls"] += (after_calls - before_calls)
            llm_stats["success"] += (after_success - before_success)
            llm_stats["fail"] += (after_fail - before_fail)

            context.current_measure = measure_num
            context.measure_position = 0.0

            # Rhythmic agent decides
            old_tempo = context.tempo
            rhythmic_events = rhythmic_agent.step(context)
            tempo_change = context.tempo - old_tempo
            rhythmic_decision = {"tempo": context.tempo, "change": tempo_change}

            if bar > 0:
                tempo_changes.append((current_absolute_time, context.tempo))

            # Collect and modify events
            bar_events = harmonic_events + melodic_events + rhythmic_events
            bar_events = apply_textural_modifications(bar_events, context)

            for event in bar_events:
                event["time"] = event.get("time", 0) + current_absolute_time

            all_events.extend(bar_events)

            # Restore context
            context.current_measure = saved_measure
            context.measure_position = saved_position

            # Update display
            live.update(make_display(
                bar + 1, num_bars, context,
                harmonic_decision,
                melodic_decision,
                rhythmic_decision,
                textural_decision,
                intensity_history,
                llm_stats
            ))

            current_absolute_time += 4.0

    # Create console for colored output
    console = Console()

    # Save MIDI file
    console.print(f"\n[bold green]✓ Generation complete![/]")
    console.print(f"Converting to MIDI: {output_file}")

    mid = events_to_midi(all_events, tempo_changes)

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    mid.save(output_file)

    console.print(f"[bold green]✓ MIDI file saved: {output_file}[/]")

    # Print summary statistics
    console.print("\n" + "=" * 70)
    console.print("[bold]COMPOSITION SUMMARY[/]")
    console.print("=" * 70)

    tempos = [t[1] for t in tempo_changes]
    console.print(f"Tempo: {tempos[0]} → {tempos[-1]} BPM (range: {min(tempos)}-{max(tempos)})")
    console.print(f"Intensity: {min(intensity_history):.2f} → {max(intensity_history):.2f}")
    console.print(f"LLM usage: {llm_stats['calls']} calls, {llm_stats['success']} successful ({llm_stats['success']/max(llm_stats['calls'],1)*100:.0f}%)")
    console.print(f"Total MIDI events: {len(all_events)}")

    console.print("\n[bold cyan]Next steps:[/]")
    console.print(f"  1. Render to audio: [bold]python3 render_audio.py {output_file}[/]")
    console.print(f"  2. Play: [bold]afplay {output_file.replace('.mid', '.wav')}[/]")

    return output_file


def parse_midi_for_playback(midi_file: str):
    """
    Parse MIDI file to extract notes with timing for playback visualization.

    Returns:
        List of note events with absolute timing in seconds
    """
    from core.music_theory import midi_to_note_name

    mid = mido.MidiFile(midi_file)
    notes = []

    # Get tempo (assuming constant tempo or using first tempo)
    tempo = 500000  # Default 120 BPM
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break

    # Convert tempo to seconds per tick
    ticks_per_beat = mid.ticks_per_beat
    seconds_per_tick = (tempo / 1000000) / ticks_per_beat

    # Track note_on and note_off events
    active_notes = {}  # note_number -> start_time
    current_time = 0.0

    for track in mid.tracks:
        track_time = 0.0
        for msg in track:
            track_time += msg.time * seconds_per_tick

            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[msg.note] = track_time
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_notes:
                    start_time = active_notes[msg.note]
                    duration = track_time - start_time
                    note_name_tuple = midi_to_note_name(msg.note)
                    note_name = f"{note_name_tuple[0]}{note_name_tuple[1]}"

                    notes.append({
                        'note': msg.note,
                        'note_name': note_name,
                        'start_time': start_time,
                        'end_time': track_time,
                        'duration': duration,
                        'channel': msg.channel
                    })
                    del active_notes[msg.note]

    # Sort by start time
    notes.sort(key=lambda n: n['start_time'])

    return notes, mid.length


def create_playback_piano_roll(notes, current_time, total_duration):
    """
    Create piano roll visualization for playback showing current position.

    Args:
        notes: List of note events from parse_midi_for_playback
        current_time: Current playback time in seconds
        total_duration: Total duration in seconds

    Returns:
        Formatted piano roll string
    """
    if not notes:
        return "  [No notes in composition]"

    # Time window (show 4 seconds: 2 before current, 2 after)
    window_before = 2.0
    window_after = 2.0
    window_start = max(0, current_time - window_before)
    window_end = min(total_duration, current_time + window_after)

    # Filter notes in window
    visible_notes = [n for n in notes if n['end_time'] >= window_start and n['start_time'] <= window_end]

    if not visible_notes:
        # Still show something when no notes visible (e.g., at end of composition)
        return "  [dim]♪ Composition ending...[/]"

    # Find note range
    midi_notes = [n['note'] for n in visible_notes]
    min_note = max(min(midi_notes) - 1, 36)  # C2 minimum
    max_note = min(max(midi_notes) + 1, 96)  # C7 maximum

    # Limit range
    if max_note - min_note > 13:
        center = int(sum(midi_notes) / len(midi_notes))
        min_note = max(center - 6, 36)
        max_note = min(center + 6, 96)

    width = 50
    lines = []

    # Build piano roll
    for midi_note in range(max_note, min_note - 1, -1):
        from core.music_theory import midi_to_note_name
        note_name_tuple = midi_to_note_name(midi_note)
        note_name = f"{note_name_tuple[0]}{note_name_tuple[1]}"

        timeline = [' '] * width

        # Plot notes
        for note_event in visible_notes:
            if note_event['note'] == midi_note:
                start = note_event['start_time']
                end = note_event['end_time']

                # Map to timeline position
                time_range = window_end - window_start
                if time_range > 0:
                    x_start = int(((start - window_start) / time_range) * width)
                    x_end = int(((end - window_start) / time_range) * width)

                    # Determine if note is playing now
                    is_current = start <= current_time <= end

                    # Choose character based on state and channel
                    if is_current:
                        char = '█'  # Currently playing - bright
                    elif end < current_time:
                        char = '░'  # Past - dim
                    else:
                        char = '▒'  # Future - medium

                    for x in range(max(0, x_start), min(width, x_end)):
                        timeline[x] = char

        # Format line with colors
        line_str = ''.join(timeline)

        # Color by state
        if '█' in line_str:
            line_str = f"[bold yellow]{line_str}[/]"  # Current - yellow
        elif '░' in line_str:
            line_str = f"[dim cyan]{line_str}[/]"  # Past - dim cyan
        elif '▒' in line_str:
            line_str = f"[magenta]{line_str}[/]"  # Future - magenta
        else:
            line_str = f"[dim]{line_str}[/]"

        lines.append(f"{note_name:>4} │{line_str}")

    # Add playhead indicator
    playhead_pos = int(((current_time - window_start) / (window_end - window_start)) * width)
    playhead_line = ' ' * 5 + '│' + ' ' * playhead_pos + '▼'
    lines.append(f"[bold green]{playhead_line}[/]")

    return "\n".join(lines)


def visualize_playback(midi_file: str, audio_file: str):
    """
    Play audio file with synchronized piano roll visualization.

    Args:
        midi_file: Path to MIDI file
        audio_file: Path to audio file to play
    """
    console = Console()

    # Parse MIDI file
    console.print("[bold cyan]Parsing MIDI file...[/]")
    notes, total_duration = parse_midi_for_playback(midi_file)

    if not notes:
        console.print("[bold red]No notes found in MIDI file![/]")
        return

    console.print(f"[bold green]Found {len(notes)} notes, duration: {total_duration:.1f}s[/]")

    # Start audio playback in background
    console.print(f"[bold cyan]Starting playback...[/]\n")
    audio_process = subprocess.Popen(
        ["afplay", audio_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    start_time = time.time()

    # Create live display
    with Live(console=console, refresh_per_second=20) as live:
        try:
            while audio_process.poll() is None:  # While playing
                current_time = time.time() - start_time

                # Continue visualizing even past MIDI duration to match audio length
                # Use max to ensure we don't go backwards
                display_duration = max(total_duration, current_time)

                # Create piano roll
                piano_roll = create_playback_piano_roll(notes, current_time, display_duration)

                # Calculate progress
                progress_pct = (current_time / display_duration) * 100 if display_duration > 0 else 0
                progress_bar = '█' * int(progress_pct / 2) + '░' * (50 - int(progress_pct / 2))

                # Create display
                panel_content = Text.from_markup(
                    f"{piano_roll}\n\n"
                    f"[bold]Time:[/] {current_time:.1f}s / {display_duration:.1f}s\n"
                    f"[cyan]{progress_bar}[/] {progress_pct:.1f}%"
                )

                panel = Panel(
                    panel_content,
                    title="[bold yellow]🎵 PLAYBACK VISUALIZATION 🎵[/]",
                    title_align="center",
                    border_style="yellow",
                    box=box.DOUBLE
                )

                live.update(panel)
                time.sleep(0.05)  # 20 FPS

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Playback stopped by user[/]")
            audio_process.terminate()

        finally:
            # Ensure process is terminated
            if audio_process.poll() is None:
                audio_process.terminate()

    console.print("\n[bold green]✓ Playback complete![/]")


def interactive_workflow(output_file: str):
    """Interactive workflow for rendering and playing audio."""
    import subprocess
    from pathlib import Path

    console = Console()
    # render_audio.py saves to output/audio/ directory, not same dir as MIDI
    midi_path = Path(output_file)
    audio_file = f"output/audio/{midi_path.stem}.wav"
    audio_path = Path(audio_file)

    # Prompt for rendering
    console.print("\n[bold yellow]═══════════════════════════════════════════════════════════════════[/]")
    render_choice = input("🎧 Render to audio? [Y/n]: ").strip().lower()

    if render_choice in ['', 'y', 'yes']:
        console.print(f"[bold cyan]Rendering audio...[/]")
        try:
            # Call render_audio.py
            result = subprocess.run(
                ["python3", "render_audio.py", output_file],
                check=True,
                capture_output=True,
                text=True
            )
            console.print(f"[bold green]✓ Audio rendered: {audio_file}[/]")

            # Prompt for playback
            play_choice = input("🔊 Play audio with visualization? [Y/n]: ").strip().lower()

            if play_choice in ['', 'y', 'yes']:
                # Play with synchronized piano roll visualization
                try:
                    visualize_playback(output_file, audio_file)
                except (subprocess.CalledProcessError, FileNotFoundError) as e:
                    console.print(f"[bold red]✗ Error during playback: {e}[/]")
                except Exception as e:
                    console.print(f"[bold red]✗ Error: {e}[/]")
            else:
                console.print(f"[dim]Skipped playback. Play later with:[/] afplay {audio_file}")

        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]✗ Error rendering audio: {e}[/]")
            console.print(f"[dim]Try manually:[/] python3 render_audio.py {output_file}")
        except FileNotFoundError:
            console.print(f"[bold red]✗ render_audio.py not found[/]")
    else:
        console.print(f"[dim]Skipped rendering. Render later with:[/] python3 render_audio.py {output_file}")

    console.print("[bold yellow]═══════════════════════════════════════════════════════════════════[/]")


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Live Terminal UI for Agentic Symphony Composition"
    )
    parser.add_argument(
        "--bars", "-b",
        type=int,
        default=16,
        help="Number of bars to generate (default: 16)"
    )
    parser.add_argument(
        "--preset", "-p",
        type=str,
        default="default",
        help="Configuration preset (default, minimal, dramatic, llm_heavy, pure_rules, no_instruments)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output MIDI file path"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="List available presets"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode: prompt to render audio and play after generation"
    )

    args = parser.parse_args()

    if args.list_presets:
        presets_file = Path("config/presets.json")
        if presets_file.exists():
            with open(presets_file) as f:
                data = json.load(f)
                presets = data.get("presets", {})
                print("Available presets:")
                for name in presets.keys():
                    print(f"  - {name}")
        return

    output_file = live_compose(
        num_bars=args.bars,
        preset_name=args.preset,
        output_file=args.output,
        seed=args.seed
    )

    # Run interactive workflow if requested
    if args.interactive:
        interactive_workflow(output_file)


if __name__ == "__main__":
    main()
