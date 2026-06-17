"""
Generate demo compositions for Phase 6.
Uses the complete 4-agent system to create multiple compositions
and tracks their characteristics for selection.
"""

import sys
import random
import json
from pathlib import Path
from test_four_agents import test_four_agents


def generate_demo_compositions(count: int = 20, bars: int = 16):
    """
    Generate multiple demo compositions and track their characteristics.

    Args:
        count: Number of compositions to generate
        bars: Number of bars per composition
    """
    print("=" * 70)
    print(f"PHASE 6: DEMO COMPOSITION GENERATION")
    print(f"Generating {count} compositions with {bars} bars each")
    print("=" * 70)
    print()

    compositions = []
    catalog = []

    for i in range(count):
        # Set different random seed for each composition
        seed = i + 1000
        random.seed(seed)

        print(f"\n{'=' * 70}")
        print(f"COMPOSITION #{i+1:02d}/{count}")
        print(f"Random seed: {seed}")
        print(f"{'=' * 70}\n")

        output_file = f"output/compositions/demo_{i+1:02d}.mid"

        # Generate composition
        generated_file = test_four_agents(bars, output_file)
        compositions.append(generated_file)

        # Extract metadata for catalog
        # We'll read the console output to capture characteristics
        # For now, just record basic info
        catalog_entry = {
            "id": i + 1,
            "filename": output_file,
            "seed": seed,
            "bars": bars,
            "notes": ""  # User can add notes after listening
        }
        catalog.append(catalog_entry)

        print(f"\n✓ Composition #{i+1:02d} saved to {output_file}\n")

    # Save catalog to JSON
    catalog_file = "output/compositions/demo_catalog.json"
    with open(catalog_file, 'w') as f:
        json.dump(catalog, f, indent=2)

    print("\n" + "=" * 70)
    print("✓ ALL COMPOSITIONS GENERATED")
    print("=" * 70)
    print(f"\nGenerated {len(compositions)} compositions:")
    for i, comp in enumerate(compositions, 1):
        print(f"  {i:2d}. {comp}")

    print(f"\nCatalog saved to: {catalog_file}")

    print(f"\n{'=' * 70}")
    print("NEXT STEPS")
    print(f"{'=' * 70}")
    print(f"\n1. Render all to audio (this may take a few minutes):")
    print(f"   python3 render_audio.py")

    print(f"\n2. Listen to each composition and take notes:")
    print(f"   Use the listening script:")
    print(f"   python3 listen_and_evaluate.py")

    print(f"\n3. Or listen manually:")
    for i in range(1, min(6, count + 1)):
        print(f"   afplay output/audio/demo_{i:02d}.wav")

    return compositions


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    bars = int(sys.argv[2]) if len(sys.argv) > 2 else 16

    print(f"\n⚠️  This will generate {count} compositions.")
    print(f"   Each composition takes ~1-2 seconds to generate.")
    print(f"   Total estimated time: ~{count * 2} seconds ({count * 2 / 60:.1f} minutes)\n")

    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    compositions = generate_demo_compositions(count, bars)

    print(f"\n{'=' * 70}")
    print("✓ PHASE 6 STEP 1 COMPLETE")
    print(f"{'=' * 70}")
