# Software Requirements Specification (SRS)

| ID | Requirement | Module | Test |
|----|-------------|--------|------|
| FR-1 | Build a network from conductances; compute the response matrix of heads to nodal flows | `network.py` | `test_response_matrix_is_symmetric_positive`, `test_hops_are_symmetric_and_finite` |
| FR-2 | Choose k sensors by greedy maximisation of the minimum signature distance | `network.py` | `test_sensors_unique` |
| FR-3 | Posterior over leak nodes given head drops, with structured demand noise | `localize.py` | `test_posterior_normalised_and_finds_noise_free_leak` |
| FR-4 | Estimate leaked flow at a node | `localize.py` | `test_flow_estimate_recovers_flow` |
| FR-5 | Split-conformal candidate set at a target coverage | `localize.py` | `test_conformal_coverage_on_exchangeable_data` |
| FR-6 | Repair priority = posterior x flow | `localize.py` | `test_repair_priority_orders_by_product` |
| NFR-1 | Seeded, reproducible scenarios | `simulate.py` | `test_scenarios_are_seeded` |

**Model assumption:** the DC (resistive) linearisation of the network equations around one operating point; leaks and demand noise add linearly. Real networks are nonlinear and vary with demand level.
