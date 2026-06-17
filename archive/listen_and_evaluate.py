"""
Interactive script to listen to compositions and take evaluation notes.
Helps with selecting the best compositions for the demo.
"""

import json
import subprocess
import os
from pathlib import Path


def play_composition(audio_file: str):
    """Play an audio file using afplay."""
    try:
        subprocess.run(["afplay", audio_file], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"Error playing {audio_file}")
        return False


def listen_and_evaluate():
    """
    Interactive listening session for evaluating compositions.
    """
    catalog_file = "output/compositions/demo_catalog.json"

    # Load catalog
    if not os.path.exists(catalog_file):
        print(f"Error: Catalog not found at {catalog_file}")
        print("Run generate_demo_compositions.py first!")
        return

    with open(catalog_file, 'r') as f:
        catalog = json.load(f)

    print("=" * 70)
    print("COMPOSITION EVALUATION SESSION")
    print("=" * 70)
    print(f"\nFound {len(catalog)} compositions to evaluate.")
    print("\nCommands:")
    print("  [Enter] - Play composition")
    print("  r - Replay current composition")
    print("  s - Skip to next")
    print("  q - Quit and save")
    print("  Rating: 1-5 stars")
    print("  Notes: Type any text")
    print()

    current_idx = 0
    ratings = {}

    while current_idx < len(catalog):
        entry = catalog[current_idx]
        comp_id = entry["id"]
        midi_file = entry["filename"]
        audio_file = midi_file.replace("/compositions/", "/audio/").replace(".mid", ".wav")

        # Check if audio exists
        if not os.path.exists(audio_file):
            print(f"\n⚠️  Audio file not found: {audio_file}")
            print("   Run: python3 render_audio.py")
            break

        print("\n" + "=" * 70)
        print(f"Composition #{comp_id:02d} / {len(catalog)}")
        print("=" * 70)
        print(f"File: {Path(midi_file).name}")
        print(f"Seed: {entry['seed']}")
        if entry.get("notes"):
            print(f"Previous notes: {entry['notes']}")
        if comp_id in ratings:
            print(f"Previous rating: {ratings[comp_id]['rating']} stars")

        # Play automatically
        print(f"\n🎵 Playing...")
        play_composition(audio_file)

        # Get user input
        while True:
            user_input = input(f"\nAction [Enter=next, r=replay, s=skip, q=quit]: ").strip()

            if user_input == '':
                # Next composition
                break
            elif user_input.lower() == 'r':
                # Replay
                print(f"🎵 Replaying...")
                play_composition(audio_file)
            elif user_input.lower() == 's':
                # Skip
                break
            elif user_input.lower() == 'q':
                # Quit and save
                print("\nSaving and exiting...")
                save_ratings(catalog, ratings, catalog_file)
                return
            elif user_input.isdigit() and 1 <= int(user_input) <= 5:
                # Rating
                rating = int(user_input)
                notes = input("Notes (optional): ").strip()
                ratings[comp_id] = {
                    "rating": rating,
                    "notes": notes,
                    "filename": midi_file
                }
                entry["rating"] = rating
                entry["notes"] = notes
                print(f"✓ Rated {rating} stars")
                break
            else:
                # Treat as notes
                if comp_id not in ratings:
                    ratings[comp_id] = {"rating": 0, "notes": "", "filename": midi_file}
                ratings[comp_id]["notes"] += " " + user_input
                entry["notes"] = ratings[comp_id]["notes"]
                print(f"✓ Note added")

        current_idx += 1

    # Save at the end
    save_ratings(catalog, ratings, catalog_file)

    # Show summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    rated = [r for r in ratings.values() if r.get("rating", 0) > 0]
    if rated:
        rated_sorted = sorted(rated, key=lambda x: x["rating"], reverse=True)
        print(f"\nTop rated compositions:")
        for i, comp in enumerate(rated_sorted[:5], 1):
            print(f"{i}. {Path(comp['filename']).stem} - {comp['rating']} stars")
            if comp.get("notes"):
                print(f"   Notes: {comp['notes']}")

    print(f"\nTotal rated: {len(rated)}/{len(catalog)}")
    print(f"Ratings saved to: {catalog_file}")


def save_ratings(catalog, ratings, catalog_file):
    """Save updated catalog with ratings."""
    # Update catalog with ratings
    for entry in catalog:
        comp_id = entry["id"]
        if comp_id in ratings:
            entry["rating"] = ratings[comp_id].get("rating", 0)
            entry["notes"] = ratings[comp_id].get("notes", "")

    # Save
    with open(catalog_file, 'w') as f:
        json.dump(catalog, f, indent=2)

    print(f"✓ Saved ratings to {catalog_file}")


def show_top_rated(n: int = 5):
    """Show top N rated compositions."""
    catalog_file = "output/compositions/demo_catalog.json"

    if not os.path.exists(catalog_file):
        print(f"Error: Catalog not found")
        return

    with open(catalog_file, 'r') as f:
        catalog = json.load(f)

    rated = [c for c in catalog if c.get("rating", 0) > 0]
    if not rated:
        print("No rated compositions yet. Run listen_and_evaluate() first.")
        return

    rated_sorted = sorted(rated, key=lambda x: x["rating"], reverse=True)

    print("=" * 70)
    print(f"TOP {n} COMPOSITIONS")
    print("=" * 70)

    for i, comp in enumerate(rated_sorted[:n], 1):
        print(f"\n{i}. {Path(comp['filename']).stem}")
        print(f"   Rating: {comp['rating']} stars")
        print(f"   File: {comp['filename']}")
        if comp.get("notes"):
            print(f"   Notes: {comp['notes']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "top":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        show_top_rated(n)
    else:
        listen_and_evaluate()
