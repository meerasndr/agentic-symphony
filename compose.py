#!/usr/bin/env python3
"""
Quick Compose - Simple command-line interface for generating compositions

Usage:
    python3 compose.py                    # Interactive mode
    python3 compose.py --preset default   # Use preset
    python3 compose.py --bars 24 --llm    # Quick config
    python3 compose.py --list             # List presets
"""

import argparse
import json
import random
from pathlib import Path
from datetime import datetime
from tests.test_four_agents import test_four_agents


def load_presets():
    """Load presets from JSON file."""
    preset_file = Path("config/presets.json")
    if preset_file.exists():
        with open(preset_file, 'r') as f:
            return json.load(f).get("presets", {})
    return {}


def list_presets():
    """List available presets."""
    presets = load_presets()
    print("\n" + "=" * 70)
    print("AVAILABLE PRESETS")
    print("=" * 70 + "\n")

    for key, preset in presets.items():
        name = preset.get("name", key)
        desc = preset.get("description", "")
        bars = preset.get("composition", {}).get("num_bars", 16)
        llm = "🤖 LLM" if preset.get("llm", {}).get("enabled") else "📏 Rules"

        print(f"  {key:15} - {name}")
        print(f"  {' ' * 15}   {desc}")
        print(f"  {' ' * 15}   {llm} | {bars} bars\n")


def generate_composition(preset_name=None, bars=None, llm=None, no_instruments=None, seed=None):
    """Generate a composition with specified parameters."""

    # Load preset or use defaults
    if preset_name:
        presets = load_presets()
        if preset_name not in presets:
            print(f"Preset '{preset_name}' not found")
            print(f"Available presets: {', '.join(presets.keys())}")
            return
        config = presets[preset_name]
        print(f"✓ Using preset: {config.get('name', preset_name)}")
    else:
        # Use default preset
        presets = load_presets()
        config = presets.get("default", {})
        print("✓ Using default preset")

    # Override parameters if specified
    if bars is not None:
        config.setdefault("composition", {})["num_bars"] = bars
        print(f"✓ Overriding bars: {bars}")

    if llm is not None:
        config.setdefault("llm", {})["enabled"] = llm
        freq = 0.3 if llm else 0.0
        config["llm"]["melodic_frequency"] = freq
        config.setdefault("agents", {}).setdefault("melodic", {})["llm_frequency"] = freq
        print(f"✓ LLM {'enabled' if llm else 'disabled'}")

    if no_instruments is not None:
        config.setdefault("agents", {}).setdefault("textural", {})["enable_instrument_selection"] = not no_instruments
        print(f"✓ Instrument selection: {'disabled' if no_instruments else 'enabled'}")

    # Set seed
    if seed is not None:
        random.seed(seed)
        print(f"✓ Using seed: {seed}")
    else:
        seed = random.randint(1000, 9999)
        random.seed(seed)
        print(f"✓ Generated seed: {seed}")

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/compositions/compose_{timestamp}.mid"

    # Extract parameters
    num_bars = config.get("composition", {}).get("num_bars", 16)

    print(f"\n{'=' * 70}")
    print(f"GENERATING COMPOSITION")
    print(f"{'=' * 70}")
    print(f"Bars: {num_bars}")
    print(f"Output: {output_file}")
    print(f"{'=' * 70}\n")

    # Generate
    result_file = test_four_agents(num_bars, output_file)

    print(f"\n{'=' * 70}")
    print(f"✅ COMPOSITION COMPLETE")
    print(f"{'=' * 70}")
    print(f"\nMIDI file: {result_file}")
    print(f"Seed: {seed} (use --seed {seed} to reproduce)")
    print(f"\nNext steps:")
    print(f"1. Render to audio:")
    print(f"   python3 render_audio.py {result_file}")
    print(f"2. Play:")
    audio_file = result_file.replace('.mid', '.wav').replace('compositions', 'audio')
    print(f"   afplay {audio_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Agentic Symphony - Quick Compose",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 compose.py --list                     List available presets
  python3 compose.py                            Interactive mode (default preset)
  python3 compose.py --preset dramatic          Use 'dramatic' preset
  python3 compose.py --bars 24                  Generate 24-bar composition
  python3 compose.py --no-llm                   Disable LLM (pure rules)
  python3 compose.py --llm --bars 16            Enable LLM, 16 bars
  python3 compose.py --preset minimal --seed 42 Minimal preset with seed 42
  python3 compose.py --no-instruments           Fixed instruments (no dynamic changes)
        """
    )

    parser.add_argument("--list", action="store_true",
                        help="List available presets")
    parser.add_argument("--preset", "-p", type=str,
                        help="Preset name to use")
    parser.add_argument("--bars", "-b", type=int,
                        help="Number of bars to generate")
    parser.add_argument("--llm", action="store_true",
                        help="Enable LLM (default: from preset)")
    parser.add_argument("--no-llm", action="store_true",
                        help="Disable LLM (pure rule-based)")
    parser.add_argument("--no-instruments", action="store_true",
                        help="Disable dynamic instrument selection")
    parser.add_argument("--seed", "-s", type=int,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    # Handle list
    if args.list:
        list_presets()
        return

    # Determine LLM setting
    llm_setting = None
    if args.llm:
        llm_setting = True
    elif args.no_llm:
        llm_setting = False

    # Generate composition
    generate_composition(
        preset_name=args.preset,
        bars=args.bars,
        llm=llm_setting,
        no_instruments=args.no_instruments,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
