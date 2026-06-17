"""
LLM-Enhanced Agent Base Class

Provides LLM reasoning capabilities for musical agents with fallback to rule-based decisions.
"""

import os
import anthropic
import json
import random
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from agents.base import MusicalAgent

# Load environment variables
load_dotenv()


class LLMEnhancedAgent(MusicalAgent):
    """
    Base class for agents that can use LLM reasoning.

    Extends MusicalAgent with Claude LLM capabilities while maintaining
    rule-based fallback for reliability.
    """

    def __init__(self, role: str, objectives: Dict[str, Any] = None, llm_frequency: float = 0.3):
        """
        Initialize LLM-enhanced agent.

        Args:
            role: Agent role (e.g., "melodic", "harmonic")
            objectives: Agent objectives dict
            llm_frequency: Probability of using LLM (0.0 to 1.0)
                          0.3 means 30% of decisions use LLM
        """
        super().__init__(role, objectives)
        self.llm_frequency = llm_frequency
        self.llm_enabled = True  # Can be disabled for testing
        self.client = None  # Lazy initialization
        self.llm_call_count = 0
        self.llm_failure_count = 0
        self.llm_success_count = 0

    def _init_llm_client(self):
        """Lazy initialize Anthropic client."""
        if self.client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key or api_key == "your_api_key_here":
                if self.llm_call_count == 0:  # Only warn once
                    print(f"⚠️  WARNING: ANTHROPIC_API_KEY not found or not set")
                    print(f"   {self.role} agent will use rule-based fallback only")
                self.llm_enabled = False
                return
            self.client = anthropic.Anthropic(api_key=api_key)

    def should_use_llm(self) -> bool:
        """Decide whether to use LLM for this decision."""
        if not self.llm_enabled:
            return False
        return random.random() < self.llm_frequency

    def call_llm(self, prompt: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """
        Make LLM call with timeout and error handling.

        Args:
            prompt: The prompt to send to Claude
            timeout: Maximum seconds to wait for response

        Returns:
            Parsed JSON response or None if failed
        """
        self._init_llm_client()

        if not self.llm_enabled:
            return None

        try:
            self.llm_call_count += 1

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,  # Keep responses brief
                temperature=0.7,  # Some creativity, not too random
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                timeout=timeout
            )

            # Extract text content
            text = response.content[0].text

            # Parse JSON (handle markdown code blocks if present)
            text = text.strip()
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("```"):
                text = text.split("```")[1].split("```")[0].strip()

            result = json.loads(text)
            self.llm_success_count += 1
            return result

        except anthropic.APITimeoutError:
            print(f"  ⏱️  LLM timeout for {self.role} agent (>{timeout}s)")
            self.llm_failure_count += 1
            return None

        except anthropic.APIError as e:
            print(f"  ❌ LLM API error for {self.role} agent: {e}")
            self.llm_failure_count += 1
            return None

        except json.JSONDecodeError as e:
            print(f"  ❌ LLM returned invalid JSON for {self.role} agent")
            print(f"     Response text: {text[:100]}...")
            self.llm_failure_count += 1
            return None

        except Exception as e:
            print(f"  ❌ Unexpected error in LLM call for {self.role} agent: {e}")
            self.llm_failure_count += 1
            return None

    def get_llm_stats(self) -> Dict[str, Any]:
        """Return statistics about LLM usage."""
        success_rate = 0.0
        if self.llm_call_count > 0:
            success_rate = self.llm_success_count / self.llm_call_count

        return {
            "total_calls": self.llm_call_count,
            "successes": self.llm_success_count,
            "failures": self.llm_failure_count,
            "success_rate": success_rate,
            "enabled": self.llm_enabled
        }

    def print_llm_stats(self):
        """Print LLM usage statistics."""
        stats = self.get_llm_stats()
        print(f"\n{self.role.upper()} Agent LLM Statistics:")
        print(f"  Total LLM calls: {stats['total_calls']}")
        print(f"  Successful: {stats['successes']}")
        print(f"  Failed: {stats['failures']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  LLM enabled: {stats['enabled']}")
