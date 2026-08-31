"""The 3 image prompts for Train Decade — DashScope Wan2.6-t2i.

Style: dark, cinematic, moody, photorealistic-illustrative fitness imagery.
Each prompt is self-contained (no text overlays — text is rendered by Hugo/CSS).

⚠️ ETHNICITY RULE (Vincent, updated 2026-08-25): any subject who is a PERSON must
be drawn as mixed/varied ethnicity — NOT Asian-first, NOT limited to "East Asian
+ Western." Draw from a genuinely varied spread (East Asian, South Asian,
Latino/Hispanic, Black/African, Middle Eastern, Caucasian/European) and phrase
it as "ambiguous mixed ethnicity" WITHOUT naming one group first. Naming "East
Asian and Western" anchors Asian-first — that's exactly why past generations
kept drifting Asian. The audience is men 30-55 across EN + ZH markets, so no
single-ethnicity read.

⚠️ PALETTE (see traindecade skill): the site is warm editorial (cream/ink/jade),
NOT navy/crimson. The "hero" prompt below predates that decision and is
superseded — hero is now a stock photo (static/images/hero.jpg). Do not use
the navy/crimson "hero" prompt for new art.
"""
PROMPTS = {
    # Home hero — broad, motivational, "long game" theme
    # (Superseded: hero is now a static/images/hero.jpg stock photo. Kept for
    #  reference only — do NOT regenerate from this prompt without updating palette.)
    "hero": (
        "Cinematic wide shot of a seasoned man in his late 40s of ambiguous mixed "
        "ethnicity, standing in a dim "
        "industrial gym lit by a single dramatic overhead beam of light. Deep "
        "shadow and warm editorial tones, jade green rim lighting along his "
        "silhouette, volumetric light rays through dust, moody chiaroscuro, film "
        "grain, epic and quiet determination, photorealistic, shallow depth of "
        "field, 16:9 composition, no text, no watermark"
    ),
    # Welcome / brand anchor — the decade-long journey
    "welcome": (
        "A long row of empty gym benches receding into darkness, each bench lit by a "
        "warm pool of light, symbolizing years of consistent effort. Deep navy blue "
        "and emerald atmosphere, cinematic perspective, fog drifting low across the "
        "floor, moody and contemplative, photorealistic, film grain, no people, "
        "no text, no watermark"
    ),
    # Why a Decade — contrast between quick fix and long game
    "decade": (
        "Dramatic split composition: on the left a shattered, cracked stopwatch "
        "falling apart in mid-air, on the right a solid antique hourglass standing "
        "on a steel gym bench, sand flowing steadily. Deep charcoal background with "
        "crimson and jade neon glow, high contrast, cinematic lighting, "
        "photorealistic, moody, no text, no watermark"
    ),
    # Zone 2 / VO2max — the aerobic engine most lifters never build
    # No human figure (avoids the ethnicity rule + direction-flip problem) —
    # a still-life of the heart-engine metaphor carrying the thesis in one second.
    "zone2-vo2max": (
        "Cinematic still life on a dark wooden workbench: a heavyweight barbell lying "
        "horizontally, and beside it a glowing translucent anatomical heart with warm "
        "pulsing emerald-green light from within, faint electrical energy filaments "
        "veining its surface like an engine firing to life. The heart casts a soft jade "
        "glow over the steel bar, highlighting the contrast between raw strength and "
        "the untended engine. Deep charcoal background, moody chiaroscuro, volumetric "
        "light rays, photorealistic-illustrative, film grain, 16:9 composition, "
        "no text, no watermark, no people"
    ),
    # Balance / fall prevention — single-leg stance, functional independence
    # No face / no discernible ethnicity (backlit silhouette of the foot/leg only),
    # same approach as grip-strength to sidestep the ethnicity + direction issues.
    "balance-training": (
        "Cinematic still life of a single bare foot and lower leg balanced on its toes "
        "on a dark slate floor, heavily backlit so the figure is a near-silhouette "
        "with a strong jade-green rim light outlining the form, the other foot lifted "
        "slightly off the ground suggesting a delicate single-leg balance pose, warm "
        "editorial mood, deep charcoal background, moody chiaroscuro, volumetric light, "
        "photorealistic-illustrative, film grain, 16:9 composition, no text, no "
        "watermark, no face"
    ),
}
