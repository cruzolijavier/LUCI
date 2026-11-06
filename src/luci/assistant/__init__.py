"""LUCI Assistant: an OpenAI (model Luna) helper inside the LUCI window.

    config.py      model, token budget and where the API key is read from
    client.py      calls to OpenAI: chat with tools, transcription, embeddings
    knowledge.py   what it knows: the window, the inputs, every program (from
                   the registry) and their upstream documentation (knowledge/)
    rag.py         search in that documentation (BM25 + embeddings)
    screen.py      what it sees on the window and what it can do there
    data_tools.py  reading tools: documentation, the user's files, environments
    session.py     the conversation and the tool loop
    audio.py       microphone dictation
    widgets.py     robot with the CONTROL switch under it, and the chat panel

Use: ``install_assistant(main_window)`` at the end of the window's construction.
"""

from __future__ import annotations


def install_assistant(window):
    """Put the robot and the chat on ``window``. If anything is missing (for example
    the openai package), LUCI keeps working without the assistant."""
    try:
        from .session import AssistantSession
        from .widgets import AssistantView
        session = AssistantSession(window)
        view = AssistantView(window, session)
        window._assistant = view
        for workspace in window.workspaces.values():
            workspace.page_changed.connect(lambda _on: session.screen_changed.emit())
            for page in workspace.pages.values():
                # Keep the end of the console lines clear of the robot.
                layout = page.console.parentWidget().layout()
                margins = layout.contentsMargins()
                layout.setContentsMargins(margins.left(), margins.top(), 96, margins.bottom())
        window.layer_list.currentRowChanged.connect(lambda _row: session.screen_changed.emit())
        if hasattr(window, "home_changed"):
            window.home_changed.connect(lambda _home: session.screen_changed.emit())
        return view
    except Exception:
        import traceback
        traceback.print_exc()
        return None


__all__ = ["install_assistant"]
