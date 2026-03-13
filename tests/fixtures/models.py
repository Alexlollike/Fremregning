"""
tests/fixtures/models.py — deterministiske model-fixtures til tests.

Indeholder MarketAssumptions og BiometricModel instanser med kendte parametre
til brug i analytiske kontrolcases.
"""

from pension.biometrics import BiometricModel
from pension.market import MarketAssumptions

# Nulrente, nul volatilitet → deterministisk afkast = 0
NUL_MARKED = MarketAssumptions(rf=0.0, volatilitet=0.0)

# Standardmarked: 3 % rente, 15 % volatilitet
STANDARD_MARKED = MarketAssumptions(rf=0.03, volatilitet=0.15)

# Nuldødelighed: A=0, B=0, c=1 (intensitet = 0 for alle aldre)
NUL_BIOMETRI = BiometricModel(A=0.0, B=0.0, c=1.0)

# Standardbiometri: Danish FSA-lignende Gompertz-Makeham parametre
STANDARD_BIOMETRI = BiometricModel(A=0.0005, B=0.00007585775, c=1.09144)
