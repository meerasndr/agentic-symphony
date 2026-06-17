# Agentic Symphony - Quick Reference Guide

**Quick command reference for generating and rendering musical compositions.**

---

## 🎵 Generate Compositions

### Live Terminal UI (Recommended for Demos) ✨ NEW!

**Real-time visualization showing agent decisions as they happen!**

```bash
# Generate with live terminal visualization
python3 live_compose.py

# Interactive mode - prompts to render and play audio after generation 🎧
python3 live_compose.py --interactive
python3 live_compose.py -i  # short form

# Quick 8-bar demo with interactive workflow
python3 live_compose.py --bars 8 --preset minimal -i

# Full 16-bar with LLM (default)
python3 live_compose.py --bars 16 --preset default --interactive

# Long dramatic composition
python3 live_compose.py --bars 24 --preset dramatic

# Compare LLM vs rules
python3 live_compose.py --preset llm_heavy --seed 1234  # 70% LLM
python3 live_compose.py --preset pure_rules --seed 1234 # 0% LLM

# List all presets
python3 live_compose.py --list-presets
```

**Features:**
- 🎨 Beautiful color-coded agent panels
- 🤖 Shows LLM decisions with reasoning
- 📏 Shows rule-based fallback decisions
- 📊 Real-time intensity arc visualization
- ⚡ Live statistics (LLM calls, success rate)
- 🎧 **NEW:** Interactive mode prompts to render and play audio automatically!

**Interactive Mode Workflow:**
1. Generate composition with live visualization
2. Prompt: "🎧 Render to audio? [Y/n]"
3. If yes, automatically renders to .wav
4. Prompt: "🔊 Play audio? [Y/n]"
5. If yes, plays audio immediately

**See:** `LIVE_TERMINAL_UI.md` for full documentation

### Quick CLI Generation

```bash
# Fast generation with command-line options
python3 compose.py                           # Default preset
python3 compose.py --preset dramatic         # 24 bars
python3 compose.py --bars 32 --llm           # 32 bars with LLM
python3 compose.py --seed 5678               # Reproducible
python3 compose.py --list                    # List presets
```

**See:** `CONFIGURATION_INTERFACE.md` for details

### Interactive Configuration

```bash
# Menu-driven interface for tweaking parameters
python3 interactive_compose.py
```

**Features:**
- Load/save presets
- Tweak all agent parameters
- Configure LLM usage
- Generate with current settings

### Test Individual Agents

```bash
# Activate venv and set PYTHONPATH
source .venv/bin/activate

# Test MIDI pipeline (C major scale)
PYTHONPATH=. python3 tests/test_midi.py

# Test harmonic agent only (chord progressions)
PYTHONPATH=. python3 tests/test_harmonic.py [num_bars]

# Test harmonic + melodic agents
PYTHONPATH=. python3 tests/test_harmony_melody.py [num_bars]

# Test harmonic + melodic + rhythmic agents
PYTHONPATH=. python3 tests/test_three_agents.py [num_bars]

# Test ALL FOUR agents (original batch mode)
PYTHONPATH=. python3 tests/test_four_agents.py [num_bars]
```

**Default:** 16 bars if not specified

**Output:** MIDI files in `output/compositions/`

---

## 🔊 Render to Audio

### Single File (Fast)

```bash
# Render a specific MIDI file to WAV
python3 render_audio.py <midi_file>

# Example:
python3 render_audio.py output/compositions/test_four_agents.mid
```

**Output:** `output/audio/<filename>.wav`

### Batch Rendering

```bash
# Render ALL MIDI files in output/compositions/
python3 render_audio.py
```

**Output:** All WAV files in `output/audio/`

---

## 🎧 Play Audio

```bash
# Play a specific composition
afplay output/audio/test_four_agents.wav

# Or open in default audio player
open output/audio/test_four_agents.wav
```

---

## 🎼 Generate Multiple Compositions

```bash
# Generate multiple compositions at once
python3 generate_multiple.py [count] [bars]

# Examples:
python3 generate_multiple.py 5        # 5 compositions, 16 bars each
python3 generate_multiple.py 10 24    # 10 compositions, 24 bars each
```

**Output:**
- MIDI: `output/compositions/composition_01.mid`, `composition_02.mid`, etc.
- Then render all: `python3 render_audio.py`

---

## 📊 Complete Workflow Examples

### Quick Single Composition

```bash
# 1. Generate (4 agents, 16 bars)
python3 test_four_agents.py

# 2. Render to audio
python3 render_audio.py output/compositions/test_four_agents.mid

# 3. Play
afplay output/audio/test_four_agents.wav
```

