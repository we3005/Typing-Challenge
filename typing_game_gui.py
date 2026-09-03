"""
Typing Anaysis - Visual Version (Updated)
--------------------------------------------------------
A small typing game that measures the typing speed as well as tracks which characters cause the most errors
"""

import io
import math
import platform
import struct
import subprocess
import tempfile
import wave
import time
import random
import statistics
import tkinter as tk
import tkinter.font as tkfont

THEMES = {
    "light": {
        "bg": "#f7f5ee",
        "card": "#dbe6d6",
        "text_main": "#45594a",
        "text_muted": "#74886f",
        "accent": "#c1620e",
        "panel_bg": "#fbfaf4",
        "badge_bg": "#cfe0cb",
        "error": "#c0392b",
        "toggle_icon": "\u22c6\u2734\ufe0e\u02da\uff61\u22c6",
        "toggle_label": "Dark",
    },
    "dark": {
        "bg": "#1b2b30",
        "card": "#3f5445",
        "text_main": "#a9c6a4",
        "text_muted": "#839a80",
        "accent": "#d97a1f",
        "panel_bg": "#17272b",
        "badge_bg": "#34473a",
        "error": "#e2725b",
        "toggle_icon": "\u23fe\u22c6.\u02da",
        "toggle_label": "Light",
    },
}

DECOR_SYMBOLS = ["\U0001315D \u22c6.", "\u2693\ufe0e", "\u0b33", "\U0001315D\u25c9"]
DECOR_POSITIONS = [
    (0.05, 0.12, 46),
    (0.92, 0.16, 32),
    (0.06, 0.86, 40),
    (0.90, 0.82, 28),
]

#Example Texts

PASSAGES = {
    "short": [
        "Jellyfish have no brain, no heart, and no bones, yet they have thrived in every ocean for over five hundred million years.",
        "A swordfish can swim in bursts approaching sixty miles per hour, making it one of the fastest fish anywhere in the ocean.",
        "Stingrays breathe through small holes called spiracles instead of their mouths, so sand never gets sucked in while they hunt.",
        "The ocean sunfish can lay more eggs than any other vertebrate on Earth, sometimes producing around three hundred million at once.",
    ],
    "medium": [
        "Jellyfish have drifted through Earth's oceans for longer than dinosaurs existed, surviving five mass extinction events without ever needing a brain to do it. Some species are even considered biologically immortal, capable of reverting their cells back to an earlier stage of life whenever they are injured or under stress.",
        "Whale sharks are the largest fish in the entire ocean, yet they survive almost entirely on tiny plankton and small fish filtered through their enormous mouths. Despite their intimidating size, which can stretch beyond forty feet, whale sharks are famously gentle and have never been recorded harming a human.",
        "Anglerfish use a glowing lure attached to their heads to attract curious prey in the pitch-black depths of the ocean. In some species, the tiny male permanently fuses to the much larger female's body, eventually sharing her bloodstream and losing nearly all of his own organs except those needed for reproduction.",
        "Moray eels have a second set of jaws hidden inside their throats, called pharyngeal jaws, which shoot forward to drag prey deeper into their mouths. Scientists only discovered this strange feeding method in 2007, even though moray eels had already been familiar residents of coral reefs for millions of years.",
    ],
    "long": [
        "Jellyfish have existed in Earth's oceans for more than five hundred million years, long before dinosaurs, trees, or even backboned animals first appeared, and they have survived every mass extinction event since without ever evolving a brain, heart, or blood. Instead, a simple nerve net allows them to sense light, detect prey, and react to their surroundings well enough to thrive in nearly every ocean on the planet. Certain species, such as the so-called immortal jellyfish, can even revert their adult cells back into an earlier developmental stage when injured, effectively resetting their biological clock indefinitely.",
        "Whale sharks may be the largest fish in the ocean, sometimes growing longer than a city bus, yet they pose almost no threat to humans because they feed by filtering enormous volumes of water for plankton, small fish, and fish eggs rather than hunting larger prey. Despite their massive size, remarkably little is known about their migration patterns, breeding habits, or exact lifespan, since tracking such large animals across vast stretches of open ocean remains extremely difficult even with modern satellite tagging technology. Divers who encounter them often describe the experience as awe-inspiring rather than frightening.",
        "Anglerfish are among the strangest creatures living in the deep sea, using a glowing lure powered by bioluminescent bacteria to attract prey through the total darkness thousands of feet below the surface. In many species, the male is dramatically smaller than the female, and upon finding a mate, he bites into her body and gradually fuses with her permanently, losing his eyes, fins, and most internal organs except those needed to produce sperm. Some female anglerfish carry several of these tiny fused males at once, effectively turning them into a lifelong, built-in source of reproduction.",
        "The frilled shark is often called a living fossil because its body shape has barely changed in over eighty million years, making it look strikingly similar to ancient sea serpents described in old sailor legends. It lives in the deep ocean, sometimes more than three thousand feet below the surface, where sunlight never reaches and pressure would crush most other creatures. Its long, snake-like body and rows of backward-curving teeth allow it to strike prey with a sudden lunge, swallowing smaller fish and squid whole. Much of what scientists know about it still comes from specimens caught accidentally in deep-sea fishing nets.",
        "Moray eels spend most of their lives hidden inside crevices and coral reefs, only revealing their head as they open and close their mouths repeatedly, a motion that looks aggressive but is actually just how they breathe by pumping water over their gills. Hidden inside their throat is a second, smaller set of jaws that scientists did not discover until relatively recently, which shoots forward to grab prey and pull it further down. This double-jaw system makes them remarkably effective hunters despite poor eyesight, since they rely on an extremely sharp sense of smell to find prey in the dark, narrow reef.",
    ],
}

