def build_prompt(brief):
    return f"Create a clean infographic: {brief.title}. Flow: {', '.join(brief.flow)}"
