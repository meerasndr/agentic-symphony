"""
Composition Visualizer

Creates visual representations of agent decisions and musical parameters
for understanding and demonstrating the multi-agent system.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import sys


def parse_generation_log(log_file):
    """
    Parse generation output to extract agent decisions.

    For now, returns dummy data. In full implementation,
    would parse test_four_agents.py output or agent memory.
    """
    # This would parse actual log data
    # For demo purposes, returning example structure
    return {
        "measures": 16,
        "harmonic_decisions": [
            {"measure": 0, "chord": "C", "is_surprise": False},
            {"measure": 1, "chord": "Am", "is_surprise": False},
            {"measure": 2, "chord": "F", "is_surprise": False},
            {"measure": 3, "chord": "G", "is_surprise": False},
            # ... more
        ],
        "melodic_decisions": [
            {"measure": 0, "action": "new", "source": "rule"},
            {"measure": 1, "action": "transpose", "source": "llm"},
            {"measure": 2, "action": "repeat", "source": "rule"},
            # ... more
        ],
        "intensity": [0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.8, 0.75, 0.7, 0.6, 0.5, 0.45, 0.4, 0.35, 0.3, 0.3],
        "tempo": [90, 92, 94, 96, 98, 100, 100, 98, 96, 94, 92, 90, 88, 88, 88, 90],
        "dynamics": ["mp", "mp", "mf", "mf", "mf", "f", "f", "f", "mf", "mf", "mp", "mp", "mp", "p", "p", "pp"],
        "voice_density": [2, 2, 3, 3, 3, 4, 4, 4, 3, 3, 2, 2, 2, 1, 1, 1]
    }


def create_timeline_visualization(data, output_file="output/visualizations/timeline.png"):
    """Create timeline showing agent decisions."""
    measures = data["measures"]

    fig, axes = plt.subplots(4, 1, figsize=(16, 10), sharex=True)
    fig.suptitle("Agentic Symphony - Agent Decision Timeline", fontsize=16, fontweight='bold')

    # 1. Harmonic Agent
    ax = axes[0]
    chords = data.get("harmonic_decisions", [])
    chord_names = [d["chord"] for d in chords[:measures]]
    x_pos = range(len(chord_names))

    ax.bar(x_pos, [1]*len(chord_names), color='steelblue', alpha=0.7)
    for i, chord in enumerate(chord_names):
        ax.text(i, 0.5, chord, ha='center', va='center', fontsize=12, fontweight='bold')
    ax.set_ylabel("Harmonic\nAgent", fontsize=11, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.grid(axis='x', alpha=0.3)
    ax.set_title("Chord Progression", fontsize=10, loc='left')

    # 2. Melodic Agent
    ax = axes[1]
    melodic = data.get("melodic_decisions", [])[:measures]

    colors = []
    labels = []
    for d in melodic:
        if d.get("source") == "llm":
            colors.append('cornflowerblue')
            labels.append(f"{d['action']}\n🤖")
        else:
            colors.append('lightgreen')
            labels.append(f"{d['action']}\n📏")

    x_pos = range(len(melodic))
    ax.bar(x_pos, [1]*len(melodic), color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    for i, label in enumerate(labels):
        ax.text(i, 0.5, label, ha='center', va='center', fontsize=9)
    ax.set_ylabel("Melodic\nAgent", fontsize=11, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.grid(axis='x', alpha=0.3)
    ax.set_title("Motif Development (🤖 = LLM, 📏 = Rules)", fontsize=10, loc='left')

    # 3. Rhythmic Agent (Tempo)
    ax = axes[2]
    tempo = data.get("tempo", [])[:measures]
    x_pos = range(len(tempo))

    ax.plot(x_pos, tempo, marker='o', color='coral', linewidth=2, markersize=6)
    ax.fill_between(x_pos, tempo, alpha=0.3, color='coral')
    ax.set_ylabel("Tempo\n(BPM)", fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_title("Tempo Evolution", fontsize=10, loc='left')
    ax.set_ylim(min(tempo) - 5, max(tempo) + 5)

    # 4. Textural Agent
    ax = axes[3]
    density = data.get("voice_density", [])[:measures]
    dynamics = data.get("dynamics", [])[:measures]

    x_pos = range(len(density))
    bars = ax.bar(x_pos, density, color='mediumpurple', alpha=0.7, edgecolor='black', linewidth=0.5)

    # Add dynamic markings as text
    for i, (d, dyn) in enumerate(zip(density, dynamics)):
        ax.text(i, d + 0.1, dyn, ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_ylabel("Voice\nDensity", fontsize=11, fontweight='bold')
    ax.set_xlabel("Measure Number", fontsize=12, fontweight='bold')
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4])
    ax.grid(axis='y', alpha=0.3)
    ax.set_title("Voice Density & Dynamics", fontsize=10, loc='left')

    # Set x-axis for all
    plt.xticks(range(measures), range(measures))

    plt.tight_layout()

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Timeline visualization saved: {output_file}")

    return fig


def create_intensity_arc_visualization(data, output_file="output/visualizations/intensity_arc.png"):
    """Create visualization of the dramatic intensity arc."""
    measures = data["measures"]
    intensity = data.get("intensity", [])[:measures]
    tempo = data.get("tempo", [])[:measures]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    fig.suptitle("Dramatic Arc - Intensity & Tempo Evolution", fontsize=16, fontweight='bold')

    x_pos = range(len(intensity))

    # Intensity arc
    ax1.plot(x_pos, intensity, marker='o', color='darkred', linewidth=3, markersize=8, label='Intensity')
    ax1.fill_between(x_pos, intensity, alpha=0.3, color='darkred')
    ax1.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='High intensity threshold')
    ax1.axhline(y=0.3, color='blue', linestyle='--', alpha=0.5, label='Low intensity threshold')
    ax1.set_ylabel("Intensity", fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    ax1.set_title("Musical Intensity (Drives agent decisions)", fontsize=11, loc='left')

    # Tempo evolution
    ax2.plot(x_pos, tempo, marker='s', color='darkgreen', linewidth=3, markersize=8, label='Tempo (BPM)')
    ax2.fill_between(x_pos, tempo, alpha=0.3, color='darkgreen')
    ax2.set_ylabel("Tempo (BPM)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Measure Number", fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    ax2.set_title("Tempo Response (Rhythmic agent adapts to intensity)", fontsize=11, loc='left')
    ax2.set_ylim(min(tempo) - 10, max(tempo) + 10)

    plt.xticks(range(measures), range(measures))
    plt.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ Intensity arc visualization saved: {output_file}")

    return fig


def create_llm_stats_visualization(melodic_data, output_file="output/visualizations/llm_stats.png"):
    """Create visualization of LLM vs rule-based decisions."""

    llm_count = sum(1 for d in melodic_data if d.get("source") == "llm")
    rule_count = sum(1 for d in melodic_data if d.get("source") == "rule")
    total = llm_count + rule_count

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("LLM vs Rule-Based Decision Making", fontsize=16, fontweight='bold')

    # Pie chart
    sizes = [llm_count, rule_count]
    labels = [f'🤖 LLM\n({llm_count} decisions)', f'📏 Rules\n({rule_count} decisions)']
    colors = ['cornflowerblue', 'lightgreen']
    explode = (0.05, 0)

    ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
            shadow=True, startangle=90, textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax1.set_title("Decision Distribution", fontsize=13, fontweight='bold')

    # Bar chart by action type
    actions = {}
    for d in melodic_data:
        action = d.get("action", "unknown")
        source = d.get("source", "rule")
        if action not in actions:
            actions[action] = {"llm": 0, "rule": 0}
        actions[action][source] += 1

    action_names = list(actions.keys())
    llm_counts = [actions[a]["llm"] for a in action_names]
    rule_counts = [actions[a]["rule"] for a in action_names]

    x = range(len(action_names))
    width = 0.35

    ax2.bar([i - width/2 for i in x], llm_counts, width, label='🤖 LLM', color='cornflowerblue')
    ax2.bar([i + width/2 for i in x], rule_counts, width, label='📏 Rules', color='lightgreen')

    ax2.set_xlabel("Motif Action", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Count", fontsize=12, fontweight='bold')
    ax2.set_title("Decisions by Action Type", fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(action_names)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✓ LLM stats visualization saved: {output_file}")

    return fig


def create_all_visualizations(log_file=None):
    """Create all visualizations for a composition."""
    print("\n" + "="*70)
    print("CREATING COMPOSITION VISUALIZATIONS")
    print("="*70)

    # Parse data (currently using dummy data)
    data = parse_generation_log(log_file)

    # Create visualizations
    print("\nGenerating visualizations...")
    create_timeline_visualization(data)
    create_intensity_arc_visualization(data)
    create_llm_stats_visualization(data.get("melodic_decisions", []))

    print("\n" + "="*70)
    print("✅ ALL VISUALIZATIONS CREATED")
    print("="*70)
    print("\nOutput files:")
    print("  - output/visualizations/timeline.png")
    print("  - output/visualizations/intensity_arc.png")
    print("  - output/visualizations/llm_stats.png")
    print("\nUse these in your presentation slides!")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = None

    create_all_visualizations(log_file)


if __name__ == "__main__":
    main()
