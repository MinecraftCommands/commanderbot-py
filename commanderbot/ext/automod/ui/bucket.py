from discord import ui

from commanderbot.ext.automod.bucket import AutomodBucket

__all__ = ("BucketList",)


class BucketList(ui.LayoutView):
    def __init__(self, buckets: list[AutomodBucket]):
        super().__init__()

        container = ui.Container(accent_color=0x00ACED)
        self.add_item(container)

        container.add_item(ui.TextDisplay("### 🪣 All buckets"))
        container.add_item(ui.Separator())

        formatted_buckets: list[str] = []
        enabled_buckets: int = 0
        disabled_buckets: int = 0
        for bucket in buckets:
            if not bucket.disabled:
                formatted_buckets.append(bucket.name)
                enabled_buckets += 1
            else:
                formatted_buckets.append(f"{bucket.name} (Disabled)")
                disabled_buckets += 1

        if formatted_buckets:
            lines = "\n".join(("```", "\n".join(formatted_buckets), "```"))
            container.add_item(ui.TextDisplay(lines))
        else:
            container.add_item(ui.TextDisplay("**None!**"))

        container.add_item(ui.Separator())
        container.add_item(
            ui.TextDisplay(
                f"-# Enabled: {enabled_buckets} | Disabled: {disabled_buckets}"
            )
        )