### Generate Multiple & Select Best

```bash
# 1. Generate 10 compositions
python3 generate_multiple.py 10

# 2. Render all to audio
python3 render_audio.py

# 3. Listen to each and select favorites
afplay output/audio/composition_01.wav
afplay output/audio/composition_02.wav
# ... etc
```

### Custom Length Composition

```bash
# Generate a 32-bar composition
python3 test_four_agents.py 32

# Render and play
python3 render_audio.py output/compositions/test_four_agents.mid
afplay output/audio/test_four_agents.wav
```

---

## 🎹 Agent Combinations

| Script | Agents Active | Features |
|--------|---------------|----------|
| `test_harmonic.py` | Harmonic | Chord progressions only |
| `test_harmony_melody.py` | Harmonic + Melodic | Chords + melody |
| `test_three_agents.py` | Harmonic + Melodic + Rhythmic | Chords + melody + tempo changes |
| `test_four_agents.py` | **All 4 agents** | **Full system: chords + melody + tempo + dynamics** |

---

## 📁 File Locations

```
output/
├── compositions/          # Generated MIDI files
│   ├── test_four_agents.mid
│   ├── composition_01.mid
│   └── ...
└── audio/                 # Rendered WAV files
    ├── test_four_agents.wav
    ├── composition_01.wav
    └── ...
```

---

## ⚙️ Common Options

### Specify Number of Bars

All test scripts accept an optional bar count:

```bash
python3 test_four_agents.py 24    # 24-bar composition
python3 test_four_agents.py 32    # 32-bar composition
python3 test_four_agents.py 8     # 8-bar composition
```

### Use Specific Python Version

If you need to use the installed Python 3.13:

```bash
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 test_four_agents.py
```

---

## 🚀 Recommended for Demo

**Generate the best compositions for your talk:**

```bash
# 1. Generate 10 full-system compositions
python3 generate_multiple.py 10 16

# 2. Render all to audio (silent, no playback)
python3 render_audio.py

# 3. Listen and select best 3-5
# Play each composition and note which ones sound best
for i in {01..10}; do
    echo "Playing composition $i..."
    afplay output/audio/composition_$i.wav
done

# 4. Keep the best ones for your demo
```

---

## 🎛️ Agent Parameters

To customize agent behavior, edit the agent initialization in test scripts:

**Harmonic Agent:**
- `surprise_rate`: 0.0-1.0 (probability of unexpected chords)
- `chord_duration`: beats per chord (default 4.0)

**Melodic Agent:**
- `variation_rate`: 0.0-1.0 (how often to vary motifs)
- `chord_tone_bias`: 0.0-1.0 (preference for chord tones vs passing tones)

**Rhythmic Agent:**
- `tempo_range`: (min_bpm, max_bpm) (default 75-110)
- `tempo_sensitivity`: 0.0-1.0 (how much intensity affects tempo)

**Textural Agent:**
- `pause_probability`: 0.0-1.0 (chance of strategic pauses)
- `dynamic_range`: (min, max) multiplier for velocity

---

## 🐛 Troubleshooting

**MIDI file but no audio?**
```bash
# Check if WAV was created
ls -lh output/audio/

# Render manually
python3 render_audio.py output/compositions/your_file.mid
```

**Can't find python3?**
```bash
which python3
# Use the full path shown above
```

**FluidSynth not found?**
```bash
# Install FluidSynth
brew install fluid-synth
```

**No soundfont?**
```bash
# Check soundfonts directory
ls soundfonts/
# Should contain default.sf2 (or another .sf2 file)
```

---

## 📝 Quick Tips

- **Faster iteration:** Use `test_four_agents.py` with lower bar counts (8-12) while experimenting
- **Best results:** Generate 10+ compositions, select the best 3-5
- **Variety:** Each run produces unique output due to randomness
- **Render only what you need:** Use single-file rendering for quick testing
- **Batch render for selection:** Generate many, render all, then listen and choose

---

## 📚 Documentation

- **LIVE_TERMINAL_UI.md** - Live visualization documentation
- **CONFIGURATION_INTERFACE.md** - Configuration & presets guide
- **PHASE_A_LLM_INTEGRATION.md** - LLM integration details
- **INSTRUMENT_SELECTION_SUMMARY.md** - Agent-driven instrument selection
- **visualization_options.md** - Visualization options analysis

---

**Last updated:** March 25, 2026 - Live Terminal UI, LLM Integration, Configuration System
