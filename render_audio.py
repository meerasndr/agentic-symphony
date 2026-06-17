"""
Helper script to render MIDI files to audio using FluidSynth.
"""

import subprocess
import os
from pathlib import Path


def render_midi_to_wav(
    midi_file: str,
    output_file: str,
    soundfont: str = "soundfonts/default.sf2",
    sample_rate: int = 44100
):
    """
    Render a MIDI file to WAV audio using FluidSynth.

    Args:
        midi_file: Path to input MIDI file
        output_file: Path to output WAV file
        soundfont: Path to soundfont file (.sf2)
        sample_rate: Audio sample rate (default 44100 Hz)

    Returns:
        True if successful, False otherwise
    """
    # Check if FluidSynth is installed
    try:
        subprocess.run(
            ["fluidsynth", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: FluidSynth is not installed!")
        print("\nTo install FluidSynth:")
        print("  macOS:   brew install fluid-synth")
        print("  Ubuntu:  sudo apt-get install fluidsynth")
        print("  Windows: Download from https://www.fluidsynth.org/")
        return False

    # Check if soundfont exists
    if not os.path.exists(soundfont):
        print(f"ERROR: Soundfont not found: {soundfont}")
        print("\nTo download a soundfont:")
        print("  1. MuseScore General: https://github.com/musescore/MuseScore/blob/master/share/sound/MuseScore_General.sf3")
        print("  2. FluidR3_GM: http://www.musescore.org/download/fluid-soundfont.tar.gz")
        print("  3. Place the .sf2 file in the soundfonts/ directory")
        return False

    # Check if MIDI file exists
    if not os.path.exists(midi_file):
        print(f"ERROR: MIDI file not found: {midi_file}")
        return False

    # Render to WAV
    print(f"Rendering {midi_file} to {output_file}...")
    try:
        cmd = [
            "fluidsynth",
            "-ni",  # No interactive mode
            "-a", "file",  # Use file audio driver (no playback)
            "-F", output_file,  # Output to file (must come before soundfont/MIDI)
            "-r", str(sample_rate),  # Sample rate
            soundfont,
            midi_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✓ Successfully rendered: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: FluidSynth failed: {e}")
        print(f"STDERR: {e.stderr}")
        return False


def render_all_midi_files(
    input_dir: str = "output/compositions",
    output_dir: str = "output/audio",
    soundfont: str = "soundfonts/default.sf2"
):
    """
    Render all MIDI files in a directory to audio.

    Args:
        input_dir: Directory containing MIDI files
        output_dir: Directory for output WAV files
        soundfont: Path to soundfont file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Find all MIDI files
    midi_files = list(Path(input_dir).glob("*.mid")) + list(Path(input_dir).glob("*.midi"))

    if not midi_files:
        print(f"No MIDI files found in {input_dir}")
        return

    print(f"Found {len(midi_files)} MIDI file(s)")
    print("=" * 60)

    success_count = 0
    for midi_file in midi_files:
        output_file = Path(output_dir) / f"{midi_file.stem}.wav"
        if render_midi_to_wav(str(midi_file), str(output_file), soundfont):
            success_count += 1
        print()

    print("=" * 60)
    print(f"✓ Rendered {success_count}/{len(midi_files)} files successfully")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Render specific file
        midi_file = sys.argv[1]

        if len(sys.argv) > 2:
            # Output file explicitly specified
            output_file = sys.argv[2]
        else:
            # Auto-generate output path in output/audio/ directory
            from pathlib import Path
            midi_path = Path(midi_file)
            output_file = f"output/audio/{midi_path.stem}.wav"
            # Ensure output directory exists
            Path("output/audio").mkdir(parents=True, exist_ok=True)

        soundfont = sys.argv[3] if len(sys.argv) > 3 else "soundfonts/default.sf2"

        success = render_midi_to_wav(midi_file, output_file, soundfont)
        if success:
            print(f"\nTo play: afplay {output_file}")
    else:
        # Render all files in output/compositions
        print("AGENTIC SYMPHONY - Audio Renderer")
        print("=" * 60)
        render_all_midi_files()
