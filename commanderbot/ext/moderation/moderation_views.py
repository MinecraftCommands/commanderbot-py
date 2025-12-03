from typing import Optional

from discord import ui


class ModerationResponse(ui.LayoutView):
    def __init__(self, title: str, reason: Optional[str] = None):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(f"### {title}"),
            ui.Separator(),
            ui.TextDisplay(f"**Reason**\n{reason or "No reason given"}"),
            accent_color=0x00ACED,
        )

        self.add_item(container)
