"""
SNGenerator.py
==============
Base class for serial-number generators.

A generator is declared in duts.json under a program entry::

    "programs": [{
        "name": "Full Production",
        "sn_generator": {
            "module": "my_module",
            "class": "MyGenerator"
        }
    }]

The class is instantiated once at DUT-load time with ``assets`` as the only
argument.  Before each run the framework calls ``generate()`` and stores the
returned string as the run's serial number.  When a generator is present the
manual serial-number input field is hidden in the UI.
"""
from abc import ABC, abstractmethod


class SNGenerator(ABC):
    """Abstract base class for serial-number generators."""

    def __init__(self, assets):
        self.assets = assets

    @abstractmethod
    def generate(self) -> str:
        """Return the serial number for the next unit under test."""
        pass
