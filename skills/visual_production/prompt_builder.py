def build_image_prompt(brief):
    flow = '; '.join(brief.flow) or brief.thesis
    outcomes = '; '.join(brief.outcomes)
    return f'Premium flat vector infographic. Title: {brief.title}. Thesis: {brief.thesis}. Flow: {flow}. Outcomes: {outcomes}. Clear hierarchy, crisp icons, readable labels, clean spacing.'
