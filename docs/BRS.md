# Business Requirements Specification (BRS)

**Product:** LeakGraph (basket id `nrwleak`), written from the product description in the iPetro basket and the code here. Not reviewed by the owner.

## Business problem
Non-revenue water (leakage) in urban distribution networks. Crews need to know where to dig; a point guess that is often wrong wastes digs. Pressure sensors are few, and demand fluctuations hide small leaks.

## Objectives
| ID | Objective |
|----|-----------|
| BO-1 | Localise a leak from a handful of pressure sensors |
| BO-2 | Give a candidate set with a stated coverage rather than a single guess |
| BO-3 | Rank repairs by probability times estimated leaked flow |
| BO-4 | State when the coverage guarantee fails (demand noise larger than assumed) |
| BO-5 | Keep the article and achievement card (`docs/REGISTRATION.md`) equal to `research/results.json`, with the article unsubmitted |

## Users
Water utility network engineers and leak-detection crews.

## Scope
In: localisation from head drops on a linearised network model, and detection on a published hydraulic simulation. Out: field integration, pipe-condition modelling.

## Success measures (simulated benchmark, not field data)
On BattLeDIM L-Town, which is an EPANET simulation: hour-level precision, recall, and false-alarm rate of a predeclared residual threshold against a split-conformal threshold. Top-1 localisation remains a synthetic-grid measure only.
