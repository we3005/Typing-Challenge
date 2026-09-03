"""
Typing Speed Test
------------------
Measures the users type speed as well as tracks which characters cause the most errors
"""

import sys
import time
import random
import statistics

# ---------------------------------------------------------------------
# Cross-platform single-character reader (no Enter key needed per char)
# ---------------------------------------------------------------------
try:
    import msvcrt  # Windows

    def get_char():
        return msvcrt.getwch()

except ImportError:
    import tty
    import termios  # macOS / Linux

    def get_char():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------
SENTENCES = [
    "the quick brown fox jumps over the lazy dog",
    "python makes it easy to build fun small projects",
    "practice typing every day to build muscle memory",
    "consistency matters more than speed when you start",
    "clear code is easier to read than clever code",
    "success is the sum of small efforts repeated daily",
]

BACKSPACE_CODES = {"\x7f", "\b"}
ENTER_CODES = {"\r", "\n"}
CTRL_C = "\x03"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


# ---------------------------------------------------------------------
# Core test logic
# ---------------------------------------------------------------------
def run_typing_test():
    target = random.choice(SENTENCES)
    print("Type the sentence below exactly. It finishes automatically.\n")
    print(f"  {target}\n")
    input("Press Enter to start...")
    print()

    typed = []
    char_times = []  # (character, seconds_since_previous_keystroke)
    errors = 0
    last_time = None
    start_time = None

    while True:
        ch = get_char()

        if ch == CTRL_C:
            print("\n\nTest cancelled.")
            sys.exit(0)

        if ch in ENTER_CODES:
            break

        now = time.time()
        if start_time is None:
            start_time = now
            last_time = now

        if ch in BACKSPACE_CODES:
            if typed:
                typed.pop()
                if char_times:
                    char_times.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            continue

        index = len(typed)
        expected_char = target[index] if index < len(target) else None
        elapsed = now - last_time
        last_time = now
        typed.append(ch)

        if expected_char is not None and ch == expected_char:
            char_times.append((ch, elapsed))
            sys.stdout.write(GREEN + ch + RESET)
        else:
            errors += 1
            char_times.append((ch, elapsed))
            sys.stdout.write(RED + ch + RESET)
        sys.stdout.flush()

        if index + 1 >= len(target):
            break

    end_time = time.time()
    total_time = max(end_time - start_time, 0.0001) if start_time else 0.0001
    typed_str = "".join(typed)
    return target, typed_str, char_times, errors, total_time


def analyze_results(target, typed_str, char_times, errors, total_time):
    words = len(target.split())
    minutes = total_time / 60
    wpm = (words / minutes) if minutes > 0 else 0

    correct_chars = sum(
        1 for i, c in enumerate(typed_str) if i < len(target) and c == target[i]
    )
    accuracy = (correct_chars / len(target)) * 100 if target else 0

    # Average time-to-type for each character (skip spaces, less meaningful)
    char_time_map = {}
    for ch, dt in char_times:
        if ch.strip():
            char_time_map.setdefault(ch, []).append(dt)

    avg_times = {ch: statistics.mean(times) for ch, times in char_time_map.items()}
    slowest = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)[:5]

    print("\n\n--- Results ---")
    print(f"Time taken:   {total_time:.2f}s")
    print(f"Speed:        {wpm:.1f} WPM")
    print(f"Accuracy:     {accuracy:.1f}%")
    print(f"Errors:       {errors}")

    if slowest:
        print("\nYour slowest characters (avg seconds between keystrokes):")
        for ch, t in slowest:
            print(f"  '{ch}': {t:.3f}s")


def main():
    print("=== Typing Speed Test ===\n")
    while True:
        target, typed_str, char_times, errors, total_time = run_typing_test()
        analyze_results(target, typed_str, char_times, errors, total_time)

        again = input("\nTry again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for practicing! Goodbye.")
            break
        print()


if __name__ == "__main__":
    main()