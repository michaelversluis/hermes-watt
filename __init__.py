"""Hermes entry point. Only public observer and command surfaces."""


def register(ctx):
    from .dashboard.plugin_api import Recorder, Store, storage_root, render_receipt
    recorder = Recorder(storage_root, local_energy=lambda: ctx.get_config("local_energy", False) is True,
                        enabled=lambda: ctx.get_config("recording", True) is True)
    for name in recorder.HOOKS:
        def observe(_event=name, **payload):
            recorder.handle(_event, payload)
        ctx.register_hook(name, observe)

    def watt(raw_args="", *, session_id=None, source=None):
        if raw_args.strip() not in {"", "help"}:
            return "Use /watt for this conversation's latest energy receipt. Open Hermes Watt in Desktop for the overview and comparisons."
        if not session_id:
            return "No conversation is bound to this command. Open Hermes Watt in Desktop to view this profile's receipts."
        receipt = Store(storage_root()).latest(session_id)
        return render_receipt(receipt) if receipt else "No energy receipt yet. Run a task with Hermes Watt enabled, then use /watt."
    ctx.register_command("watt", handler=watt, description="Show this conversation's latest energy receipt")
