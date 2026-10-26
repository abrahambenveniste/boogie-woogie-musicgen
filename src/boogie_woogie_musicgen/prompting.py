"""Boogie-Woogie prompt presets and prompt assembly."""

PRESETS = {
    "classic-honky-tonk": (
        "Instrumental solo piano in a lively classic Boogie-Woogie style, "
        "steady swinging 12-bar blues feel, rolling walking left-hand bass, "
        "syncopated right-hand blues riffs and turnarounds, bright honky-tonk "
        "piano, intimate vintage club sound, no vocals."
    ),
    "chicago-club": (
        "Instrumental piano-led Chicago blues Boogie-Woogie, driving shuffle "
        "groove, repetitive walking bass in the left hand, expressive bent-note "
        "style right-hand piano phrases, small smoky club ambience, no vocals."
    ),
    "jump-blues-piano": (
        "Upbeat instrumental jump-blues and Boogie-Woogie piano, brisk swing, "
        "rolling bass ostinato, crisp syncopated piano fills, playful call-and-" 
        "response energy, vintage dance-hall character, piano in the foreground, "
        "no vocals."
    ),
}


def build_prompt(preset: str | None = None, notes: str = "") -> str:
    """Return a readable prompt from a known preset and optional style notes."""
    if preset is None:
        base = "Instrumental solo piano in a lively Boogie-Woogie style, no vocals."
    else:
        try:
            base = PRESETS[preset]
        except KeyError as exc:
            choices = ", ".join(sorted(PRESETS))
            raise ValueError(f"Unknown preset {preset!r}. Choose from: {choices}") from exc

    notes = notes.strip()
    if not notes:
        return base
    return f"{base} Additional direction: {notes}"
