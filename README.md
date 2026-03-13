# pension-model

Aktuariel cashflow-projektionsmodel for en dansk unit-link pensionsportefølje.

Givet en portefølje af forsikringsaftaler, en rentekurve og en biometrisk model projekterer modellen forventede fremtidige cashflows for hver aftale og hvert produkt. Output er en CSV-fil med cashflows opdelt på produkt (præmier, omkostninger, ydelser, udgifter) og forventede opsparingskonti, alignet med Solvens II QRT-konventioner.

## Struktur

pension/
├── policy.py        # Aftale- og produktdataklasser
├── projection.py    # projicér() — hovedprojektionsalgoritme
├── biometrics.py    # BiometriskModel — dødelighedsintensiteter
├── market.py        # Markedsantagelser — rentekurve
└── output.py        # DataFrame til QRT-alignet CSV

## Status

Første implementation dækker en to-tilstands (levende/død) Markov-model med én fælles unit-link opsparingskonto per aftale. Solvens II-stressscenarier er uden for scope foreløbigt.
