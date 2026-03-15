# Sandsynlighedsvægtede tilstandsvise depoter for markedsrentepolicer

## Setup: multi-tilstandsmodel

Lad den forsikrede befinde sig i tilstand $j \in \mathcal{J}$ til tid $t$.
Modellen er en endelig Markov-kæde med tilstandsrum $\mathcal{J}$,
intensitetsmatrix $\boldsymbol{\mu}(t) = (\mu_{jk}(t))_{j \neq k}$,
og samlede afgangsintensitet $\mu_j(t) = \sum_{k \neq j} \mu_{jk}(t)$.

## Betalingsfunktioner

Betalinger opdeles i en depotafhængig og en depotsuafhængig del:

- $b_j(t, x) = \beta_j(t)\,x + \gamma_j(t)$ — løbende betalingsrate i tilstand $j$
- $b_{jk}(t, x) = \beta_{jk}(t)\,x + \gamma_{jk}(t)$ — kontant betaling ved overgang $j \to k$

hvor $x$ betegner depotets størrelse. Positive værdier svarer til indbetalinger.

## Det betingede retrospektive depot

Lad $X^j(t)$ betegne det retrospektive depot betinget på at den forsikrede
er i tilstand $j$ til tid $t$. Thieles differentialligning er fremadrettet:

$$
\frac{d}{dt}X^j(t) = \Bigl[\delta(t) - \beta_j(t)
  + \sum_{k \neq j}\mu_{jk}(t)\bigl(1 + \beta_{jk}(t)\bigr)\Bigr]X^j(t)
  - \sum_{k \neq j}\mu_{jk}(t)\,X^k(t)
  - \gamma_j(t)
  + \sum_{k \neq j}\mu_{jk}(t)\,\gamma_{jk}(t)
$$

hvor $\delta(t)$ er den kontinuerte afkastrate.

Begyndelsesvilkår: $X^j(0) = 0$ for alle $j$ undtagen starttilstanden $i$, hvor $X^i(0) = X(0)$, startdepotet.

## Det sandsynlighedsvægtede depot

Lad $p^j(t)$ betegne sandsynligheden for at befinde sig i tilstand $j$
til tid $t$ (ubetinget, fra starttilstand $i$ til tid $0$). Fremskrivning via
Kolmogorovs forlæns ligning:

$$
\frac{d}{dt}p^j(t) = \sum_{k \neq j} p^k(t)\,\mu_{kj}(t) - p^j(t)\,\mu_j(t)
$$

med $p^i(0) = 1$, $p^j(0) = 0$ for $j \neq i$.

Det sandsynlighedsvægtede retrospektive depot er:

$$\tilde{X}(t) = \sum_{j \in \mathcal{J}} p^j(t)\,X^j(t)$$

## Numerisk løsning

Begge ligningssystemer er fremadrettede og løses simultant for $t = 0, h, \ldots, T$:

$$
X^j(t+h) \approx X^j(t) + h\Bigl[
  \Bigl(\delta(t) - \beta_j(t) + \sum_{k \neq j}\mu_{jk}(t)\bigl(1+\beta_{jk}(t)\bigr)\Bigr)X^j(t)
  - \sum_{k \neq j}\mu_{jk}(t)\,X^k(t)
  - \gamma_j(t)
  + \sum_{k \neq j}\mu_{jk}(t)\,\gamma_{jk}(t)
\Bigr]
$$

$$
p^j(t+h) \approx p^j(t) + h\Bigl[\sum_{k \neq j}p^k(t)\,\mu_{kj}(t)
  - p^j(t)\,\mu_j(t)\Bigr]
$$

Kombiner: $\tilde{X}(t) = \sum_{j \in \mathcal{J}} p^j(t)\,X^j(t)$.

## Eksempel: to-tilstandsmodel (aktiv / død)

$\mathcal{J} = \{a, d\}$, $\mu_{ad}(t) = \mu(t)$ (dødelighed), $X^d(t) = 0$.

$$
\frac{d}{dt}X^a(t) = \Bigl[\delta(t) - \beta_a(t) + \mu(t)\bigl(1 + \beta_{ad}(t)\bigr)\Bigr]X^a(t)
  - \gamma_a(t) + \mu(t)\,\gamma_{ad}(t)
$$

Det sandsynlighedsvægtede depot reducerer til:

$$\tilde{X}(t) = p^a(t)\,X^a(t)$$

hvor $p^a(t) = \exp\!\Bigl(-\int_0^t \mu(s)\,ds\Bigr)$.
