# banner.py — light-blue startup banner. Call banner() at app startup.
import os, shutil

if os.name == "nt":
    os.system("")            # ponytail: turns on ANSI in legacy Windows consoles; no-op in Windows Terminal

LIGHT_BLUE = "\033[38;2;173;216;230m"   # truecolor "lightblue"; swap for "\033[94m" if you want plain bright-blue
RESET = "\033[0m"

def banner():
    width = shutil.get_terminal_size((105, 20)).columns   # spans the terminal; falls back to 105
    print(f"{LIGHT_BLUE}{'─' * width}\n❯{RESET}")

Then call it at the top of whichever app's entry point:

- sysdiag CLI — first line of main() in sysdiag.py:
def main():
    import banner; banner.banner()
    ...
- Chatbot — before app.launch(...) in app.py:
import banner; banner.banner()
app.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)