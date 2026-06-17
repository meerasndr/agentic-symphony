#!/usr/bin/env python3
"""
Play a composition with synchronized piano roll visualization.

Usage:
    python3 play_with_viz.py output/compositions/demo_01.mid
    python3 play_with_viz.py output/compositions/demo_01.mid output/audio/demo_01.wav
"""

import sys
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
import mido

console = Console()


def parse_midi_for_playback(midi_file: str):
    """Parse MIDI file to extract notes with timing for playback visualization."""
    mid = mido.MidiFile(midi_file)
    notes = []

    # Get tempo from the file (look for set_tempo messages)
    tempo = 500000  # Default 120 BPM (500000 microseconds per beat)
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break

    ticks_per_beat = mid.ticks_per_beat
    seconds_per_tick = (tempo / 1000000) / ticks_per_beat

    # Track note_on and note_off events with timing
    active_notes = {}  # {note: start_time}

    for track in mid.tracks:
        track_time = 0.0
        for msg in track:
            track_time += msg.time * seconds_per_tick

            if msg.type == 'note_on' and msg.velocity > 0:
                # Note starts
                active_notes[msg.note] = track_time
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                # Note ends
                if msg.note in active_notes:
                    start_time = active_notes[msg.note]
                    duration = track_time - start_time
                    notes.append({
                        'note': msg.note,
                        'start_time': start_time,
                        'end_time': track_time,
                        'duration': duration,
                        'channel': msg.channel
                    })
                    del active_notes[msg.note]

    # Calculate total duration
    total_duration = max([n['end_time'] for n in notes]) if notes else 0

    return notes, total_duration


def create_playback_piano_roll(notes, current_time, total_duration):
    """Create piano roll showing current playback position."""
    from core.music_theory import midi_to_note_name

    if not notes:
        return "[dim]No notes to display[/]"

    # Always show all notes on a fixed timeline (MIDI duration)
    # This keeps the piano roll visible throughout entire playback, including reverb tail
    midi_duration = max([n['end_time'] for n in notes]) if notes else 0
    window_start = 0
    window_end = midi_duration

    # Show all notes throughout playback
    visible_notes = notes

    # Always show time and progress
    progress = min(1.0, current_time / total_duration) if total_duration > 0 else 0
    progress_bar_width = 70
    filled = int(progress * progress_bar_width)
    filled = min(filled, progress_bar_width)  # Cap at 100%
    progress_bar = '█' * filled + '░' * (progress_bar_width - filled)
    time_line = f" Time: {current_time:.1f}s / {total_duration:.1f}s"

    # Show different message during reverb tail
    if current_time > midi_duration:
        reverb_time = current_time - midi_duration
        progress_line = f" {progress_bar} {progress * 100:.1f}% [dim](reverb/release: +{reverb_time:.1f}s)[/]"
    else:
        progress_line = f" {progress_bar} {progress * 100:.1f}%"

    # Get note range
    all_midi_notes = [n['note'] for n in visible_notes]
    min_note = min(all_midi_notes)
    max_note = max(all_midi_notes)

    # Build piano roll
    width = 70
    lines = []

    for midi_note in range(max_note, min_note - 1, -1):
        note_name_tuple = midi_to_note_name(midi_note)
        note_name = f"{note_name_tuple[0]}{note_name_tuple[1]}"

        # Create timeline for this note - store (char, color) tuples
        timeline = [(' ', None)] * width

        # Plot notes
        for note_event in visible_notes:
            if note_event['note'] == midi_note:
                start = note_event['start_time']
                end = note_event['end_time']

                # Calculate positions
                start_pos = int(((start - window_start) / (window_end - window_start)) * width)
                end_pos = int(((end - window_start) / (window_end - window_start)) * width)

                start_pos = max(0, min(width - 1, start_pos))
                end_pos = max(0, min(width - 1, end_pos))

                # Determine if note is currently playing
                is_current = start <= current_time <= end

                if is_current:
                    char = '█'  # Currently playing - yellow
                    color = 'yellow'
                elif end < current_time:
                    char = '░'  # Past - dim cyan
                    color = 'cyan dim'
                else:
                    char = '▒'  # Future - magenta
                    color = 'magenta'

                # Fill the timeline with colored characters
                for i in range(start_pos, end_pos + 1):
                    timeline[i] = (char, color)

        # Build line with Rich color markup
        line_parts = []
        i = 0
        while i < width:
            char, color = timeline[i]
            # Collect consecutive chars with same color
            start_i = i
            while i < width and timeline[i][1] == color:
                i += 1

            # Build the segment
            segment = ''.join([timeline[j][0] for j in range(start_i, i)])
            if color:
                line_parts.append(f'[{color}]{segment}[/{color}]')
            else:
                line_parts.append(segment)

        line_str = ''.join(line_parts)
        lines.append(f"{note_name:>4} │{line_str}")

    # Add playhead indicator
    playhead_pos = int(((current_time - window_start) / (window_end - window_start)) * width)
    playhead_pos = max(0, min(width - 1, playhead_pos))

    # Show different playhead when past MIDI notes (in reverb tail)
    if current_time > midi_duration:
        playhead_marker = '▼[dim](reverb)[/]'
    else:
        playhead_marker = '▼'

    playhead_line = ' ' * 5 + '│' + ' ' * playhead_pos + playhead_marker

    # Time and progress already calculated above
    result = '\n'.join(lines) + '\n' + playhead_line + '\n' + time_line + '\n' + progress_line
    return result


