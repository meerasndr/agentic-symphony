"""
Interactive Composition Interface

Allows you to tweak all parameters (LLM usage, instruments, duration, etc.)
and generate compositions with custom configurations.
"""

import json
import sys
import random
from pathlib import Path
from datetime import datetime
from tests.test_four_agents import test_four_agents
from core.context import MusicalContext
from agents.harmonic import HarmonicAgent
from agents.melodic import MelodicAgent
from agents.rhythmic import RhythmicAgent
from agents.textural import TexturalAgent


def load_presets():
    """Load presets from JSON file."""
    preset_file = Path("config/presets.json")
    if not preset_file.exists():
        print("❌ Presets file not found: config/presets.json")
        return {}

    with open(preset_file, 'r') as f:
        data = json.load(f)
    return data.get("presets", {})


def display_presets(presets):
    """Display available presets."""
    print("\n" + "=" * 70)
    print("AVAILABLE PRESETS")
    print("=" * 70)

    for i, (key, preset) in enumerate(presets.items(), 1):
        name = preset.get("name", key)
        desc = preset.get("description", "No description")
        llm_enabled = preset.get("llm", {}).get("enabled", False)
        num_bars = preset.get("composition", {}).get("num_bars", 16)

        llm_indicator = "🤖 LLM" if llm_enabled else "📏 Rules"

        print(f"\n{i}. [{key}] {name}")
        print(f"   {desc}")
        print(f"   {llm_indicator} | {num_bars} bars")


def display_config(config):
    """Display current configuration."""
    print("\n" + "=" * 70)
    print("CURRENT CONFIGURATION")
    print("=" * 70)

    # Composition settings
    comp = config.get("composition", {})
    print(f"\n📝 Composition:")
    print(f"   Bars: {comp.get('num_bars', 16)}")
    print(f"   Tempo: {comp.get('tempo', 90)} BPM")
    print(f"   Time: {comp.get('time_signature', [4, 4])[0]}/{comp.get('time_signature', [4, 4])[1]}")
    print(f"   Key: {comp.get('key', 'C')}")

    # LLM settings
    llm = config.get("llm", {})
    print(f"\n🤖 LLM Settings:")
    print(f"   Enabled: {llm.get('enabled', True)}")
    print(f"   Melodic frequency: {llm.get('melodic_frequency', 0.3):.0%}")
    print(f"   Harmonic frequency: {llm.get('harmonic_frequency', 0.0):.0%}")
    print(f"   Textural frequency: {llm.get('textural_frequency', 0.0):.0%}")

    # Agent settings
    agents = config.get("agents", {})

    print(f"\n🎹 Harmonic Agent:")
    harm = agents.get("harmonic", {})
    print(f"   Enabled: {harm.get('enabled', True)}")
    print(f"   Surprise rate: {harm.get('surprise_rate', 0.1):.0%}")
    print(f"   Voicing: {harm.get('voicing', 'block')}")

    print(f"\n🎵 Melodic Agent:")
    mel = agents.get("melodic", {})
    print(f"   Enabled: {mel.get('enabled', True)}")
    print(f"   LLM frequency: {mel.get('llm_frequency', 0.3):.0%}")
    print(f"   Variation rate: {mel.get('variation_rate', 0.5):.0%}")
    print(f"   Octave: {mel.get('octave', 5)}")

    print(f"\n⏱️  Rhythmic Agent:")
    rhy = agents.get("rhythmic", {})
    print(f"   Enabled: {rhy.get('enabled', True)}")
    print(f"   Tempo range: {rhy.get('tempo_range', [75, 110])}")
    print(f"   Sensitivity: {rhy.get('tempo_sensitivity', 0.7):.0%}")

    print(f"\n🎨 Textural Agent:")
    tex = agents.get("textural", {})
    print(f"   Enabled: {tex.get('enabled', True)}")
    print(f"   Dynamic range: {tex.get('dynamic_range', [0.5, 1.2])}")
    print(f"   Pause probability: {tex.get('pause_probability', 0.08):.0%}")
    print(f"   Instrument selection: {tex.get('enable_instrument_selection', True)}")


def tweak_parameter(config):
    """Interactive parameter tweaking."""
    print("\n" + "=" * 70)
    print("TWEAK PARAMETERS")
    print("=" * 70)
    print("\nWhat would you like to adjust?")
    print("\n1. Composition settings (bars, tempo, key)")
    print("2. LLM settings (enable/disable, frequencies)")
    print("3. Harmonic agent settings")
    print("4. Melodic agent settings")
    print("5. Rhythmic agent settings")
    print("6. Textural agent settings")
    print("0. Back to main menu")

    choice = input("\nSelect category (0-6): ").strip()

    if choice == "1":
        tweak_composition(config)
    elif choice == "2":
        tweak_llm(config)
    elif choice == "3":
        tweak_harmonic(config)
    elif choice == "4":
        tweak_melodic(config)
    elif choice == "5":
        tweak_rhythmic(config)
    elif choice == "6":
        tweak_textural(config)

    return config


