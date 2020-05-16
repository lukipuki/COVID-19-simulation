Mathematicians Katarína Boďová and Richard Kollár predicted in March and April 2020
the growth of active cases during COVID-19 pandemic. Their model suggests polynomial
growth with exponential decay given by:

* <em>N</em>(<em>t</em>) = (<em>A</em>/<em>T</em><sub><em>G</em></sub>) ⋅
  (<em>t</em>/<em>T</em><sub><em>G</em></sub>)<sup>α</sup> /
  e<sup><em>t</em>/<em>T</em><sub><em>G</em></sub></sup>

Where:

* *t* is time in days counted from a country-specific "day one"
* *N(t)* the number of active cases (cumulative positively tested minus recovered and deceased)
* *A*, *T<sub>G</sub>* and *α* are country-specific parameters

They made two predictions, on March 30 (for 7 countries) and on April 12 (for 23
countries), each based on data available until the day before.

We have replicated their method and now publish automatic predictions every day. Note
that the method to compute these predictions slightly differs from Boďová and Kollár due
to differences in implementation details.

### References
* [Polynomial growth in age-dependent branching processes with diverging
  reproductive number](https://arxiv.org/abs/cond-mat/0505116) by Alexei Vazquez
* [Fractal kinetics of COVID-19 pandemic]
  (https://www.medrxiv.org/content/10.1101/2020.02.16.20023820v2.full.pdf)
  by Robert Ziff and Anna Ziff
* [Emerging Polynomial Growth Trends in COVID-19 Pandemic Data and Their Reconciliation with Compartment Based Models](https://arxiv.org/pdf/2005.06933.pdf) by Katarína Boďová and Richard Kollár
* March 30 predictions: [Facebook post](https://www.facebook.com/permalink.php?story_fbid=10113020662000793&id=2247644)
* April 12 predictions: Personal communication