def get_audio_duration(audio_file: str) -> float:
    """Get the duration of an audio file using afinfo."""
    try:
        result = subprocess.run(
            ["afinfo", audio_file],
            capture_output=True,
            text=True,
            check=True
        )
        # Parse output for "estimated duration: X.XXX sec"
        for line in result.stdout.split('\n'):
            if 'estimated duration:' in line or 'duration:' in line:
                # Extract number before 'sec'
                parts = line.split(':')
                if len(parts) >= 2:
                    duration_str = parts[1].strip().split()[0]
                    return float(duration_str)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass
    return 0.0


def visualize_playback(midi_file: str, audio_file: str):
    """Play audio file with synchronized piano roll visualization."""
    console.print(f"[cyan]Parsing MIDI file...[/]")
    notes, midi_duration = parse_midi_for_playback(midi_file)

    # Get actual audio duration (may be longer due to reverb/release)
    audio_duration = get_audio_duration(audio_file)
    total_duration = max(midi_duration, audio_duration)

    console.print(f"[green]Found {len(notes)} notes, MIDI duration: {midi_duration:.1f}s, Audio duration: {audio_duration:.1f}s[/]")

    console.print(f"[cyan]Starting playback...[/]")

    # Start audio playback in background
    audio_process = subprocess.Popen(
        ["afplay", audio_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    start_time = time.time()

    # Update display at 20 FPS
    try:
        with Live(console=console, refresh_per_second=20) as live:
            while audio_process.poll() is None:
                current_time = time.time() - start_time

                piano_roll = create_playback_piano_roll(notes, current_time, total_duration)
                panel = Panel(
                    piano_roll,
                    title="🎵 PLAYBACK VISUALIZATION 🎵",
                    border_style="cyan"
                )
                live.update(panel)
                time.sleep(0.05)  # 20 FPS

    except KeyboardInterrupt:
        console.print("\n[yellow]Playback interrupted by user[/]")
        audio_process.terminate()
        return

    # Wait for audio to finish
    audio_process.wait()
    console.print("[green]✓ Playback complete![/]")


def main():
    if len(sys.argv) < 2:
        console.print("[red]Usage: python3 play_with_viz.py <midi_file> [audio_file][/]")
        console.print("[yellow]Examples:[/]")
        console.print("  python3 play_with_viz.py output/compositions/demo_01.mid")
        console.print("  python3 play_with_viz.py output/compositions/demo_01.mid output/audio/demo_01.wav")
        sys.exit(1)

    midi_file = sys.argv[1]

    # Check MIDI file exists
    if not Path(midi_file).exists():
        console.print(f"[red]Error: MIDI file not found: {midi_file}[/]")
        sys.exit(1)

    # Determine audio file
    if len(sys.argv) >= 3:
        audio_file = sys.argv[2]
    else:
        # Auto-detect: output/compositions/X.mid -> output/audio/X.wav
        midi_path = Path(midi_file)
        audio_file = f"output/audio/{midi_path.stem}.wav"

    # Check audio file exists
    if not Path(audio_file).exists():
        console.print(f"[red]Error: Audio file not found: {audio_file}[/]")
        console.print(f"[yellow]Tip: Render audio first with:[/]")
        console.print(f"  python3 render_audio.py {midi_file}")
        sys.exit(1)

    console.print(f"[cyan]MIDI: {midi_file}[/]")
    console.print(f"[cyan]Audio: {audio_file}[/]")
    console.print()

    visualize_playback(midi_file, audio_file)


if __name__ == "__main__":
    main()
