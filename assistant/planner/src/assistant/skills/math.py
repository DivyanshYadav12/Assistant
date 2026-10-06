"""Math skill — real-time arithmetic and Notepad problem solving.

Supports:
- "what is 2 plus 2" / "calculate 15 times 3" → speaks the answer
- "solve this on notepad" → reads selected text from Notepad, solves,
  writes the answer below the question
"""

from __future__ import annotations

import re
import subprocess
import time

import pyautogui
import pyperclip

from assistant.skills.base import SkillContext, SkillResult

# Word -> operator mapping
_WORD_OPS = {
    "plus": "+", "add": "+", "added to": "+", "and": "+",
    "minus": "-", "subtract": "-", "subtracted from": "-",
    "times": "*", "multiply": "*", "multiplied by": "*",
    "divide": "/", "divided by": "/",
    "x": "*",  # "2 x 3"
}

# Word -> number mapping
_WORD_NUMBERS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}

# Pattern: number op number (op number)*  e.g. "2 + 3 * 4"
# More flexible to handle spaces and variations
_MATH_PATTERN = re.compile(
    r"([-+]?\d+(?:\.\d+)?)\s+"
    r"([+\-*/x]|plus|minus|times|divide|multiplied|divided|add|subtract)\s+"
    r"([-+]?\d+(?:\.\d+)?)"
    r"(?:\s+([+\-*/x]|plus|minus|times|divide|multiplied|divided|add|subtract)\s+([-+]?\d+(?:\.\d+)?))*",
    re.IGNORECASE,
)


def _words_to_symbols(expr: str) -> str:
    """Convert '2 plus 3 times 4' -> '2 + 3 * 4'."""
    expr = expr.lower().strip()
    # Convert word numbers first
    for word, num in sorted(_WORD_NUMBERS.items(), key=lambda x: -len(x[0])):
        expr = expr.replace(word, num)
    # Then convert operators
    for word, sym in sorted(_WORD_OPS.items(), key=lambda x: -len(x[0])):
        expr = expr.replace(word, sym)
    # Normalize x to *
    expr = expr.replace("x", "*")
    return expr


def _safe_eval(expr: str) -> float | None:
    """Safely evaluate a basic arithmetic expression."""
    expr = expr.strip()
    # Only allow digits, operators, decimals, spaces, parentheses
    if not re.match(r"^[\d\s+\-*/().]+$", expr):
        return None
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        if isinstance(result, (int, float)):
            return float(result)
    except Exception:
        return None
    return None


