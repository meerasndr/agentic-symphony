# Agentic Symphony

A multi-agent system where four autonomous agents (Harmonic, Melodic, Rhythmic, Textural) collaborate in real-time to create emergent musical compositions.

**Target:** ADCx India 26 talk on March 29, 2026

## Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt --break-system-packages

# Install FluidSynth (for audio rendering)
# macOS:
brew install fluid-synth

# Ubuntu/Debian:
sudo apt-get install fluidsynth

# Windows:
# Download from https://www.fluidsynth.org/
```

### 2. Get a Soundfont

Download a soundfont (.sf2 file) and place it in the `soundfonts/` directory:

**Recommended soundfonts:**
- [MuseScore General](https://github.com/musescore/MuseScore/tree/master/share/sound) - High quality, free
- [FluidR3_GM](http://www.musescore.org/download/fluid-soundfont.tar.gz) - Classic, lightweight
- [GeneralUser GS](https://schristiancollins.com/generaluser.php) - Comprehensive

```bash
# Example: Download MuseScore General (if available as .sf2)
cd soundfonts/
# Download your chosen soundfont here
ln -s your-soundfont.sf2 default.sf2  # Create a default link
```

### 3. Test MIDI Generation

```bash
# Run the test to verify MIDI generation works
python3 test_midi.py
# or use the specific python version:
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 test_midi.py

# This will create: output/compositions/test_c_major.mid
```

### 4. Render to Audio

```bash
# Render a specific MIDI file
fluidsynth -ni soundfonts/default.sf2 output/compositions/test_c_major.mid -F output/test.wav -r 44100

# Or use the helper script to render all MIDI files
python3 render_audio.py
```

## Repository Structure

```
agentic-symphony/
├── agents/                    # Musical agent implementations
│   ├── base.py               # Base MusicalAgent class
│   ├── harmonic.py           # Chord progression agent
│   ├── melodic.py            # Melody generation agent (LLM-enhanced)
│   ├── rhythmic.py           # Rhythm and tempo agent
│   ├── textural.py           # Dynamics and texture agent
│   └── llm_enhanced_base.py  # LLM integration base class
├── core/                     # Core system components
│   ├── context.py            # Shared MusicalContext
│   └── music_theory.py       # Music theory utilities
├── config/                   # Configuration files
│   └── presets.json          # Composition presets
├── docs/                     # 📚 All documentation
│   ├── LIVE_TERMINAL_UI.md                    # Live visualization guide
│   ├── CONFIGURATION_INTERFACE.md             # Configuration & presets
│   ├── PHASE_A_LLM_INTEGRATION.md             # LLM integration details
│   ├── TERMINAL_UI_IMPLEMENTATION_SUMMARY.md  # UI implementation
│   ├── INSTRUMENT_SELECTION_SUMMARY.md        # Instrument selection
│   ├── abstract.md                            # Talk abstract
│   ├── talk_outline.md                        # Talk outline
│   └── ... (other docs)
├── output/
│   ├── compositions/         # Generated MIDI files
│   ├── audio/               # Rendered audio files
│   └── visualizations/      # PNG visualizations
├── soundfonts/              # .sf2 soundfont files
├── tests/                   # Test scripts
│   ├── test_midi.py         # Basic MIDI pipeline test
│   ├── test_harmonic.py     # Harmonic agent test
│   ├── test_harmony_melody.py # Two agents test
│   ├── test_three_agents.py # Three agents test
│   └── test_four_agents.py  # Full system test (RECOMMENDED)
├── archive/                 # Archived utilities (not needed for talk)
│   ├── visualize_composition.py  # Static PNG visualizations
│   └── listen_and_evaluate.py    # Composition evaluation tool
├── live_compose.py          # ✨ Live terminal UI (RECOMMENDED)
├── compose.py               # Quick CLI generation
├── interactive_compose.py   # Interactive configuration
├── render_audio.py          # Audio rendering
├── generate_demo_compositions.py # Batch composition generation
├── README.md                # This file
└── QUICK_REFERENCE.md       # Quick command reference
```

## Architecture

### Four Specialized Agents

1. **Harmonic Agent** - Generates chord progressions using weighted Markov chains
2. **Melodic Agent** - Creates melodies that follow the harmony
3. **Rhythmic Agent** - Controls tempo and rhythmic patterns
4. **Textural Agent** - Manages dynamics and voice density

### Communication

Agents share a `MusicalContext` object containing:
- Current key, chord, and chord notes
- Tempo and time signature
- Measure position and number
- Intensity and harmonic tension
- Recent notes (for memory)

### Execution Model

Sequential execution: Harmonic → Melodic → Rhythmic → Textural

Each agent:
1. Reads the current musical state
2. Makes a decision based on its role
3. Updates the shared context
4. Generates MIDI events

## Usage

**See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for detailed command reference.**

### Quick Start - Generate a Composition

```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate

# EASIEST: Live UI with interactive mode (prompts to render & play)
python3 live_compose.py --interactive

# Or use test script for quick generation
PYTHONPATH=. python3 tests/test_four_agents.py

# Manual render to audio (if not using interactive mode)
python3 render_audio.py output/compositions/test_four_agents.mid

# Manual play (if not using interactive mode)
afplay output/audio/test_four_agents.wav
```

### Available Test Scripts

```bash
# Test individual components (run from project root with PYTHONPATH set)
PYTHONPATH=. python3 tests/test_midi.py                 # Basic MIDI pipeline
PYTHONPATH=. python3 tests/test_harmonic.py            # Harmonic agent only
PYTHONPATH=. python3 tests/test_harmony_melody.py      # Harmonic + Melodic
PYTHONPATH=. python3 tests/test_three_agents.py        # Harmonic + Melodic + Rhythmic
PYTHONPATH=. python3 tests/test_four_agents.py         # All 4 agents (RECOMMENDED)

# Generate multiple compositions
python3 generate_demo_compositions.py 20 16    # Generate 20 compositions of 16 bars
```

## Resources

- [mido Documentation](https://mido.readthedocs.io/)
- [FluidSynth](https://www.fluidsynth.org/)
- [MIDI Note Numbers](https://www.inspiredacoustics.com/en/MIDI_note_numbers_and_center_frequencies)
- [Music Theory Basics](https://www.musictheory.net/)

## License

MIT License - Created for ADCx India 26 talk
