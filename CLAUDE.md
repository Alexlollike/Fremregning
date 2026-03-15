# CLAUDE.md

## Rolle og ansvar

Denne fil definerer matematiske konventioner som Claude Code skal følge strengt.
Afvigelser fra disse formler kræver eksplicit godkendelse.

Kodeansvar: arkitektur, struktur, test, tooling.
Aktuarfagligt ansvar: Alexander. Spørg ved tvivl — gæt ikke.

---

## Tidskonvention

Diskret månedlig fremregning. $t$ er månedsnummer fra 0. Alder ved trin $t$: $x + t/12$.

---

## Depotfremregning

### Opsparingsperiode (alle produkter)

$$D_{t+1} = \bigl(D_t + \pi - \delta_{\text{liv},t}\bigr) \cdot (1 + r_t) \cdot (1 - \alpha) - U_t$$

### Livrente i udbetalingsperiode (uden tilbagebetalingsgaranti)

Dødsfaldsdækning er ophørt: $\delta_{\text{liv},t} = 0$. Dødelighedsgevinster tilfalder overlevende forsikringstagere:

$$D_{t+1} = D_t \cdot (1 + r_t + \mu_t) \cdot (1 - \alpha) - U_t$$

hvor $\mu_t = \mu(x + t/12)/12$.

### Ratepension/aldersopsparing i udbetalingsperiode

Dødsfaldsdækning er ophørt: $\delta_{\text{liv},t} = 0$. Ingen dødelighedsgevinster:

$$D_{t+1} = D_t \cdot (1 + r_t) \cdot (1 - \alpha) - U_t$$

---

## Trin-for-trin fremregning

**Trin 1 — Nettorisiko og risikopræmie:**

Kun i opsparingsperioden:

$$R_t = S - D_t$$
$$\delta_{\text{liv},t} = \mu_t \cdot R_t$$
$$D_t^* = D_t + \pi - \delta_{\text{liv},t}$$

Negative $R_t$ er tilladt og fortolkes som dødelighedsgevinst til policen. I udbetalingsperioden bortfalder dødsfaldsdækningen og $\delta_{\text{liv},t} = 0$.

**Trin 2 — Investeringsafkast:**

Risikoneutralt (certainty equivalent): $\mu = r_f$

$$r_t = \exp\!\left(\left(r_f - \tfrac{1}{2}\sigma^2\right)\tfrac{1}{12} + \sigma\sqrt{\tfrac{1}{12}}\,\varepsilon_t\right) - 1, \quad \varepsilon_t \sim \mathcal{N}(0,1)$$

Livrente i udbetalingsperiode: afkastleddet er $(1 + r_t + \mu_t)$ jf. depotformlen ovenfor.

**Trin 3 — Depotomkostning:**

Fratrækkes som løbende procentsats $\alpha$ af den investerede formue efter afkast.

**Trin 4 — PAL-skat (påvirker ikke depotet):**

$$\text{PAL}_t = \frac{0{,}153}{12} \cdot \max\!\bigl(D_t^* \cdot r_t,\, 0\bigr)$$

Akkumuleres som acontoforpligtelse på selskabsniveau:
$$\text{PAL}_t^{\text{aconto}} = \text{PAL}_{t-1}^{\text{aconto}} + \text{PAL}_t$$

Nulstilles ved afregning til SKAT. Negativt afkast giver nul bidrag men fremførselsberettiget underskud.

**Trin 5 — Udbetaling $U_t$:**

Opsparingsperiode: $U_t = 0$

Ratepension/aldersopsparing: fast månedlig rate beregnet én gang ved konvertering.

Livrente — dynamisk, genberegnes hver måned:
$$U_t = \frac{D_t}{\ddot{a}_{x+t} \cdot 12}, \qquad \ddot{a}_{x+t} = \texttt{annuityPV}(x+t,\, r)$$

---

## Variabelnavne (Python)

