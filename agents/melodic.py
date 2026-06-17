"""
Melodic Agent - Creates melodies that follow the harmonic progression.

Can use LLM reasoning for motif development decisions (Phase A: LLM Integration).
"""

import random
from typing import List, Dict, Any, Optional
from agents.llm_enhanced_base import LLMEnhancedAgent
from core.context import MusicalContext
from core.music_theory import get_chord_notes_from_symbol, get_scale


class MelodicAgent(LLMEnhancedAgent):
    """
    Agent responsible for generating melodies.

    Creates melodic motifs, develops them through repetition and variation,
    and ensures melodies follow the underlying harmony.
    """

    # Rhythmic patterns (durations in beats)
    RHYTHMIC_PATTERNS = [
        [1.0, 1.0, 1.0, 1.0],           # Four quarter notes
        [0.5, 0.5, 1.0, 0.5, 0.5, 1.0], # Eighth note patterns
        [1.0, 0.5, 0.5, 2.0],           # Mixed durations
        [2.0, 1.0, 1.0],                # Half and quarters
        [0.5, 0.5, 0.5, 0.5, 2.0],      # Quick start, long end
    ]

    # Melodic contour patterns (relative pitch movements)
    CONTOUR_PATTERNS = [
        [0, 1, 2, 1],      # Up and back down
        [0, -1, -2, -1],   # Down and back up
        [0, 2, 1, 3],      # Ascending
        [0, -2, -1, -3],   # Descending
        [0, 1, -1, 0],     # Wave pattern
    ]

    def __init__(self, objectives: Dict[str, Any] = None):
        """
        Initialize the Melodic Agent.

        Args:
            objectives: Agent objectives, including:
                - octave: Starting octave (default 5)
                - motif_length: Number of notes in motif (default 4)
                - variation_rate: Probability of varying motif (default 0.5)
                - chord_tone_bias: Preference for chord tones vs passing tones (default 0.7)
                - llm_frequency: Probability of using LLM (default 0.3 = 30%)
        """
        llm_freq = objectives.get("llm_frequency", 0.3) if objectives else 0.3
        super().__init__(role="melodic", objectives=objectives, llm_frequency=llm_freq)

        self.octave = self.objectives.get("octave", 5)
        self.motif_length = self.objectives.get("motif_length", 4)
        self.variation_rate = self.objectives.get("variation_rate", 0.5)
        self.chord_tone_bias = self.objectives.get("chord_tone_bias", 0.7)

        # Current motif
        self.current_motif: Optional[List[int]] = None
        self.motif_repetitions = 0
        self.max_repetitions = 3

        # Track last instrument sent (to avoid duplicate program changes)
        self.last_instrument = None

    def listen(self, context: MusicalContext) -> Dict[str, Any]:
        """
        Analyze the current harmonic and musical state.

        Args:
            context: The shared musical context

        Returns:
            Dictionary with:
                - current_chord: Current chord symbol
                - chord_notes: MIDI notes in current chord
                - harmonic_tension: Current tension level
                - intensity: Musical intensity
                - measure_position: Position in measure
        """
        # Get available chord tones
        chord_notes = get_chord_notes_from_symbol(context.current_chord, self.octave)

        # Get scale notes for passing tones
        scale_notes = get_scale(context.current_key, "major", self.octave)

        return {
            "current_chord": context.current_chord,
            "chord_notes": chord_notes,
            "scale_notes": scale_notes,
            "harmonic_tension": context.harmonic_tension,
            "intensity": context.intensity,
            "measure_position": context.measure_position,
            "current_measure": context.current_measure
        }

    def llm_decide_motif_action(self, context: MusicalContext) -> Optional[str]:
        """
        Use LLM to decide how to handle motif development.

        Args:
            context: Musical context

        Returns:
            One of: "repeat", "transpose", "invert", "new", or None if LLM fails
        """
        # Get current musical context
        current_chord = context.current_chord
        intensity = context.intensity
        tension = context.harmonic_tension
        measure = context.current_measure

        # Get motif history
        last_decision = self.memory[-1] if self.memory else None
        motif_info = "none"
        if last_decision and "variation_type" in last_decision:
            motif_info = last_decision["variation_type"]

        # Construct prompt
        prompt = f"""You are a melodic decision-making agent in a multi-agent music composition system.

Current musical state:
- Chord: {current_chord}
- Intensity: {intensity:.2f} (0.0 = calm, 1.0 = climactic)
- Harmonic tension: {tension:.2f} (0.0 = consonant, 1.0 = dissonant)
- Measure number: {measure}
- Previous action: {motif_info}

Your goal: Decide how to develop the melody at this moment.

Options:
1. "repeat" - Play a similar motif again (creates unity, familiarity)
2. "transpose" - Move the motif to fit current chord (development, coherence)
3. "invert" - Mirror the intervals of the motif (variation, interest)
4. "new" - Create a contrasting new motif (surprise, fresh idea)

Guidelines:
- Early in piece (measures 0-7): Establish motifs, prefer "repeat" or "transpose"
- Middle section (measures 8-15): Develop and vary, prefer "transpose" or "invert"
- High intensity/tension (>0.7): Consider "new" for dramatic effect
- Low intensity (<0.3): Prefer "repeat" for stability
- If no previous motif exists: Must choose "new"

Return ONLY valid JSON in this exact format:
{{"action": "repeat|transpose|invert|new", "reasoning": "brief explanation"}}"""

        response = self.call_llm(prompt)

        if response and "action" in response:
            action = response["action"]
            reasoning = response.get("reasoning", "")

            # Validate response
            if action in ["repeat", "transpose", "invert", "new"]:
                print(f"  🤖 LLM melodic decision: {action} - {reasoning}")
                return action

        return None  # LLM failed, use rule-based fallback

    def _llm_decide_with_reasoning(self, context: MusicalContext) -> Optional[Dict[str, str]]:
        """
        Use LLM to decide motif action and return both action and reasoning.

        Args:
            context: Musical context

        Returns:
            Dictionary with "action" and "reasoning" keys, or None if LLM fails
        """
        # Get current musical context
        current_chord = context.current_chord
        intensity = context.intensity
        tension = context.harmonic_tension
        measure = context.current_measure

        # Get motif history
        last_decision = self.memory[-1] if self.memory else None
        motif_info = "none"
        if last_decision and "variation_type" in last_decision:
            motif_info = last_decision["variation_type"]

        # Construct prompt
        prompt = f"""You are a melodic decision-making agent in a multi-agent music composition system.

Current musical state:
- Chord: {current_chord}
- Intensity: {intensity:.2f} (0.0 = calm, 1.0 = climactic)
- Harmonic tension: {tension:.2f} (0.0 = consonant, 1.0 = dissonant)
- Measure number: {measure}
- Previous action: {motif_info}

Your goal: Decide how to develop the melody at this moment.

Options:
1. "repeat" - Play a similar motif again (creates unity, familiarity)
2. "transpose" - Move the motif to fit current chord (development, coherence)
3. "invert" - Mirror the intervals of the motif (variation, interest)
4. "new" - Create a contrasting new motif (surprise, fresh idea)

Guidelines:
- Early in piece (measures 0-7): Establish motifs, prefer "repeat" or "transpose"
- Middle section (measures 8-15): Develop and vary, prefer "transpose" or "invert"
- High intensity/tension (>0.7): Consider "new" for dramatic effect
- Low intensity (<0.3): Prefer "repeat" for stability
- If no previous motif exists: Must choose "new"

Return ONLY valid JSON in this exact format:
{{"action": "repeat|transpose|invert|new", "reasoning": "brief explanation"}}"""

        response = self.call_llm(prompt)

        if response and "action" in response:
            action = response["action"]
            reasoning = response.get("reasoning", "")

            # Validate response
            if action in ["repeat", "transpose", "invert", "new"]:
                return {"action": action, "reasoning": reasoning}

        return None  # LLM failed

    def _get_rule_reasoning(self, action: str, context: MusicalContext) -> str:
        """
        Generate reasoning text for rule-based decisions.

        Args:
            action: The action taken
            context: Musical context

        Returns:
            Brief explanation of why this action was chosen
        """
        if action == "new":
            if self.current_motif is None:
                return "No existing motif - creating fresh melodic material"
            elif self.motif_repetitions >= self.max_repetitions:
                return f"Motif repeated {self.max_repetitions}x - introducing new idea"
            else:
                return "High intensity/tension suggests fresh melodic material"

        elif action == "repeat":
            return f"Low intensity ({context.intensity:.2f}) - maintaining stability"

        elif action == "transpose":
            return f"Moderate intensity - developing motif for {context.current_chord}"

        elif action == "invert":
            return f"Adding variation through interval inversion"

        return "Continuing melodic development"

    def decide(self, analysis: Dict[str, Any], context: MusicalContext) -> Dict[str, Any]:
        """
        Decide what melodic phrase to play (with optional LLM reasoning).

        Args:
            analysis: Analyzed features
            context: Musical context

        Returns:
            Decision dictionary with:
                - notes: List of MIDI note numbers
                - durations: List of durations in beats
                - is_new_motif: Whether this is a new motif
                - variation_type: Type of variation applied (if any)
                - action: The action taken (new/transpose/invert/repeat)
                - source: Decision source ("llm" or "rule")
                - reasoning: Explanation of decision (if from LLM)
        """
        chord_notes = analysis["chord_notes"]
        scale_notes = analysis["scale_notes"]
        tension = analysis["harmonic_tension"]

        # Try LLM decision if enabled
        action = None
        reasoning = ""
        source = "rule"

        if self.should_use_llm():
            llm_response = self._llm_decide_with_reasoning(context)
            if llm_response:
                action = llm_response["action"]
                reasoning = llm_response.get("reasoning", "")
                source = "llm"
                print(f"  🤖 LLM melodic decision: {action} - {reasoning}")

        # Fallback to rule-based if LLM failed or not used
        if action is None:
            action = self._rule_based_action(context)
            source = "rule"
            reasoning = self._get_rule_reasoning(action, context)
            print(f"  📏 Rule-based decision: {action}")

        # Execute the chosen action to generate notes
        if action == "new" or self.current_motif is None:
            notes = self._generate_new_motif(chord_notes, scale_notes, tension)
            self.current_motif = notes
            self.motif_repetitions = 0
            is_new = True
            variation_type = "new"
        elif action == "transpose":
            notes = self._transpose_motif_to_chord(self.current_motif, chord_notes)
            self.motif_repetitions += 1
            is_new = False
            variation_type = "transpose"
        elif action == "invert":
            notes = self._invert_motif(self.current_motif, chord_notes)
            self.motif_repetitions += 1
            is_new = False
            variation_type = "invert"
        elif action == "repeat":
            notes = self._transpose_motif_to_chord(self.current_motif, chord_notes)
            self.motif_repetitions += 1
            is_new = False
            variation_type = "repeat"
        else:
            # Safety fallback (shouldn't happen)
            notes = self._generate_new_motif(chord_notes, scale_notes, tension)
            self.current_motif = notes
            self.motif_repetitions = 0
            is_new = True
            variation_type = "new"

        # Choose rhythmic pattern based on intensity
        if context.intensity > 0.7:
            # High intensity: faster rhythms
            durations = self.RHYTHMIC_PATTERNS[1]  # Eighth notes
        elif context.intensity < 0.3:
            # Low intensity: slower rhythms
            durations = self.RHYTHMIC_PATTERNS[3]  # Half and quarters
        else:
            # Medium intensity: mixed
            durations = random.choice(self.RHYTHMIC_PATTERNS)

        # Ensure we have enough durations for all notes
        while len(durations) < len(notes):
            durations = durations + durations

        durations = durations[:len(notes)]

        return {
            "notes": notes,
            "durations": durations,
            "is_new_motif": is_new,
            "variation_type": variation_type,
            "action": action,
            "source": source,
            "reasoning": reasoning,
            "measure": context.current_measure
        }

    def _rule_based_action(self, context: MusicalContext) -> str:
        """
        Rule-based fallback for motif decisions.

        Args:
            context: Musical context

        Returns:
            Action string: "repeat", "transpose", "invert", or "new"
        """
        # Must create new motif if none exists
        if self.current_motif is None:
            return "new"

        # Reset if we've repeated too many times
        if self.motif_repetitions >= self.max_repetitions:
            return "new"

        # Simple heuristics based on intensity and tension
        if context.intensity < 0.3:
            # Low intensity: prefer repetition for stability
            return "repeat"
        elif context.intensity < 0.7:
            # Medium intensity: transpose to develop motif
            return "transpose" if random.random() < 0.7 else "invert"
        else:
            # High intensity: more variety
            if context.harmonic_tension > 0.7:
                # High tension + high intensity: dramatic new motif
                return "new"
            else:
                # High intensity but lower tension: vary existing
                return random.choice(["transpose", "invert"])

    def act(self, decision: Dict[str, Any], context: MusicalContext) -> List[Dict[str, Any]]:
        """
        Generate MIDI events for the melodic phrase.

        Args:
            decision: Decision from decide()
            context: Musical context (will be updated)

        Returns:
            List of MIDI events
        """
        notes = decision["notes"]
        durations = decision["durations"]

        events = []

        # Check if instrument has changed and send program_change if needed
        current_instrument = context.melodic_instrument
        if current_instrument != self.last_instrument:
            events.append({
                "type": "program_change",
                "program": current_instrument,
                "time": 0.0,
                "channel": 1  # Melodic agent uses channel 1
            })
            self.last_instrument = current_instrument

        current_time = 0.0

        for note, duration in zip(notes, durations):
            # Velocity varies with intensity and slight randomness
            base_velocity = int(60 + context.intensity * 50)  # 60-110
            velocity = max(40, min(127, base_velocity + random.randint(-10, 10)))

            events.append({
                "type": "note_on",
                "note": note,
                "velocity": velocity,
                "time": current_time,
                "duration": duration,
                "channel": 1  # Different channel from harmony
            })

            # Add to context memory
            context.add_note(note, velocity, duration, self.role)

            current_time += duration

        # Calculate melodic tension (feedback signal for harmonic agent)
        # Tension = ratio of non-chord tones to total notes
        from core.music_theory import get_chord_notes_from_symbol

        chord_midi_notes = get_chord_notes_from_symbol(context.current_chord, octave=4)
        # Normalize to pitch classes (0-11) for comparison
        chord_pitch_classes = set(n % 12 for n in chord_midi_notes)

        non_chord_count = 0
        for note in notes:
            note_pitch_class = note % 12
            if note_pitch_class not in chord_pitch_classes:
                non_chord_count += 1

        # Calculate tension ratio
        melodic_tension = non_chord_count / len(notes) if notes else 0.0
        context.melodic_tension = melodic_tension

        # Log high tension for debugging
        if melodic_tension > 0.5:
            print(f"  🔄 Melodic tension: {melodic_tension:.2f} (exploring outside harmony)")

        # Advance time by total duration
        total_duration = sum(durations)
        context.advance_time(total_duration)

        return events

    def _generate_new_motif(
        self,
        chord_notes: List[int],
        scale_notes: List[int],
        tension: float
    ) -> List[int]:
        """
        Generate a new melodic motif.

        Args:
            chord_notes: Available chord tones
            scale_notes: Available scale notes
            tension: Harmonic tension (0.0-1.0)

        Returns:
            List of MIDI note numbers
        """
        notes = []

        # Start with a chord tone for stability
        current_note = random.choice(chord_notes)
        notes.append(current_note)

        # Generate remaining notes
        for _ in range(self.motif_length - 1):
            # Decide: chord tone or passing tone?
            use_chord_tone = random.random() < self.chord_tone_bias

            if use_chord_tone:
                # Move to nearby chord tone
                available = [n for n in chord_notes if abs(n - current_note) <= 7]
                if available:
                    current_note = random.choice(available)
                else:
                    current_note = random.choice(chord_notes)
            else:
                # Use passing tone from scale
                available = [n for n in scale_notes if abs(n - current_note) <= 4]
                if available:
                    current_note = random.choice(available)

            notes.append(current_note)

        # End on a chord tone for resolution
        if notes[-1] not in chord_notes:
            notes[-1] = min(chord_notes, key=lambda n: abs(n - notes[-1]))

        return notes

    def _vary_motif(
        self,
        motif: List[int],
        chord_notes: List[int],
        scale_notes: List[int],
        tension: float
    ) -> tuple[str, List[int]]:
        """
        Apply variation to an existing motif.

        Args:
            motif: Original motif
            chord_notes: Current chord notes
            scale_notes: Current scale notes
            tension: Harmonic tension

        Returns:
            Tuple of (variation_type, varied_notes)
        """
        variation_type = random.choice([
            "transpose",
            "invert",
            "retrograde",
            "augment",
            "ornament"
        ])

        if variation_type == "transpose":
            # Transpose to fit current chord
            notes = self._transpose_motif_to_chord(motif, chord_notes)
        elif variation_type == "invert":
            # Invert the melodic contour
            notes = self._invert_motif(motif, chord_notes)
        elif variation_type == "retrograde":
            # Play backwards
            notes = motif[::-1]
        elif variation_type == "augment":
            # Add passing tones between notes
            notes = self._augment_motif(motif, scale_notes)
        else:  # ornament
            # Add ornamental notes
            notes = self._ornament_motif(motif, scale_notes)

        return variation_type, notes

    def _transpose_motif_to_chord(self, motif: List[int], chord_notes: List[int]) -> List[int]:
        """
        Transpose motif to fit current chord.

        Args:
            motif: Original motif notes
            chord_notes: Target chord notes

        Returns:
            Transposed notes
        """
        if not motif or not chord_notes:
            return motif

        # Find closest chord tone to first note
        first_note = motif[0]
        target_root = min(chord_notes, key=lambda n: abs(n - first_note))
        transposition = target_root - first_note

        # Transpose all notes
        transposed = [note + transposition for note in motif]

        # Quantize to scale/chord tones where possible
        result = []
        for note in transposed:
            # Keep within reasonable range
            note = max(48, min(84, note))
            result.append(note)

        return result

    def _invert_motif(self, motif: List[int], chord_notes: List[int]) -> List[int]:
        """
        Invert the melodic contour around the first note.

        Args:
            motif: Original motif
            chord_notes: Chord notes for reference

        Returns:
            Inverted motif
        """
        if len(motif) < 2:
            return motif

        pivot = motif[0]
        inverted = [pivot]

        for i in range(1, len(motif)):
            interval = motif[i] - motif[i-1]
            new_note = inverted[-1] - interval  # Invert the interval
            new_note = max(48, min(84, new_note))  # Keep in range
            inverted.append(new_note)

        return inverted

    def _augment_motif(self, motif: List[int], scale_notes: List[int]) -> List[int]:
        """
        Add passing tones between motif notes.

        Args:
            motif: Original motif
            scale_notes: Available scale notes

        Returns:
            Augmented motif
        """
        if len(motif) < 2:
            return motif

        augmented = [motif[0]]

        for i in range(1, len(motif)):
            prev_note = motif[i-1]
            curr_note = motif[i]

            # If there's a leap, add a passing tone
            if abs(curr_note - prev_note) > 2:
                passing = (prev_note + curr_note) // 2
                # Find closest scale tone
                passing = min(scale_notes, key=lambda n: abs(n - passing))
                augmented.append(passing)

            augmented.append(curr_note)

        return augmented

    def _ornament_motif(self, motif: List[int], scale_notes: List[int]) -> List[int]:
        """
        Add ornamental notes (neighbor tones, etc.).

        Args:
            motif: Original motif
            scale_notes: Available scale notes

        Returns:
            Ornamented motif
        """
        if len(motif) < 2:
            return motif

        ornamented = []

        for note in motif:
            # 50% chance to add neighbor tone before the note
            if random.random() < 0.5 and scale_notes:
                neighbor = min(scale_notes, key=lambda n: abs(n - (note + 1)))
                ornamented.append(neighbor)

            ornamented.append(note)

        return ornamented[:self.motif_length * 2]  # Don't make it too long

    def reset(self):
        """Reset the agent to initial state."""
        super().reset()
        self.current_motif = None
        self.motif_repetitions = 0
