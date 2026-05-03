def build_image_prompt(brief):
    flow = '; '.join(brief.flow) or brief.thesis
    outcomes = '; '.join(brief.outcomes)

    return (
        f"Premium geopolitical infographic. Title: {brief.title}. "
        f"Thesis: {brief.thesis}. Flow: {flow}. Outcomes: {outcomes}. "
        "Layout: structured logic diagram with clear hierarchy and connected nodes. "
        "Style: flat vector, dark navy/slate palette, white text, clean spacing. "
        "Readable at mobile size. No clutter, no tiny text, no raw diagram code."
    )
