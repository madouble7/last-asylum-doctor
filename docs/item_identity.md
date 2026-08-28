# Canonical item identity

The Doctor has one shared item registry so the same economic item can later connect shop acquisition, game upgrade costs, and progression calculations.

Canonical identity is deliberately separate from source vocabulary. A source record retains its original name, while aliases and domain keys point to a canonical Doctor item.

| Canonical Doctor item | Source terminology / bridge | Meaning |
| --- | --- | --- |
| `speedup` | all package denominations and task types | One economic item; base unit is one minute |
| `grain` | research `farms`; workbook Farm/Farms aliases | Resource identity bridge only |
| `timber` | research `lumber`; workbook Lumber alias | Resource identity bridge only |
| `herbs` | research `herbs` | Same logical item; research spelling remains unchanged |
| `study-scroll` | research `study_scroll` | Same logical item; source underscore remains unchanged |
| `refined-iron` | Refined Ore | Explicit tracker equivalency |
| `raven-gear-chest-lv5` | Level 5 Raven Gear; Raven Gear Lv5 | Explicit tracker equivalencies |

The current research corpus is not rewritten. Its `research_level_costs.resource_identifier` values stay exactly as sourced. The economic database stores bridge rows in `item_domain_keys(domain='research_cost')` instead.

Supply containers remain items in their own right. For example, `SSR Antitoxin Supply` is not replaced by Antitoxin: it has a context-specific conversion to 5.4M Antitoxin at Sanctuary Lv26. Resource Supply and Deluxe Choice Chest relationships are choice graphs, so their alternatives must never become an additive item bundle.

Item identity is factual plumbing, not a strategic ranking. A bridge only says that two source terms refer to the same Doctor resource; it does not say which resource is worth buying or spending.

