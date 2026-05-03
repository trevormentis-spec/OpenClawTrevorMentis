class VisualRouter:
    def route(self, brief):
        if brief.render_engine == "nano_banana":
            return "nano"
        if brief.render_engine == "svg":
            return "svg"
        return "hybrid"
