"""Deployed graph entry for the main EvoQuant agent.

The main ``EvoQuant_agent`` is exposed via ``__getattr__`` lazy loading
in ``CamusGIT/EvoQuant.py`` so it doesn't construct on plain
``import EvoQuant``. ``langgraph dev`` 's symbol resolver inspects
module attributes directly and doesn't trigger ``__getattr__``, so we
re-export here to make it visible.
"""

from EvoQuant.EvoQuant import EvoQuant_agent

__all__ = ["EvoQuant_agent"]
