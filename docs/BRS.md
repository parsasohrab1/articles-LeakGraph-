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

## Users
Water utility network engineers and leak-detection crews.

## Scope
In: localisation from head drops on a network model. Out: hydraulic simulation with a full solver (EPANET), field integration, pipe-condition modelling.

## Success measures (on field data)
Top-1 and top-3 localisation accuracy, mean distance (hops or metres) to the true leak, coverage of the candidate set, digs saved.
