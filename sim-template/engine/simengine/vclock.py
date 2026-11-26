"""Reloj simulado para los temporizadores de SpiffWorkflow (ADR-001, criterio S4).

SpiffWorkflow lee el reloj con `datetime.now()` en un solo módulo; se sustituye por el reloj de SimPy.
Dos reglas: (1) fijar `Clock.seconds` antes de cada llamada a SpiffWorkflow; (2) SpiffWorkflow dispara solo con un reloj
ESTRICTAMENTE posterior al instante configurado, por eso `fire_epsilon` avanza una millonésima al disparar.
Estado global: las simulaciones se ejecutan una a la vez (el servidor las serializa con un candado).
NOTA: aún no está conectado al motor del sorteo (no usa temporizadores); se usará con la trivia.
"""
from datetime import datetime as _dt, timedelta, timezone

import SpiffWorkflow.bpmn.specs.event_definitions.timer as _timer

BASE = _dt(2026, 1, 1, tzinfo=timezone.utc)
fire_epsilon = 1e-6


class Clock:
    seconds = 0.0

    @classmethod
    def now(cls):
        return BASE + timedelta(seconds=cls.seconds)


class _VirtualDatetime(_dt):
    @classmethod
    def now(cls, tz=None):
        d = Clock.now()
        return d.astimezone(tz) if tz else d.replace(tzinfo=None)


def install():
    _timer.datetime = _VirtualDatetime