def _format_result(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _extract_math(text: str) -> str | None:
    """Try to extract a math expression from free-form text."""
    import structlog
    log = structlog.get_logger()
    
    text = text.lower().strip()
    log.debug("math_extract_input", original=text)

    # Remove filler phrases - check both start and anywhere in text
    for phrase in ("what is", "what's", "calculate", "compute",
                   "tell me", "solve", "how much is", "the answer to",
                   "equals", "is equal to", "equal to", "=", "that is"):
        if text.startswith(phrase):
            text = text[len(phrase):].strip()
        # Also remove if phrase appears anywhere
        text = text.replace(phrase, " ")

    # Remove trailing question marks and filler words
    text = text.rstrip("?").strip()
    for word in ("please", "okay", "thanks", "the"):
        text = text.replace(word, "")
    
    log.debug("math_extract_after_cleanup", cleaned=text)

    # Convert word operators to symbols
    text = _words_to_symbols(text)
    log.debug("math_extract_after_symbols", with_symbols=text)

    # Clean up extra spaces
    text = " ".join(text.split())
    log.debug("math_extract_final", final=text)

    # Try direct eval
    if _safe_eval(text) is not None:
        log.debug("math_extract_success_direct", expr=text)
        return text

    # Try to find a math expression pattern in the text
    match = _MATH_PATTERN.search(text)
    if match:
        candidate = match.group(0)
        log.debug("math_extract_pattern_match", candidate=candidate)
        # Convert any remaining word operators in the match
        candidate = _words_to_symbols(candidate)
        if _safe_eval(candidate) is not None:
            log.debug("math_extract_success_pattern", expr=candidate)
            return candidate

    log.debug("math_extract_failed", text=text)
    return None


def _solve_text_block(text: str) -> str | None:
    """Try to solve a math problem from a text block (from Notepad).

    Handles:
    - "2 + 2" -> "4"
    - "what is 15 * 3?" -> "45"
    - "x + 5 = 10" -> "x = 5"
    - Multiple lines: solve each independently
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return None

    results = []
    for line in lines:
        # Try simple math first
        expr = _extract_math(line)
        if expr:
            val = _safe_eval(expr)
            if val is not None:
                results.append(f"= {_format_result(val)}")
                continue

        # Try simple equation: "x + 5 = 10" or "2x = 8"
        eq_result = _solve_equation(line)
        if eq_result:
            results.append(eq_result)
            continue

        # Couldn't solve this line
        results.append("= (could not solve)")

    if len(results) == 1:
        return results[0]
    return "\n".join(results)


def _solve_equation(line: str) -> str | None:
    """Solve simple linear equations like 'x + 5 = 10' or '2x = 8'."""
    line = line.lower().strip().rstrip("?")
    # Pattern: something = something
    if "=" not in line:
        return None

    left, right = line.split("=", 1)
    left = left.strip()
    right = right.strip()

    # Check if one side has 'x' and the other is a number
    if "x" in left and _safe_eval(right) is not None:
        target = _safe_eval(right)
        # Parse left: forms like "x + 5", "x - 3", "2x", "x / 2"
        # ax + b = target => x = (target - b) / a
        m = re.match(r"([-+]?\d+(?:\.\d+)?)?\s*x\s*([+\-])\s*(\d+(?:\.\d+)?)", left)
        if m:
            a = float(m.group(1)) if m.group(1) else 1.0
            op = m.group(2)
            b = float(m.group(3))
            if op == "+":
                x = (target - b) / a
            else:
                x = (target + b) / a
            return f"x = {_format_result(x)}"

        # Form: ax = target (e.g. "2x = 8")
        m = re.match(r"([-+]?\d+(?:\.\d+)?)\s*x$", left)
        if m:
            a = float(m.group(1))
            if a != 0:
                x = target / a
                return f"x = {_format_result(x)}"

        # Form: x = target (already solved)
        m = re.match(r"^x$", left)
        if m:
            return f"x = {_format_result(target)}"

    return None


class MathSkill:
    """Real-time arithmetic: 'what is 2+2', 'calculate 15 times 3'."""

    name = "math"
    description = "Perform basic math operations: add, subtract, multiply, divide"
    risk_default = "safe"

    _TRIGGER = ("what is", "what's", "calculate", "compute", "how much",
                "solve", "add", "subtract", "multiply", "divide",
                "plus", "minus", "times", "divided")

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower().strip()
        # Check if it looks like math
        expr = _extract_math(text)
        if expr is not None:
            return 0.95
        # Check for trigger words + numbers
        has_trigger = any(t in text for t in self._TRIGGER)
        has_number = bool(re.search(r"\d", text))
        if has_trigger and has_number:
            return 0.8
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        text = context.user_intent
        expr = _extract_math(text)
        
        if expr is None:
            # Try to extract numbers and operators to see what's missing
            numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
            operators = re.findall(r"[+\-*/]|plus|minus|times|divide|multiplied|subtracted|add", text.lower())
            
            if numbers and not operators:
                return SkillResult(
                    status="clarify",
                    clarification_question=f"I see the number{'s' if len(numbers) > 1 else ''} {', '.join(numbers)}. What operation should I perform? (add, subtract, multiply, or divide?)",
                )
            elif len(numbers) == 1 and operators:
                return SkillResult(
                    status="clarify",
                    clarification_question=f"I have {numbers[0]} and want to {operators[0]}. What's the second number?",
                )
            elif len(numbers) >= 2 and not operators:
                return SkillResult(
                    status="clarify",
                    clarification_question=f"I have numbers {', '.join(numbers)}. What operation should I perform?",
                )
            else:
                return SkillResult(
                    status="clarify",
                    clarification_question="What math problem should I solve? Please provide the complete expression.",
                )
        
        result = _safe_eval(expr)
        if result is None:
            return SkillResult(
                status="failed",
                speak="I couldn't solve that math problem.",
            )
        answer = _format_result(result)
        spoken = f"{expr.replace('*', ' times ').replace('/', ' divided by ')} equals {answer}"
        return SkillResult(
            status="ok",
            speak=spoken,
            output={"expression": expr, "answer": answer},
        )


class NotepadSolveSkill:
    """Read selected text from Notepad, solve math, write answer below."""

    name = "notepad_solve"
    description = "Read a math problem from selected text in Notepad and write the answer below it"
    risk_default = "medium"  # writes into Notepad

    _TRIGGER = ("solve this", "solve it", "solve the", "answer this",
                "answer it", "answer the")

    def can_handle(self, intent: str, context: SkillContext) -> float:
        text = intent.lower().strip()
        if any(t in text for t in self._TRIGGER) and "notepad" in text:
            return 0.92
        if any(t in text for t in self._TRIGGER) and "solve" in text:
            return 0.7
        return 0.0

    def execute(self, context: SkillContext) -> SkillResult:
        if not context.session.get("approved"):
            return SkillResult(
                status="needs_approval",
                requires_approval=True,
                approval_preview="Read selected text from Notepad, solve math, and write the answer below.",
            )

        try:
            # Copy selected text from Notepad (Ctrl+C)
            pyautogui.hotkey("ctrl", "c")
            time.sleep(0.3)
            selected = pyperclip.paste()
        except Exception as e:
            return SkillResult(status="failed", error=str(e),
                               speak="I couldn't read the selected text.")

        if not selected or not selected.strip():
            return SkillResult(
                status="clarify",
                clarification_question="I couldn't read any selected text. Please select the math problem in Notepad first.",
            )

        log_text = selected.strip()[:200]
        answer = _solve_text_block(selected.strip())

        if answer is None:
            return SkillResult(
                status="failed",
                speak="I couldn't solve that problem.",
            )

        try:
            # Move to end of selection, add newline, write answer
            pyautogui.press("right")  # deselect, cursor after selection
            pyautogui.press("enter")
            time.sleep(0.1)
            pyautogui.write(answer, interval=0.02)
            return SkillResult(
                status="ok",
                speak=f"The answer is {answer.replace('=', 'is').replace(chr(10), ' and ')}.",
                output={"question": log_text, "answer": answer},
            )
        except Exception as e:
            return SkillResult(status="failed", error=str(e),
                               speak="I solved it but couldn't write the answer.")