| Symbol | Python |
|--------|--------|
| $D_t$ | `depot` |
| $\pi$ | `praemie` |
| $\delta_{\text{liv},t}$ | `risikopraemie` |
| $S$ | `doedsfaldssum` |
| $R_t$ | `nettorisiko` |
| $r_t$ | `afkast` |
| $\alpha$ | `omkostningspct` |
| $U_t$ | `ydelse` |
| $\mu_t$ | `doedsintensitet` |
| $\sigma$ | `volatilitet` |
| $\ddot{a}_{x+t}$ | `livrente_pv` |
| $\text{PAL}_t$ | `pal_skat` |

---

## Markov-model med flere tilstande

### Tilstandsrum

Tilstandsrummet indeholder $N$ tilstande $\{s_0, s_1, \ldots, s_{N-1}\}$.
Mindst én tilstand er absorberende (fx $\text{doed}$); de øvrige er transiente (fx $\text{aktiv}$, $\text{invalid}$).

### Intensitetsmatrix og overgangsmatrix

Intensitetsmatrix $Q(t)$ ved alder $x + t/12$:

$$Q_{ij}(t) = \mu_{ij}(x + t/12), \quad i \neq j$$
$$Q_{ii}(t) = -\sum_{j \neq i} Q_{ij}(t)$$

Månedlig overgangsmatrix (Euler-approksimation):

$$P(t) \approx I + Q(t) \cdot \tfrac{1}{12}$$

### Sandsynlighedsvektor

$$\pi(t) = \bigl[\pi_{s_0}(t),\, \pi_{s_1}(t),\, \ldots\bigr], \quad \sum_s \pi_s(t) = 1$$

Opdatering:

$$\pi_j(t+1) = \sum_i \pi_i(t) \cdot P_{ij}(t)$$

### Tilstandsbetingede depoter

Hvert transient tilstand $s$ har et betinget depot $D_s(t)$, fremregnet med de cashflows der gælder for tilstand $s$. Det absorberende $\text{doed}$-depot kan være $>0$ i udbetalingsperioden (arvingernes ydelse).

### Cashflow-regler (produktdefinition)

Et produkt er defineret ved to typer regler:

- **Tilstandscashflow:** Løbende udbetaling $U_s(t)$ mens den forsikrede er i tilstand $s$.
- **Overgangscashflow:** Éngangsudbetaling $K_{ss'}(t)$ ved overgang $s \to s'$ i trin $t$.

### Forventede størrelser (til regnskab)

$$\mathbb{E}[D(t)] = \sum_s \pi_s(t) \cdot D_s(t)$$

$$\mathbb{E}[U(t)] = \sum_s \pi_s(t) \cdot U_s(t) + \sum_{s,s'} \pi_s(t) \cdot P_{ss'}(t) \cdot K_{ss'}(t)$$

$$\mathbb{E}[\text{PAL}(t)] = \sum_s \pi_s(t) \cdot \text{PAL}_s(t)$$

### Variabelnavne (Markov-udvidelse)

| Symbol | Python |
|--------|--------|
| $\pi(t)$ | `pi` |
| $Q(t)$ | `q_matrix` |
| $P(t)$ | `p_matrix` |
| $D_s(t)$ | `depot_per_tilstand[s]` |
| $U_s(t)$ | `cashflow_per_tilstand[s]` |
| $K_{ss'}(t)$ | `overgangscashflow` |
| $\mathbb{E}[D(t)]$ | `forventet_depot` |
| $\mathbb{E}[U(t)]$ | `forventet_ydelse` |
| $\mathbb{E}[\text{PAL}(t)]$ | `forventet_pal_skat` |

---

## Hvad Claude Code ikke må

- Ændre diskretiseringsrækkefølgen uden godkendelse
- Introducere nye formler eller approksimationer uden godkendelse
- Antage noget om dækningsvalg, præmiestruktur eller produktparametre — spørg i stedet
