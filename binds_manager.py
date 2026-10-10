from pathlib import Path
import re


def load_binds(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"//.*", "", text)

    pattern = re.compile(
        r"^\s*([A-Za-z0-9+\-_]+)\s+"
        r"(?:[^{]*?)"
        r"\{\s*([^}]+?)\s*\}",
        re.MULTILINE,
    )
    return {
        m.group(1): m.group(2).strip().rstrip(";")
        for m in pattern.finditer(text)
    }


def find_bind(binds: dict, keywords: list[str]) -> list[tuple[str, str]]:
    result = []
    for k, v in binds.items():
        tokens = v.replace('"', " ").split()
        for kw in keywords:
            if kw in tokens:
                result.append((k, v))
                break
    return result


def replace_bind(path: Path, old_keys: str, new_keys: str, action: str) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue

        if not stripped.startswith(old_keys):
            continue

        after = stripped[len(old_keys):]
        if not after or not after[0].isspace():
            continue

        brace_match = re.search(r"\{\s*([^}]+?)\s*\}", line)
        if not brace_match:
            continue
        inside = brace_match.group(1).strip().rstrip(";")
        if inside != action:
            continue

        new_line = line.replace(old_keys, new_keys, 1)
        lines[i] = new_line
        path.write_text("".join(lines), encoding="utf-8")
        return True

    return False


def ask_new_keys(old_keys: str) -> str | None:
    new_keys = input(f"New keybinding (was {old_keys}, Enter to cancel): ").strip()
    if not new_keys:
        return None
    return new_keys


def edit_bind(path: Path, binds: dict, keyword: str) -> None:
    results = find_bind(binds, [keyword])
    if not results:
        print("Not found.")
        return

    if len(results) == 1:
        old_keys, action = results[0]
    else:
        for i, (k, v) in enumerate(results, start=1):
            print(f"  {i}. {k:<20} -> {v}")
        choice = input("Choose number: ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(results)):
            print("Invalid choice.")
            return
        old_keys, action = results[int(choice) - 1]

    new_keys = ask_new_keys(old_keys)
    if new_keys is None:
        print("Cancelled.")
        return

    if replace_bind(path, old_keys, new_keys, action):
        print(f"Done: {old_keys} -> {new_keys}  (action: {action})")
    else:
        print("Failed to replace - line not found.")


def main():
    path = Path.home() / ".config" / "niri" / "cfg" / "keybinds.kdl"

    if not path.exists():
        print(f"File not found: {path}")
        return

    binds = load_binds(path)
    print(f"Total binds loaded: {len(binds)}\n")

    queries = {
        "Close window":      ["close-window"],
        "Browser":           ["firefox", "google-chrome", "chromium",
                              "brave", "vivaldi", "opera", "zen-browser",
                              "librewolf", "qutebrowser", "epiphany"],
        "Terminal":          ["kitty", "alacritty", "wezterm", "foot",
                              "gnome-terminal", "konsole", "xfce4-terminal",
                              "ghostty"],
        "Screenshot":        ["screenshot", "grim", "flameshot",
                              "spectacle", "gnome-screenshot"],
        "File manager":      ["nautilus", "dolphin", "thunar", "nemo",
                              "pcmanfm", "ranger", "yazi", "lf"],
        "Lock screen":       ["swaylock", "hyprlock", "gtklock", "lock"],
        "Quit":              ["quit", "exit"],
        "Monitors off":      ["power-off-monitors"],
        "Text editor":       ["zed", "nvim", "vim", "neovim", "code",
                              "emacs", "helix", "kate"],
        "Music/media":       ["media", "playerctl", "mpv", "spotify"],
    }

    for title, keywords in queries.items():
        results = find_bind(binds, keywords)
        if results:
            for i, (keys, action) in enumerate(results, start=1):
                print(f"{title:<18} {i}. {keys:<20} -> {action}")
        else:
            print(f"{title:<18} - not found")

    show_allask = input("\nShow all binds? y/N: ").strip().lower()
    if show_allask == "y":
        for i, (bind, action) in enumerate(binds.items(), start=1):
            print(f"{i:>3}. {bind:<25} -> {action}")

    change = input("\nEdit a bind? y/N: ").strip().lower()
    if change != "y":
        return

    print("\nAvailable keywords:")
    for title, keywords in queries.items():
        print(f"  {title:<18} -> {keywords[0]}")

    keyword = input("\nEnter keyword (e.g. close-window, firefox, screenshot): ").strip()
    if not keyword:
        print("Empty - cancelled.")
        return

    edit_bind(path, binds, keyword)


if __name__ == "__main__":
    main()