LENGTH_LABELS = {
    "short": "Short (~20 words)",
    "medium": "Medium (~50 words)",
    "long": "Long (~100 words)",
}


#sound
def _generate_pop_wav_bytes(freq_start=520.0, freq_end=320.0, duration=0.14,
                             volume=0.35, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    attack = max(1, int(0.015 * sample_rate))
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        progress = i / n_samples
        freq = freq_start * ((freq_end / freq_start) ** progress)
        env = (i / attack) if i < attack else math.exp(-7 * (i - attack) / n_samples)
        sample = volume * env * math.sin(2 * math.pi * freq * t)
        val = int(max(-1.0, min(1.0, sample)) * 32767)
        frames += struct.pack("<h", val)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))
    return buf.getvalue()


class ClickSound:

    def __init__(self):
        self.enabled = True
        self._path = None
        try:
            data = _generate_pop_wav_bytes()
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(data)
            tmp.close()
            self._path = tmp.name
        except Exception:
            self.enabled = False

    def play(self):
        if not self.enabled or not self._path:
            return
        system = platform.system()
        try:
            if system == "Windows":
                import winsound
                winsound.PlaySound(self._path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif system == "Darwin":
                subprocess.Popen(["afplay", self._path],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(["aplay", "-q", self._path],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Never let a sound-playback failure break the app.
            pass


def resolve_font(root, preferred, fallback):
    try:
        families = set(tkfont.families(root))
    except Exception:
        families = set()
    return preferred if preferred in families else fallback


def make_sticker_frame(parent, colors):
    """A 'shadow' frame behind a bordered 'card' frame - mimics the
    offset box-shadow look of your site's .card / section elements."""
    shadow = tk.Frame(parent, bg=colors["card"])
    card = tk.Frame(shadow, bg=colors["panel_bg"], highlightthickness=2,
                     highlightbackground=colors["text_main"], bd=0)
    card.pack(padx=(0, 6), pady=(0, 6), fill="both", expand=True)
    return shadow, card


def sound_and(controller, func):
    """Wrap a button command so it plays the click sound first."""
    def _inner(*_args):
        controller.click()
        func()
    return _inner


#main
class TypingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Typing Analysis")
        self.geometry("820x580")
        self.minsize(720, 500)

        self.theme_name = "light"
        self.settings = {"length": "medium"}
        self.click_sound = ClickSound()

        self.font_header = resolve_font(self, "Pixelify Sans", "Segoe UI")
        self.font_body = resolve_font(self, "VT323", "Courier New")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for ScreenClass in (StartScreen, SettingsScreen, GameScreen):
            frame = ScreenClass(container, self)
            self.frames[ScreenClass.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.apply_theme()
        self.show_frame("StartScreen")

    @property
    def colors(self):
        return THEMES[self.theme_name]

    def click(self):
        self.click_sound.play()

    def toggle_theme(self):
        self.click()
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.apply_theme()

    def apply_theme(self):
        colors = self.colors
        self.configure(bg=colors["bg"])
        for frame in self.frames.values():
            frame.apply_theme(colors)

    def show_frame(self, name):
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()


#start

class StartScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.header = tk.Frame(self, height=70)
        self.header.pack(fill="x")

        self.toggle_btn = tk.Button(
            self.header, font=(controller.font_header, 10, "bold"),
            relief="flat", bd=0, cursor="hand2",
            command=lambda: controller.toggle_theme()
        )
        self.toggle_btn.pack(side="right", padx=16, pady=16)

        self.title_label = tk.Label(
            self.header, text="Typing Analysis",
            font=(controller.font_header, 22, "bold")
        )
        self.title_label.pack(side="left", padx=20, pady=16)

        self.decor_labels = []
        for (relx, rely, size), sym in zip(DECOR_POSITIONS, DECOR_SYMBOLS):
            lbl = tk.Label(self, text=sym, font=(controller.font_body, size), bd=0)
            lbl.place(relx=relx, rely=rely, anchor="center")
            self.decor_labels.append(lbl)

        self.body = tk.Frame(self)
        self.body.place(relx=0.5, rely=0.56, anchor="center")

        self.shadow, self.card = make_sticker_frame(self.body, controller.colors)
        self.shadow.pack()
        self.inner = tk.Frame(self.card, padx=45, pady=35)
        self.inner.pack()

        self.subtitle_label = tk.Label(
            self.inner, text="Test your speed. Find your weak keys.",
            font=(controller.font_header, 12)
        )
        self.subtitle_label.pack(pady=(0, 25))

        self.start_btn = tk.Button(
            self.inner, text="Start", width=20,
            font=(controller.font_header, 12, "bold"), relief="flat",
            bd=0, cursor="hand2",
            command=sound_and(controller, lambda: controller.show_frame("GameScreen"))
        )
        self.start_btn.pack(pady=8, ipady=4)

        self.settings_btn = tk.Button(
            self.inner, text="Settings", width=20,
            font=(controller.font_header, 12, "bold"), relief="flat",
            bd=0, cursor="hand2",
            command=sound_and(controller, lambda: controller.show_frame("SettingsScreen"))
        )
        self.settings_btn.pack(pady=8, ipady=4)

        self.quit_btn = tk.Button(
            self.inner, text="Quit", width=20,
            font=(controller.font_header, 12, "bold"), relief="solid", bd=2,
            cursor="hand2",
            command=sound_and(controller, controller.destroy)
        )
        self.quit_btn.pack(pady=8, ipady=4)

    def apply_theme(self, colors):
        self.configure(bg=colors["bg"])
        self.header.configure(bg=colors["bg"])
        self.title_label.configure(bg=colors["bg"], fg=colors["text_main"])
        self.toggle_btn.configure(
            text=f"{colors['toggle_icon']}  {colors['toggle_label']}",
            bg=colors["card"], fg=colors["text_main"],
            activebackground=colors["accent"], activeforeground=colors["bg"]
        )
        self.body.configure(bg=colors["bg"])
        for lbl in self.decor_labels:
            lbl.configure(bg=colors["bg"], fg=colors["card"])

        self.shadow.configure(bg=colors["card"])
        self.card.configure(bg=colors["panel_bg"], highlightbackground=colors["text_main"])
        self.inner.configure(bg=colors["panel_bg"])
        self.subtitle_label.configure(bg=colors["panel_bg"], fg=colors["text_muted"])

        for btn in (self.start_btn, self.settings_btn):
            btn.configure(bg=colors["accent"], fg=colors["bg"],
                          activebackground=colors["text_main"], activeforeground=colors["bg"])

        self.quit_btn.configure(
            bg=colors["panel_bg"], fg=colors["accent"],
            activebackground=colors["accent"], activeforeground=colors["bg"]
        )


#settings

class SettingsScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.header = tk.Frame(self, height=70)
        self.header.pack(fill="x")

        self.toggle_btn = tk.Button(
            self.header, font=(controller.font_header, 10, "bold"),
            relief="flat", bd=0, cursor="hand2",
            command=lambda: controller.toggle_theme()
        )
        self.toggle_btn.pack(side="right", padx=16, pady=16)

        self.title_label = tk.Label(
            self.header, text="Settings", font=(controller.font_header, 20, "bold")
        )
        self.title_label.pack(side="left", padx=20, pady=16)

        self.decor_labels = []
        for (relx, rely, size), sym in zip(DECOR_POSITIONS, DECOR_SYMBOLS):
            lbl = tk.Label(self, text=sym, font=(controller.font_body, size), bd=0)
            lbl.place(relx=relx, rely=rely, anchor="center")
            self.decor_labels.append(lbl)

        self.body = tk.Frame(self)
        self.body.place(relx=0.5, rely=0.56, anchor="center")

        self.shadow, self.card = make_sticker_frame(self.body, controller.colors)
        self.shadow.pack()
        self.inner = tk.Frame(self.card, padx=45, pady=35)
        self.inner.pack()

        self.section_label = tk.Label(
            self.inner, text="\u2605 Challenge Length \u2605",
            font=(controller.font_header, 14, "bold")
        )
        self.section_label.pack(anchor="w", pady=(0, 14))

        self.length_var = tk.StringVar(value=controller.settings["length"])
        self.radio_buttons = []
        for value in ("short", "medium", "long"):
            rb = tk.Radiobutton(
                self.inner, text=LENGTH_LABELS[value], variable=self.length_var,
                value=value, font=(controller.font_body, 15),
                command=sound_and(controller, self._save_setting),
                anchor="w", bd=0, highlightthickness=0
            )
            rb.pack(anchor="w", pady=4, fill="x")
            self.radio_buttons.append(rb)

        self.back_btn = tk.Button(
            self.inner, text="Back to Menu", font=(controller.font_header, 11, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=14, pady=8,
            command=sound_and(controller, lambda: controller.show_frame("StartScreen"))
        )
        self.back_btn.pack(anchor="w", pady=(24, 0))

    def _save_setting(self):
        self.controller.settings["length"] = self.length_var.get()

    def apply_theme(self, colors):
        self.configure(bg=colors["bg"])
        self.header.configure(bg=colors["bg"])
        self.title_label.configure(bg=colors["bg"], fg=colors["text_main"])
        self.toggle_btn.configure(
            text=f"{colors['toggle_icon']}  {colors['toggle_label']}",
            bg=colors["card"], fg=colors["text_main"],
            activebackground=colors["accent"], activeforeground=colors["bg"]
        )
        self.body.configure(bg=colors["bg"])
        for lbl in self.decor_labels:
            lbl.configure(bg=colors["bg"], fg=colors["card"])

        self.shadow.configure(bg=colors["card"])
        self.card.configure(bg=colors["panel_bg"], highlightbackground=colors["text_main"])
        self.inner.configure(bg=colors["panel_bg"])
        self.section_label.configure(bg=colors["panel_bg"], fg=colors["text_main"])

        for rb in self.radio_buttons:
            rb.configure(
                bg=colors["panel_bg"], fg=colors["text_main"],
                selectcolor=colors["badge_bg"], activebackground=colors["panel_bg"],
                activeforeground=colors["accent"]
            )

        self.back_btn.configure(
            bg=colors["accent"], fg=colors["bg"],
            activebackground=colors["text_main"], activeforeground=colors["bg"]
        )


#game

class GameScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.passage = ""
        self.start_time = None
        self.last_key_time = None
        self.char_times = []  # (expected_char, elapsed_seconds, was_correct)
        self.errors = 0
        self.typed_length = 0
        self.finished = False

        self.header = tk.Frame(self, height=60)
        self.header.pack(fill="x")

        self.title_label = tk.Label(
            self.header, text="Typing Analysis", font=(controller.font_header, 16, "bold")
        )
        self.title_label.pack(side="left", padx=20, pady=14)

        self.right_box = tk.Frame(self.header)
        self.right_box.pack(side="right", padx=16, pady=10)

        self.toggle_btn = tk.Button(
            self.right_box, font=(controller.font_header, 9, "bold"),
            relief="flat", bd=0, cursor="hand2",
            command=lambda: controller.toggle_theme()
        )
        self.toggle_btn.pack(side="left", padx=(0, 8))

        self.menu_btn = tk.Button(
            self.right_box, text="Menu", font=(controller.font_header, 10, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=10,
            command=sound_and(controller, lambda: controller.show_frame("StartScreen"))
        )
        self.menu_btn.pack(side="left")

        self.body = tk.Frame(self, padx=20, pady=20)
        self.body.pack(fill="both", expand=True)

        self.shadow, self.card = make_sticker_frame(self.body, controller.colors)
        self.shadow.pack(fill="both", expand=True, pady=(0, 15))

        self.passage_text = tk.Text(
            self.card, wrap="word", height=9, relief="flat",
            padx=15, pady=15, state="disabled", bd=0, highlightthickness=0
        )
        self.passage_text.pack(fill="both", expand=True)

        self.input_entry = tk.Entry(self.body, relief="solid", bd=2)
        self.input_entry.pack(fill="x", pady=(0, 15), ipady=8)
        self.input_entry.bind("<KeyPress>", self.on_key_press)

        self.button_frame = tk.Frame(self.body)
        self.button_frame.pack(fill="x")

        self.new_btn = tk.Button(
            self.button_frame, text="New Challenge", relief="flat", bd=0,
            padx=15, pady=8, cursor="hand2",
            command=sound_and(controller, self.new_challenge)
        )
        self.new_btn.pack(side="left")

        self.results_label = tk.Label(
            self.body, text="", justify="left", anchor="w", wraplength=740
        )
        self.results_label.pack(fill="x", pady=(15, 0))

        self.passage_text.configure(font=(controller.font_body, 15))
        self.input_entry.configure(font=(controller.font_body, 15))
        self.new_btn.configure(font=(controller.font_header, 11, "bold"))
        self.results_label.configure(font=(controller.font_body, 13))

    def on_show(self):
        self.new_challenge()

    def new_challenge(self):
        length = self.controller.settings["length"]
        self.passage = random.choice(PASSAGES[length])
        self.start_time = None
        self.last_key_time = None
        self.char_times = []
        self.errors = 0
        self.typed_length = 0
        self.finished = False

        self.input_entry.config(state="normal")
        self.input_entry.delete(0, tk.END)
        self.results_label.config(text="")

        self.passage_text.config(state="normal")
        self.passage_text.delete("1.0", tk.END)
        self.passage_text.insert("1.0", self.passage)
        self.passage_text.tag_add("pending", "1.0", tk.END)
        self.passage_text.config(state="disabled")

        self.input_entry.focus_set()

    def on_key_press(self, event):
        if self.finished:
            return "break"

        if event.keysym in (
            "Shift_L", "Shift_R", "Control_L", "Control_R",
            "Alt_L", "Alt_R", "Caps_Lock", "Tab", "Return"
        ):
            return

        now = time.time()
        if self.start_time is None:
            self.start_time = now
            self.last_key_time = now

        if event.keysym == "BackSpace":
            if self.typed_length > 0:
                self.typed_length -= 1
                if self.char_times:
                    self.char_times.pop()
                self._refresh_highlight()
            return

        char = event.char
        if not char:
            return

        if self.typed_length >= len(self.passage):
            return "break"

        elapsed = now - self.last_key_time
        self.last_key_time = now

        expected = self.passage[self.typed_length]
        is_correct = char == expected
        if not is_correct:
            self.errors += 1

        self.char_times.append((expected, elapsed, is_correct))
        self.typed_length += 1
        self._refresh_highlight()

        if self.typed_length >= len(self.passage):
            self.finish_test()

    def _refresh_highlight(self):
        self.passage_text.config(state="normal")
        self.passage_text.tag_remove("correct", "1.0", tk.END)
        self.passage_text.tag_remove("incorrect", "1.0", tk.END)
        self.passage_text.tag_remove("pending", "1.0", tk.END)

        for i, (expected, elapsed, is_correct) in enumerate(self.char_times):
            start = f"1.0 + {i} chars"
            end = f"1.0 + {i + 1} chars"
            tag = "correct" if is_correct else "incorrect"
            self.passage_text.tag_add(tag, start, end)

        pending_start = f"1.0 + {self.typed_length} chars"
        self.passage_text.tag_add("pending", pending_start, tk.END)
        self.passage_text.config(state="disabled")

    def finish_test(self):
        self.finished = True
        self.input_entry.config(state="disabled")

        total_time = max(time.time() - self.start_time, 0.0001)
        minutes = total_time / 60
        words = len(self.passage.split())
        wpm = words / minutes if minutes > 0 else 0

        correct_count = sum(1 for _, _, ok in self.char_times if ok)
        accuracy = (correct_count / len(self.char_times)) * 100 if self.char_times else 0

        char_time_map = {}
        for expected, elapsed, is_correct in self.char_times:
            if expected.strip():
                char_time_map.setdefault(expected, []).append(elapsed)

        avg_times = {c: statistics.mean(t) for c, t in char_time_map.items()}
        slowest = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)[:5]
        slow_str = ", ".join(f"'{c}' ({t:.2f}s)" for c, t in slowest)

        result_text = (
            f"Time: {total_time:.1f}s   |   Speed: {wpm:.1f} WPM   |   "
            f"Accuracy: {accuracy:.1f}%   |   Errors: {self.errors}\n"
            f"Slowest characters: {slow_str if slow_str else 'N/A'}"
        )
        self.results_label.config(text=result_text)

    def apply_theme(self, colors):
        self.configure(bg=colors["bg"])
        self.header.configure(bg=colors["bg"])
        self.title_label.configure(bg=colors["bg"], fg=colors["text_main"])
        self.right_box.configure(bg=colors["bg"])
        self.toggle_btn.configure(
            text=f"{colors['toggle_icon']}  {colors['toggle_label']}",
            bg=colors["card"], fg=colors["text_main"],
            activebackground=colors["accent"], activeforeground=colors["bg"]
        )
        self.menu_btn.configure(
            bg=colors["accent"], fg=colors["bg"],
            activebackground=colors["text_main"], activeforeground=colors["bg"]
        )
        self.body.configure(bg=colors["bg"])
        self.shadow.configure(bg=colors["card"])
        self.card.configure(bg=colors["panel_bg"], highlightbackground=colors["text_main"])

        self.passage_text.configure(
            bg=colors["panel_bg"], fg=colors["text_main"], insertbackground=colors["text_main"]
        )
        self.passage_text.tag_config("correct", foreground=colors["bg"], background=colors["accent"])
        self.passage_text.tag_config("incorrect", foreground=colors["bg"], background=colors["error"])
        self.passage_text.tag_config("pending", foreground=colors["text_muted"], background=colors["panel_bg"])

        self.input_entry.configure(
            bg=colors["panel_bg"], fg=colors["text_main"], insertbackground=colors["text_main"],
            highlightbackground=colors["text_main"]
        )
        self.button_frame.configure(bg=colors["bg"])
        self.new_btn.configure(
            bg=colors["accent"], fg=colors["bg"],
            activebackground=colors["text_main"], activeforeground=colors["bg"]
        )
        self.results_label.configure(bg=colors["bg"], fg=colors["text_muted"])


def main():
    app = TypingApp()
    app.mainloop()


if __name__ == "__main__":
    main()