def tweak_composition(config):
    """Tweak composition settings."""
    comp = config.setdefault("composition", {})

    print("\n📝 Composition Settings:")

    # Number of bars
    current_bars = comp.get("num_bars", 16)
    bars_input = input(f"Number of bars [{current_bars}]: ").strip()
    if bars_input:
        try:
            comp["num_bars"] = int(bars_input)
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Tempo
    current_tempo = comp.get("tempo", 90)
    tempo_input = input(f"Tempo BPM [{current_tempo}]: ").strip()
    if tempo_input:
        try:
            comp["tempo"] = int(tempo_input)
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Key
    current_key = comp.get("key", "C")
    key_input = input(f"Key [{current_key}]: ").strip()
    if key_input:
        comp["key"] = key_input.upper()

    print("\n✅ Composition settings updated!")


def tweak_llm(config):
    """Tweak LLM settings."""
    llm = config.setdefault("llm", {})

    print("\n🤖 LLM Settings:")

    # Enable/disable
    current_enabled = llm.get("enabled", True)
    enable_input = input(f"Enable LLM? (y/n) [{'y' if current_enabled else 'n'}]: ").strip().lower()
    if enable_input:
        llm["enabled"] = (enable_input == 'y')

    # Melodic frequency
    current_freq = llm.get("melodic_frequency", 0.3)
    freq_input = input(f"Melodic LLM frequency (0.0-1.0) [{current_freq}]: ").strip()
    if freq_input:
        try:
            freq = float(freq_input)
            if 0.0 <= freq <= 1.0:
                llm["melodic_frequency"] = freq
                # Also update melodic agent
                config.setdefault("agents", {}).setdefault("melodic", {})["llm_frequency"] = freq
            else:
                print("❌ Frequency must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    print("\n✅ LLM settings updated!")


def tweak_harmonic(config):
    """Tweak harmonic agent settings."""
    harm = config.setdefault("agents", {}).setdefault("harmonic", {})

    print("\n🎹 Harmonic Agent Settings:")

    # Surprise rate
    current_rate = harm.get("surprise_rate", 0.1)
    rate_input = input(f"Surprise rate (0.0-1.0) [{current_rate}]: ").strip()
    if rate_input:
        try:
            rate = float(rate_input)
            if 0.0 <= rate <= 1.0:
                harm["surprise_rate"] = rate
            else:
                print("❌ Rate must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Voicing
    current_voicing = harm.get("voicing", "block")
    voicing_input = input(f"Voicing (block/arpeggio) [{current_voicing}]: ").strip().lower()
    if voicing_input in ["block", "arpeggio"]:
        harm["voicing"] = voicing_input

    print("\n✅ Harmonic agent settings updated!")


def tweak_melodic(config):
    """Tweak melodic agent settings."""
    mel = config.setdefault("agents", {}).setdefault("melodic", {})

    print("\n🎵 Melodic Agent Settings:")

    # LLM frequency
    current_freq = mel.get("llm_frequency", 0.3)
    freq_input = input(f"LLM frequency (0.0-1.0) [{current_freq}]: ").strip()
    if freq_input:
        try:
            freq = float(freq_input)
            if 0.0 <= freq <= 1.0:
                mel["llm_frequency"] = freq
            else:
                print("❌ Frequency must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Variation rate
    current_var = mel.get("variation_rate", 0.5)
    var_input = input(f"Variation rate (0.0-1.0) [{current_var}]: ").strip()
    if var_input:
        try:
            var = float(var_input)
            if 0.0 <= var <= 1.0:
                mel["variation_rate"] = var
            else:
                print("❌ Rate must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Octave
    current_oct = mel.get("octave", 5)
    oct_input = input(f"Octave (3-6) [{current_oct}]: ").strip()
    if oct_input:
        try:
            oct = int(oct_input)
            if 3 <= oct <= 6:
                mel["octave"] = oct
            else:
                print("❌ Octave must be between 3 and 6")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    print("\n✅ Melodic agent settings updated!")


def tweak_rhythmic(config):
    """Tweak rhythmic agent settings."""
    rhy = config.setdefault("agents", {}).setdefault("rhythmic", {})

    print("\n⏱️  Rhythmic Agent Settings:")

    # Tempo range
    current_range = rhy.get("tempo_range", [75, 110])
    print(f"Current tempo range: {current_range}")
    min_input = input(f"Minimum tempo [{current_range[0]}]: ").strip()
    max_input = input(f"Maximum tempo [{current_range[1]}]: ").strip()

    if min_input or max_input:
        try:
            min_tempo = int(min_input) if min_input else current_range[0]
            max_tempo = int(max_input) if max_input else current_range[1]
            if min_tempo < max_tempo:
                rhy["tempo_range"] = [min_tempo, max_tempo]
            else:
                print("❌ Min must be less than max")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Sensitivity
    current_sens = rhy.get("tempo_sensitivity", 0.7)
    sens_input = input(f"Tempo sensitivity (0.0-1.0) [{current_sens}]: ").strip()
    if sens_input:
        try:
            sens = float(sens_input)
            if 0.0 <= sens <= 1.0:
                rhy["tempo_sensitivity"] = sens
            else:
                print("❌ Sensitivity must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    print("\n✅ Rhythmic agent settings updated!")


def tweak_textural(config):
    """Tweak textural agent settings."""
    tex = config.setdefault("agents", {}).setdefault("textural", {})

    print("\n🎨 Textural Agent Settings:")

    # Pause probability
    current_pause = tex.get("pause_probability", 0.08)
    pause_input = input(f"Pause probability (0.0-1.0) [{current_pause}]: ").strip()
    if pause_input:
        try:
            pause = float(pause_input)
            if 0.0 <= pause <= 1.0:
                tex["pause_probability"] = pause
            else:
                print("❌ Probability must be between 0.0 and 1.0")
        except ValueError:
            print("❌ Invalid number, keeping current value")

    # Instrument selection
    current_inst = tex.get("enable_instrument_selection", True)
    inst_input = input(f"Enable dynamic instrument selection? (y/n) [{'y' if current_inst else 'n'}]: ").strip().lower()
    if inst_input:
        tex["enable_instrument_selection"] = (inst_input == 'y')

    print("\n✅ Textural agent settings updated!")


def generate_with_config(config):
    """Generate composition using current configuration."""
    print("\n" + "=" * 70)
    print("GENERATING COMPOSITION")
    print("=" * 70)

    # Set random seed for reproducibility
    seed_input = input("\nRandom seed (leave empty for random): ").strip()
    if seed_input:
        try:
            seed = int(seed_input)
            random.seed(seed)
            print(f"✓ Using seed: {seed}")
        except ValueError:
            print("❌ Invalid seed, using random")
            seed = random.randint(1000, 9999)
            random.seed(seed)
            print(f"✓ Generated seed: {seed}")
    else:
        seed = random.randint(1000, 9999)
        random.seed(seed)
        print(f"✓ Generated seed: {seed}")

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/compositions/interactive_{timestamp}.mid"

    # Extract parameters
    num_bars = config.get("composition", {}).get("num_bars", 16)

    print(f"\nGenerating {num_bars}-bar composition...")
    print(f"Output file: {output_file}")
    print()

    # Generate using test_four_agents
    # Note: We'd need to modify test_four_agents to accept config, but for now just call it
    result_file = test_four_agents(num_bars, output_file)

    print(f"\n✅ Composition generated!")
    print(f"   MIDI: {result_file}")
    print(f"\nNext steps:")
    print(f"1. Render to audio:")
    print(f"   python3 render_audio.py {result_file}")
    print(f"2. Play audio:")
    print(f"   afplay {result_file.replace('.mid', '.wav').replace('compositions', 'audio')}")


def save_preset(config, presets):
    """Save current configuration as a preset."""
    print("\n" + "=" * 70)
    print("SAVE PRESET")
    print("=" * 70)

    name = input("\nPreset key (e.g., 'my_preset'): ").strip()
    if not name:
        print("❌ Cancelled")
        return

    if name in presets:
        confirm = input(f"⚠️  Preset '{name}' exists. Overwrite? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return

    display_name = input("Display name: ").strip()
    description = input("Description: ").strip()

    preset = {
        "name": display_name or name,
        "description": description or "Custom preset",
        **config
    }

    presets[name] = preset

    # Save to file
    preset_file = Path("config/presets.json")
    with open(preset_file, 'w') as f:
        json.dump({"presets": presets}, f, indent=2)

    print(f"\n✅ Preset '{name}' saved!")


def main():
    """Main interactive loop."""
    print("\n" + "=" * 70)
    print("AGENTIC SYMPHONY - INTERACTIVE COMPOSER")
    print("Multi-Agent Music Composition System")
    print("=" * 70)

    # Load presets
    presets = load_presets()

    # Current configuration
    current_config = None

    while True:
        print("\n" + "=" * 70)
        print("MAIN MENU")
        print("=" * 70)
        print("\n1. Select a preset")
        print("2. View current configuration")
        print("3. Tweak parameters")
        print("4. Generate composition")
        print("5. Save current config as preset")
        print("0. Exit")

        choice = input("\nSelect option (0-5): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!")
            break

        elif choice == "1":
            display_presets(presets)
            preset_num = input("\nSelect preset number: ").strip()
            try:
                preset_key = list(presets.keys())[int(preset_num) - 1]
                current_config = presets[preset_key].copy()
                print(f"\n✅ Loaded preset: {presets[preset_key]['name']}")
            except (ValueError, IndexError, KeyError):
                print("❌ Invalid selection")

        elif choice == "2":
            if current_config is None:
                print("\n⚠️  No configuration loaded. Please select a preset first.")
            else:
                display_config(current_config)

        elif choice == "3":
            if current_config is None:
                print("\n⚠️  No configuration loaded. Please select a preset first.")
            else:
                current_config = tweak_parameter(current_config)

        elif choice == "4":
            if current_config is None:
                print("\n⚠️  No configuration loaded. Please select a preset first.")
            else:
                generate_with_config(current_config)

        elif choice == "5":
            if current_config is None:
                print("\n⚠️  No configuration loaded. Please select a preset first.")
            else:
                save_preset(current_config, presets)

        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
