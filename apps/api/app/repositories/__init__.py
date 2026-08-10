"""Repository package.

Repository implementations are imported from their concrete modules. Keeping
this package initializer side-effect free prevents every model family from
being registered when only one repository is needed.
"""
