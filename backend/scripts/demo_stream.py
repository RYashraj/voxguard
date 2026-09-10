"""
VoxGuard Live Terminal Visualizer & Video Demo Script
Run this script while the backend server is running, or it runs the stream directly.
Displays an animated live risk dashboard in the terminal for video recording and team walkthroughs.
"""
import sys
import time
import asyncio
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.simulator import simulate_call
from app.utils.audio_generator import ensure_default_sample_audio

# ANSI Color Codes for terminal
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
GRAY = "\033[90m"
BG_RED = "\033[41m\033[97m"


def render_bar(score: float, width: int = 30) -> str:
    filled = int(score * width)
    empty = width - filled
    
    if score >= 0.70:
        color = RED
    elif score >= 0.40:
        color = YELLOW
    else:
        color = GREEN
        
    bar = color + "█" * filled + GRAY + "░" * empty + RESET
    return f"[{bar}] {color}{score:.2f}{RESET}"


async def run_terminal_demo():
    print(f"\n{BOLD}{CYAN}======================================================================{RESET}")
    print(f"{BOLD}{CYAN}             VOXGUARD — REAL-TIME VOICE IMPERSONATION DETECTION       {RESET}")
    print(f"{BOLD}{GRAY}             SIH26104 | Team Crackjack | Evaluation Live Demo         {RESET}")
    print(f"{BOLD}{CYAN}======================================================================{RESET}\n")

    print(f"{BOLD}Simulating live incoming call with ML inference & rolling risk engine...{RESET}\n")
    time.sleep(1)

    audio_file = ensure_default_sample_audio()
    step = 0
    auto_locked = False

    async for update in simulate_call(audio_file, chunk_duration_sec=3.0, delay_sec=1.5, scenario="gradual_escalation"):
        step += 1
        
        # Color & Alert formatting
        if update.alert_level == "high":
            alert_str = f"{RED}{BOLD}🚨 HIGH RISK — POSSIBLE AI CLONE{RESET}"
            gate_str = f"{BG_RED} ⛔ TRANSACTION AUTO-LOCKED {RESET}"
            auto_locked = True
        elif update.alert_level == "medium":
            alert_str = f"{YELLOW}{BOLD}⚠️  ELEVATED RISK — MONITORING{RESET}"
            gate_str = f"{YELLOW}🔓 Unlocked (Under Watch){RESET}"
        else:
            alert_str = f"{GREEN}{BOLD}✅ LOW RISK — NORMAL VOICE{RESET}"
            gate_str = f"{GREEN}🔓 Unlocked (Safe){RESET}"

        bar = render_bar(update.rolling_risk_score, width=28)
        flags_str = f"{RED}" + ", ".join(update.flags) + f"{RESET}" if update.flags else f"{GRAY}None{RESET}"

        print(f"{BOLD}┌── [{CYAN}{update.chunk_id}{RESET}{BOLD}] ────────────────────────────────────────────────────────{RESET}")
        print(f"│  {BOLD}Instant Chunk Score :{RESET} {update.chunk_score:.4f}  |  {BOLD}Confidence:{RESET} {update.confidence*100:.1f}%")
        print(f"│  {BOLD}Smoothed Rolling Risk:{RESET} {bar}")
        print(f"│  {BOLD}Current Alert Level  :{RESET} {alert_str}")
        print(f"│  {BOLD}Synthetic Flags      :{RESET} {flags_str}")
        print(f"│  {BOLD}Approval Gate Status :{RESET} {gate_str}")
        print(f"{BOLD}└───────────────────────────────────────────────────────────────────{RESET}\n")

    if auto_locked:
        print(f"\n{BOLD}{YELLOW}>>> Secondary Verification Triggered: Click 'Verify via Callback' to unlock approval gate.{RESET}")
        print(f"{BOLD}{GREEN}>>> Callback confirmed. Prevention policy successfully demonstrated!{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run_terminal_demo())
