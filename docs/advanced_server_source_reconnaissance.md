# Advanced-server public-source reconnaissance

Investigation date: 2026-08-27  
Player context: Server 283, Sanctuary 26  
Scope: public-source reconnaissance only; no final progression recommendation

## A. Executive summary

The public Last Asylum: Plague information ecosystem is young, fragmented, and surprisingly useful. No single source can answer the project's core question safely. The strongest research program is a three-layer combination:

1. **Exact-data layer:** [Last Asylum Database](https://lastasylumdatabase.com/), [SatoriMeta](https://satorimeta.com/en/last-asylum/), and [lastasylumwiki.com](https://lastasylumwiki.com/) expose costs, level tables, effects, requirements, breakpoints, and calculators. These are the best starting points for calculations, but their conflicting snapshots must be versioned and checked in game.
2. **Player-strategy layer:** [VØID Dominion](https://rtfm.codes/) identifies Server 237 and publishes event point tables and a broad current guide; Krris Gaming identifies Server 125; Chuppergaming RTS, KorpezGaming, v1ne1c, LastAsylumBR, and others show mechanics in video. These sources explain what experienced players actually prioritize.
3. **Future-horizon layer:** Chuppergaming's Era of Revival videos, current data sites exposing Awakening and Exclusive Weapons, and older-kingdom Era guides show systems substantially beyond the stated Server 283 context. They establish a plausible horizon, not a rollout date.

The best immediate finding is methodological: **present optimization and future preparation must be researched as separate claim types.** A current S26 claim can often be checked against exact tables and the user's game. A future claim may be observable on Kingdoms 33–64 or Server 125 yet still be wrong for Server 283's eventual build, schedule, or balance.

The strongest public coverage is currently:

- exact Sanctuary/building and research costs;
- hero Antitoxin, Skill Badge, star/shard tables;
- UR gear level and promotion costs;
- Raven level, Fruit/Essence, skill milestones, gear, evolution, and Epigraph concepts;
- recurring Alliance Duel, Survival Battle, Kingdom War, and Elixir Scramble timing;
- Era of Revival system discovery.

The weakest coverage is:

- exact marginal stat growth for every hero skill and gear slot under the current build;
- current gear-cap and Raven-gear-slot truth after recent reworks;
- exact Curio shard costs and marginal gains;
- MR gear costs and conversion rules;
- Lord Specialty/Resistance cost curves;
- advanced troop combat formulas, Morale, and T10 return on investment;
- reliable public guides for Arena of Fate, Treasure Digger, Dwarf Mine, and several seasonal events;
- a verified server-to-season rollout chronology.

The public ecosystem supports well over 25 useful sources without padding. It also contains obvious content-marketing and derivative guides. Such pages are useful for discovery but should not become factual authorities unless screenshots, exact tables, or independent player evidence corroborate them.

The project's 20/80 allocation is appropriate. Early-game material should be harvested only for compounding mistakes—permanent queues, Development research, active-alliance benefits, main-squad concentration, event timing, and avoiding stranded upgrades. Most collection effort should target S26–30 cost/effect curves and the resources that bridge into Era systems.

## B. Research methodology

### Scope and access discipline

Research used ordinary public web pages, public search results, public Reddit threads, and public YouTube watch/search pages. No login wall, private Discord, restricted spreadsheet, access control, or paywall was bypassed. YouTube caption-track availability was checked from public video metadata; full transcripts were not copied into this report.

The repository was inspected read-only to establish its current baseline: the project already recognizes **18 research trees** and has structured factual science data. Existing application code, schemas, databases, and progression documents were not changed.

### Search approach

Searches combined the exact game title with:

- Sanctuary 25/26/30, research, Elite Troop, T10, offensive/defensive tactics;
- heroes, tiers, formations, stars, shards, skills, Hall of Honor, Awakening;
- gear, Gearstones, UR/MR Blueprints, Tempered Steel, promotion;
- Raven, Fruit, Essence, gear, evolution, Epigraphs;
- Curios and Universal Curio Shards;
- Alliance Duel, Kingdom War, Survival Battle, Elixir Scramble, Demon King, Cheese Trap, Caravan, and later events;
- Era of Revival, Lord Specialty, Resistance, Exclusive Weapons, and older kingdoms/servers.

YouTube was also queried directly because general web search returned only a small fraction of the available videos. For selected videos, the public player metadata supplied exact publication date, channel, duration, description, and caption-track presence.

### Claim discipline

Every harvested claim should receive one of these labels:

| Label | Meaning | Example handling |
| --- | --- | --- |
| `FACT` | An exact value or observable mechanic | Store value, unit, game context, timestamp, and evidence. |
| `STRATEGY` | A player's choice or prioritization | Attribute to the source; do not state as game fact. |
| `FUTURE_WARNING` | A claim that present behavior affects a later system | Record current action, future dependency, server/era, and uncertainty. |
| `VERSION_SIGNAL` | A contradiction or mechanic that may have changed | Preserve both observations and open a verification task. |

### Server chronology

Server number is chronology evidence, not a universal clock. This report uses three practical bands:

- **Near Server 283:** roughly the same broad cohort; Server 237 is the best identified example found.
- **Moderately older:** lower-numbered servers whose systems may be weeks or phases ahead; Server 159 account evidence is weak but illustrative.
- **Significantly older/endgame:** Server 125 and explicitly identified Kingdoms 33–64/Era accounts.

The bands do not imply equal launch cadence, identical regional rollout, or a fixed number of days per server gap.

## C. Source-quality framework

Each catalog entry is scored 1–5 on seven dimensions:

- **F** — Freshness: recent and maintained.
- **A** — Advanced-server relevance: older-server or late-system visibility.
- **N** — Numerical data quality: exact, complete, internally checkable data.
- **S** — Strategy depth: reasoning, tradeoffs, and prioritization.
- **26** — Sanctuary 26–30 relevance.
- **P** — Future-preparation value.
- **V** — Verifiability: identifiable context, screenshots/tables, provenance, and ease of in-game checking.

A score is a routing aid, not a truth probability. A fresh marketing guide can score high on discovery value but low on verifiability. An older exact table can score high on numerical value while carrying major drift risk.

Priority tiers:

- **Tier 1 — systematic harvest:** unusually strong data, context, or repeatable creator coverage.
- **Tier 2 — targeted harvest:** useful for particular systems or corroboration.
- **Tier 3 — leads only:** potentially helpful but derivative, weakly contextualized, or drift-prone.

## D. Prioritized source catalog

This catalog contains 34 genuinely useful sources: 16 sites/pages below and 18 videos in section F. Video IDs `Y1`–`Y18` are part of this prioritized catalog and carry the same scoring fields.

### Tier 1 and Tier 2 sites/pages

| ID | Priority | Source; type; creator/site | Published/updated; server/stage | Strongest topics | Weaknesses / drift risk | Scores F/A/N/S/26/P/V | Recommended use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 1 | [Last Asylum Database](https://lastasylumdatabase.com/); structured fan database | Current crawl 2026-08; server unstated; includes Awakening/EW | 46 buildings, 31 heroes, Raven, 35 Curios, 348 nodes/18 trees, Gearstones, Alliance Tech, VIP | Snapshot date and server not exposed per record; strategy-light; some internal/current-guide conflicts | 5/4/5/1/5/5/4 | Primary factual candidate; ingest/version exact tables, then validate current S283 values. |
| D2 | 1 | [SatoriMeta Last Asylum hub](https://satorimeta.com/en/last-asylum/); data tools | Live 2026-08; server unstated; endgame data present | Building calculator, item/chest tools, hero/Hall tables, exact gear, Awakening and Exclusive Weapon data | Claims game-data provenance but lacks visible build/server tag; some values differ from guides | 5/5/5/2/5/5/4 | Second exact-data authority; compare record-by-record with D1 and current game. |
| D3 | 1 | [lastasylumwiki.com compendium](https://lastasylumwiki.com/); data + strategy wiki | Updated 2026-04-26 on core pages; server mostly unstated | Hero costs, Skill Badges, Raven breakpoints, UR gear costs, research, Expedition | Older snapshot; tables contain gaps; gear cap conflicts with newer sources | 3/3/5/4/5/3/4 | Harvest its clean cost curves and warnings with explicit snapshot date. |
| D4 | 1 | [VØID Dominion](https://rtfm.codes/); server guide/database | Updated 2026-08-26; **Server 237, day 81** | Current event point table, Alliance Duel, Elixir, KvK, heroes, formations, gear, skills, F2P spending | Near rather than far-future; some advice alliance-specific; not a raw-data export | 5/3/4/5/5/2/5 | Best near-S283 contextual benchmark; systematically review all pages and future updates. |
| D5 | 1 | [Raven Upgrade Costs](https://lastasylumwiki.com/docs/raven-upgrade-costs/); table/guide | Updated 2026-04-26; server unstated; Raven to 100 in visible table | Fruit/Essence by breakpoint, critical-upgrade note, unknown-row disclosure | Stops short of newer level/evolution horizon; older mechanics possible | 3/3/5/4/4/3/4 | Seed exact Raven cost model; verify each milestone in current build. |
| D6 | 1 | [Gearstone Cost: UR Gear](https://lastasylumwiki.com/docs/gearstone-cost-ur-gear/); table/guide | 2026-04; server unstated; UR→MR boundary shown | Gearstones, Herbs, UR Blueprints, Tempered Steel, promotion stages, dismantling warning, MR Blueprint at 5★ | Visible level table ends at 40; newer videos claim rework/cap changes | 3/4/5/4/5/5/4 | Seed gear cost/recovery model and identify exact rework checks. |
| D7 | 1 | [Hero Upgrade Costs](https://lastasylumwiki.com/docs/hero-upgrade-costs/); table/guide | Updated 2026-04-26; server unstated; hero level 150 | Antitoxin curve, Skill Badges, stars, shards, Hall of Honor trigger | Some column semantics need validation; no per-skill marginal effect table | 3/4/5/3/5/4/4 | Primary hero-cost seed; pair with hero skill facts from D1/D2. |
| D8 | 1 | [Research Guide](https://lastasylumguides.com/2026/07/14/last-asylum-research-guide/); strategy guide; Berdy | Published 2026-07-14, updated 2026-08-23; server unstated | Development, Alliance Duel, faction hero tech, Soldier, Squad 1, Elite Troop/T10 and Study Scroll tradeoff | Broad ordering is opinion; omits many of the project's 18 trees | 5/3/2/4/5/3/3 | Strategy hypothesis set; test orders against exact node costs/effects. |
| D9 | 1 | [Raven Upgrade Guide](https://lastasylumguides.com/2026/08/26/raven-upgrade-guide/); current guide; Berdy | 2026-08-26; server unstated; Raven evolution to 900 | Level 110 skill target, eight reported gear pieces, gear sources, evolution/Epigraph stages, skins | Conflicts with D1's six-slot display and max-level presentation; provenance not explicit | 5/5/4/4/4/5/3 | Best current Raven horizon map; treat conflicting counts as verification tasks. |
| D10 | 1 | [Era of Revival guide](https://www.ldshop.gg/blog/last-asylum-plague/era-of-revival-event.html); commercial guide | 2026-07-13; says Kingdoms 33–64 entered Era | Lord Specialty/Resistance, Awakening, EW, Revival League, Era Enhancement, MR Blueprints | Top-up marketing; author context/server not shown; advice may be derivative | 4/5/2/3/2/5/2 | Discovery checklist only; corroborate every mechanic with videos/data/current older-server screens. |
| D11 | 2 | [Research Lab Guide](https://lastasylumwiki.com/docs/research-lab-guide/); strategy guide | Updated 2026-04-26; server unstated | Development/Full Development, Soldier, Squad 1, Alliance Duel, Elite, tactics, Caravan | Covers nine categories vs current 18-tree corpus; priority claims lack math | 3/3/2/4/5/2/3 | Preserve as explicit drift example and a strategy-claim source. |
| D12 | 2 | [Shop Guide](https://lastasylumguides.com/2026/07/24/shop-guide/); economy guide; Berdy | 2026-07-24; server unstated | Acquisition routes and relative purchase tiers for shards, Essence, Curios, Blueprints | Shop prices/stock are volatile; recommendations not budget-normalized | 4/3/3/4/5/3/3 | Map repeatable acquisition; verify stock, reset cadence, and S283 prices. |
| D13 | 2 | [Kingdom War guide](https://lastasylumguides.com/2026/08/24/kingdom-war-kvk-event-guide/); event guide; Berdy | 2026-08-24; server unstated; eight-kingdom bracket | KvK phases, cross-event scoring, Demon King, caravans, Survival Battle, Elixir | Exact values may be bracket/version-specific; no server label | 5/4/4/4/4/4/3 | Event dependency map and candidate point values for in-game verification. |
| D14 | 2 | [Alliance Duel Guide](https://last-asylum-plague.fandom.com/wiki/Alliance_Duell_Guide); community wiki | Crawled 2026-06; server unstated | Day-by-day hoarding and base point values; candidly marks unconfirmed base stats | Editable, serverless, and some numbers explicitly uncertain | 4/2/3/4/5/2/3 | Corroborate timing claims; never promote its points to facts without screens. |
| D15 | 2 | [KvK Academy](https://www.zaraelsguide.com/kvk-academy); visual/community guide; Zarael Rose | Current 2026-08 crawl; server unstated | Territory levels, siege, detailed Alliance Duel timing, T9→T10 promotion, Skill Badge day | Many assets are image-led; numerical provenance and server are not stated | 4/3/3/4/5/3/3 | Visual playbook and second-source corroboration for event timing. |
| D16 | 2 | [Things I Wish I Knew Starting Out](https://www.reddit.com/r/LastAsylumPlague/comments/1vxrsvp/last_asylum_plague_things_i_wish_i_knew_starting/); Reddit discussion | 2026-08-25; several players, servers unstated | Main-march focus, meaningful buildings, event timing, alliances as resource multiplier, battle-report skepticism | Anecdotal, self-selected, very new thread; mixed stages | 5/2/1/4/4/2/3 | Source early compounding mistakes and recruit follow-up interview questions. |

### Coverage by research category

| Category | Best current public sources | Coverage judgment |
| --- | --- | --- |
| Development/economy research | D1, D2, D8, D11, Y8 | Exact costs strong; comparative return needs calculation. |
| Hero/faction research | D1, D8, D11, Y6/Y7 | Exact nodes available; outcome modeling weak. |
| Soldier/troop research | D1, D8, D11, Y5 | Node facts and training strategy available; combat ROI weak. |
| Squad research | D1, D8, D11 | Exact costs available; cross-tree marginal comparison absent. |
| Elite Troop/T10 | D1, D8, D11, D15, Y5 | Unlock relationship visible; full opportunity-cost model absent. |
| Offensive/Defensive tactics | D1, D11, D2 | Exact tables likely harvestable; public strategic analysis thin. |
| Alliance Duel research | D1, D4, D8, D14, D15, Y13/Y15 | Strategy strong; exact point multipliers need current verification. |
| Later/unknown trees | D1's current 18-tree corpus, D2, Era sources | Discovery incomplete; do not infer future trees from old nine-tree guides. |

### Event-source coverage map

This table maps the named event requirements even where public coverage is weak. Linked pages that are not IDs in the scored catalog are discovery leads, not additional counted catalog entries.

| Event/system | Best source route found | What it can answer | Remaining problem |
| --- | --- | --- | --- |
| Alliance Duel | D4, D14, D15, Y10, Y13; [LastAsylumPlague.com day guide](https://lastasylumplague.com/events/alliance-duel/) | Daily actions, hoarding rhythm, point tables, research multiplier | Current S283 league/bracket values and matchmaking rules. |
| Kingdom War | D13, Y11, Y14 | Bracket/phases, throne/tower play, cross-event contribution, shielding | Server-specific schedule, casualty rules, exact current rewards. |
| Survival Battle | [Berdy's Survival Battle page](https://lastasylumguides.com/2026/07/11/survival-battle-event/), D13–D16 | Theme overlap and four-hour-window planning | Exact S26 bracket/reward schedule and rotation. |
| Elixir Scramble | Y15, D4, D13 | Occupation/gathering logic, captains, KvK contribution | Current map and scoring after updates. |
| Demon King | [Berdy's Demon King page](https://lastasylumguides.com/2026/05/16/demon-king-event/), D13, Y11 | Damage-event role, KvK contribution, broad reward/acquisition route | Exact boss formula, formation optimization, difficulty scaling. |
| Cheese Trap | [Berdy's Cheese Trap page](https://lastasylumguides.com/2026/05/16/cheese-trap-event/), D12 | Basic event and Diamond-source discovery | No strong advanced-server optimization or exact modern reward table found. |
| Caravan | [Berdy's Caravan guide](https://lastasylumguides.com/2026/08/23/caravan-guide/), D4, D13 | Dispatch/plunder attempts, reward quality, event timing | Expected value by rarity and cross-server risk. |
| Arena of Fate | D4 says its guide covers four arenas; otherwise search results were weak | Candidate source family only | Needs a dedicated, current, publicly verifiable guide and reward table. |
| Treasure Digger | Y4/Y8 descriptions mention Covert Operation Treasure Digger as a gear-material route | Acquisition lead only | Mechanics, cadence, drop table, and whether the name denotes a Covert Op subtype or event. |
| Dwarf Mine | No strong indexed public Last Asylum source found | Nothing reliable yet | Confirm exact English name, unlock context, rules, and rewards from S283 UI/older-server video. |
| Crystal Cluster Valley | [Berdy's event guide](https://lastasylumguides.com/2026/07/12/crystal-cluster-valley-event-guide/) | Timed spawn plan, skills, reward table including Essence/Steel/shards | Bracket/version and opportunity cost of combat resources. |
| Canyon Conquest | [Berdy's event guide](https://lastasylumguides.com/2026/05/30/canyon-conquest-event/) and Krris video back catalog | Alliance event structure and Fame Medal route | Current matchmaking and advanced tactical evidence. |
| Undead Siege | Y1/Y6 channel back catalog and [Berdy's guide](https://lastasylumguides.com/2026/08/22/undead-seige-event-guide/) | Later recurring PvE/event discovery | Exact reward/value comparison and spelling/version normalization. |
| Seasonal/Era events | Y1–Y3, D10 | Era timeline, Covenant/League/Lord/Resistance discovery | Official schedule, rollover, and Server 283 entry conditions. |

### Spending/economy source coverage

| Spend profile | Useful sources | Information value | Caution |
| --- | --- | --- | --- |
| F2P | D4, D8, D12, D16, Y4–Y7, Y15/Y16 | Queue utilization, main-march focus, repeatable shops/events, timing, alliance multiplier | “F2P” videos sometimes contain sponsored top-up links; evaluate the mechanic separately. |
| Low spender | D4's `$0–$50` path, [Berdy's Packs Guide](https://lastasylumguides.com/2026/08/02/packs-guide/), Y4/Y7 | Permanent queues, weekly/pass value, shop efficiency | Pack contents and regional prices change; normalize by actual S283 price and marginal resource value. |
| High spender | D10 and other Era commercial guides, Y2's Era offer discussion | Discovery of newly monetized Awakening/EW/Lord/Resistance bottlenecks | Strongest commercial bias and weakest independent testing; use only to enumerate systems/resources. |
| Regret/trap evidence | D6, D12, D16, Y4/Y7/Y8/Y9, Reddit Raven debate | Dismantle losses, spreading investment, buying repeatable resources at premium rates, disputed Epigraph priorities | “Trap” language is creator framing until cost and alternative use are quantified. |

## E. High-value creator/site profiles

### Last Asylum Database

- **Best at:** broad exact factual coverage and machine-readable-style tables.
- **Stage/server:** server unstated; contains Awakening, Exclusive Weapons, later Raven/Epigraph, and all 18 current research trees.
- **Currentness:** actively deployed in August 2026; individual record version tags are missing.
- **Numbers vs opinion:** overwhelmingly numbers; little strategy.
- **S26 use:** excellent for costs, prerequisites, research, Curios, gear, and buildings.
- **Future use:** strong discovery signal because later systems already appear in its data.
- **Back catalog:** yes—systematic, with source hash/retrieval time and change detection.

### SatoriMeta

- **Best at:** exact game-data-derived calculators, hero/Hall facts, gear progression, Awakening, and Exclusive Weapons.
- **Stage/server:** server unstated; data reaches endgame systems.
- **Currentness:** live and actively crawled in August 2026; claims patch-oriented JSON replacement.
- **Numbers vs opinion:** mostly numbers and tools.
- **S26 use:** excellent for cumulative building requirements and gear/hero calculations.
- **Future use:** excellent lead source for systems not yet visible to Server 283.
- **Back catalog:** yes—harvest schemas and version, but independently validate its claimed game-data provenance.

### lastasylumwiki.com

- **Best at:** clean cost tables plus explicit player-facing breakpoints and warnings.
- **Stage/server:** mostly unstated; Expedition page credits Dawar `[S4 TOTK]`, demonstrating at least some very old-server contribution.
- **Currentness:** core pages updated 2026-04-26, so rework risk is high.
- **Numbers vs opinion:** strong tables with short strategy overlays.
- **S26 use:** excellent seed data for hero, Raven, gear, and Sanctuary calculations.
- **Future use:** moderate; it exposes MR Blueprint use but not the full Era layer.
- **Back catalog:** yes, once per-page snapshot dates and known gaps are retained.

### VØID Dominion / Server 237

- **Best at:** a living near-cohort operational guide, exact event scoring, F2P spending, formations, and alliance practice.
- **Stage/server:** Server 237, day 81 on 2026-08-26.
- **Currentness:** very high; the site reports frequent August updates.
- **Numbers vs opinion:** both; point tables say they omit actions whose numbers are not shown rather than guess.
- **S26 use:** exceptionally strong because Server 237 is closer to Server 283 than endgame sources.
- **Future use:** limited until that server advances, but its updates can become a longitudinal rollout log.
- **Back catalog:** yes, and archive snapshots over time.

### Chuppergaming RTS

- **Best at:** broad, timely, explanatory videos with on-screen systems; standout coverage for Era, Raven, gear, research, troops, and battle reports.
- **Stage/server:** server number not found in public metadata reviewed; creator explicitly says their Era of Revival season had finished by 2026-08-18.
- **Currentness:** very high, including August 2026 uploads.
- **Numbers vs opinion:** mix of displayed mechanics, worked examples, and personal strategy.
- **S26 use:** strong for gear/troop/hero mechanics and identifying what to measure.
- **Future use:** the best recurring English-language video source found.
- **Back catalog:** yes—systematically, starting with Era, gear rework, Raven, research, and battle reports.

### KorpezGaming

- **Best at:** long-form practical event/Raven walkthroughs with clear timestamps.
- **Stage/server:** server not stated in reviewed public metadata.
- **Currentness:** very high (August 2026 Raven and Alliance Duel guides).
- **Numbers vs opinion:** mostly strategy with screen-demonstrable mechanics.
- **S26 use:** strong for weekly timing, shop acquisition, and Raven/Epigraph choices.
- **Future use:** moderate; monitor for later-system updates.
- **Back catalog:** targeted review recommended.

### Krris Gaming

- **Best at:** concise hero, gear, event, and composition videos.
- **Stage/server:** explicitly **Server 125** in Y12, making it valuable advanced-server context.
- **Currentness:** active through mid-2026 in reviewed inventory.
- **Numbers vs opinion:** both, often quoting skill percentages; short format limits nuance.
- **S26 use:** useful for candidate hero/gear priorities.
- **Future use:** high because the server is substantially older than 283.
- **Back catalog:** yes, but corroborate rankings and dates because some descriptions say “2025” despite 2026 publication.

### v1ne1c | Last Asylum Guide

- **Best at:** detailed Russian-language gear and Kingdom War walkthroughs; the gear video has unusually high views for the niche.
- **Stage/server:** not found in reviewed metadata.
- **Currentness:** March–June 2026 for reviewed videos.
- **Numbers vs opinion:** mostly on-screen mechanics and upgrade sequences.
- **S26 use:** strong for gear crafting/promotion order.
- **Future use:** moderate.
- **Back catalog:** targeted review, with Russian transcription/translation quality checks.

### Berdy / Last Asylum Plague Guides

- **Best at:** wide topical breadth, current event pages, shops, Raven, research, formations, and troop concepts.
- **Stage/server:** not stated.
- **Currentness:** very high, with multiple August 2026 updates.
- **Numbers vs opinion:** mixed; some exact tables and many unmodeled priority judgments.
- **S26 use:** strong discovery and corroboration.
- **Future use:** strong for Raven evolution; Era coverage is currently limited.
- **Back catalog:** yes, but treat the site as one editorial source, not independent corroboration among its pages.

### Zarael's Plague Academy

- **Best at:** polished visual guides for gear, research/power systems, and weekly event coordination.
- **Stage/server:** not stated; community-curated.
- **Currentness:** active June–August 2026.
- **Numbers vs opinion:** many visual cards and strategy summaries; exact source provenance is thin.
- **S26 use:** strong as a manual-facing visual reference.
- **Future use:** moderate.
- **Back catalog:** targeted review, especially downloadable gear cards and Hall of Honor pages.

## F. YouTube source inventory

Caption availability below was checked against public YouTube player metadata on 2026-08-27. `YES-auto` means a public auto-generated caption track was advertised; `YES-manual` means a creator-provided English track was also present. It does not mean a transcript was copied. Numerical/strategy/future fields describe information value, not independent verification.

| ID | Priority; title; creator; URL | Published; context | Topic and information value | Transcript | Num / strategy / future | Drift risk and weakness | Scores F/A/N/S/26/P/V |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Y1 | 1; [The Complete Era of Revival Breakdown](https://www.youtube.com/watch?v=tAgVqvstPBY); Chuppergaming RTS | 2026-06-29; completed/active Era context; server unstated | Two-month/16-kingdom framing, Soldiers Rest, Lord systems, Marina Awakening, new buildings, release timeline | YES-auto | Y/Y/Y | Rollout specifics may differ by cohort | 4/5/3/5/2/5/4 |
| Y2 | 1; [Don't Start Era of Revival Without Watching This](https://www.youtube.com/watch?v=FrZc05xee0s); Chuppergaming RTS | 2026-08-18; creator says Era finished on their server | Post-season lessons: Lord Statue, Specialty fork, monsters, packs, early Resistance compounding | YES-auto | Y/Y/Y | Personal top-five advice; spender element | 5/5/2/5/2/5/4 |
| Y3 | 1; [Ultimate Research & Upgrade Guide — Era of Revival](https://www.youtube.com/watch?v=o2bZgHPWhIg); Chuppergaming RTS | 2026-07-30; Era | Lord Studio/Handyman time reductions, free speedups, city speed bonuses, S30 push context | YES-manual + auto | Y/Y/Y | Seasonal buffs may expire or change | 5/5/3/5/4/5/5 |
| Y4 | 1; [The Only Gear Guide You Will Ever Need](https://www.youtube.com/watch?v=SPj-rBfLYRs); Chuppergaming RTS | 2026-06-07; post-gear nerf/rework | Acquisition, conversion, role order, enhancement, promotion changes | YES-auto | Y/Y/N | Title explicitly says older guides are obsolete; requires rework date capture | 5/4/4/5/5/3/4 |
| Y5 | 1; [The Only Troop Guide You'll Ever Need](https://www.youtube.com/watch?v=4LiO1FPbZt8); Chuppergaming RTS | 2026-06-12; demonstrates T4→T9 example | One max Training Ground plus lower grounds, promotion-time arithmetic, Alliance Duel Day 5 | YES-auto | Y/Y/N | T9 example may not generalize to T10/current timers | 5/3/4/5/5/2/4 |
| Y6 | 1; [Ravens & Epigraph System Breakdown](https://www.youtube.com/watch?v=Sl90M9eAiNg); Chuppergaming RTS | 2026-04-21; server unstated | Unlocks, squad assignment, upgrade focus, F2P/spender framing | YES-auto | Y/Y/Y | Predates August Raven/evolution updates | 3/4/3/5/4/4/4 |
| Y7 | 1; [DO NOT Touch Your Raven Before Watching This](https://www.youtube.com/watch?v=MaTgA50P81s); KorpezGaming | 2026-08-08; server unstated | Skins, Essence, gear slots, shops, Epigraph priorities by faction, evolve stages | YES-auto | Y/Y/Y | Personal Epigraph choices are disputed in Reddit comments | 5/4/3/5/4/4/4 |
| Y8 | 1; [STOP Wasting Gears — Ultimate Gear Guide](https://www.youtube.com/watch?v=u3KYGVtI1gI); Asylum Commander | 2026-07-19; recent gear rework; says max enhancement 52 | Sources, workshop, class slot choices, promotion, Gearstones/Blueprint/“Temporal Steel” terminology | YES-auto | Y/Y/N | Very low view count; material naming and cap conflict with data sites | 5/4/4/4/5/3/3 |
| Y9 | 1; [Equipment Guide: Crafting Order, Leveling, Star Upgrades](https://www.youtube.com/watch?v=SiNKWfyrFLE); v1ne1c | 2026-06-06; Russian; server unstated | 19-minute detailed crafting, do-not-dismantle warning, swords first, levels and Blueprint order | NO public caption track detected | Y/Y/N | Translation/manual review required; rework timing uncertain | 4/4/4/5/5/3/4 |
| Y10 | 1; [HOW TO DOMINATE Last Asylum Alliance Duels](https://www.youtube.com/watch?v=2LJ11oTk20M); KorpezGaming | 2026-08-12; six-day current event | 22-minute day-by-day resource schedule and Saturday PvP | YES-auto | Y/Y/N | Server/league rules not stated | 5/3/4/5/5/2/4 |
| Y11 | 1; [The ULTIMATE KvK Rundown](https://www.youtube.com/watch?v=QjtaglYMb8c); KorpezGaming | 2026-06-28; Kingdom War | Cross-event phases, shops, caravans, Elixir, Demon King, Raven, healing/defense tactics | YES-auto | Y/Y/Y | Bundles several systems; exact values limited | 4/4/3/5/4/4/4 |
| Y12 | 1; [Top 5 UR Heroes](https://www.youtube.com/watch?v=7qZKyVQ51wk); Krris Gaming | 2026-06-15; **Server 125** stated | Exact skill percentages and PvP roles for Daskal, Annie, Nicole, Red Lady, Louis | YES-auto | Y/Y/Y | Tier ranking is opinion; description contains stale “2025” wording | 4/5/4/4/4/5/4 |
| Y13 | 2; [Moving Ahead in Alliance Duel Research Part 1](https://www.youtube.com/watch?v=GYaEpmJ_Vn4); Pro Noobs | 2026-04-04; server unstated | On-screen Alliance Duel research progression | NO public caption track detected | Y/Y/N | Low views, multi-part fragmentation, older snapshot | 3/3/3/3/5/2/3 |
| Y14 | 2; [Kingdom War Guide](https://www.youtube.com/watch?v=gQr81GwF0PA); LastAsylumBR | 2026-06-03; Portuguese captions | Points, targets, defense, towers, Sanctuary battles | YES-auto (Portuguese) | Y/Y/Y | Translation and server context needed | 4/4/3/4/4/3/3 |
| Y15 | 2; [Master the Elixir Scramble](https://www.youtube.com/watch?v=dO0tbJMcCVs); Chuppergaming RTS | 2026-02-19; server unstated | Occupation vs gathering, captains, rewards, cost of speedups/troops | YES-auto | Y/Y/N | Oldest strategic video in priority set; event may have changed | 2/3/3/5/4/2/4 |
| Y16 | 2; [How to Level Up Heroes the RIGHT Way](https://www.youtube.com/watch?v=C7wH29bw0ik); Chuppergaming RTS | 2026-06-17; mid-game | Damage dealer/tank/support sequence, one carry at a time, replacement warning | YES-auto | Y/Y/N | Specific hero meta and level economics may drift | 5/3/2/4/5/2/4 |
| Y17 | 2; [How to Read Battle Reports](https://www.youtube.com/watch?v=7rbobMa_UPQ); Chuppergaming RTS | 2026-08-20; current PvP | Diagnostic use of reports to separate hero, tech, gear, and stat weaknesses | YES-auto | Y/Y/Y | Teaches analysis rather than cost/value tables | 5/5/3/5/5/5/4 |
| Y18 | 2; [Last Asylum: Plague Tier List of Best Heroes](https://www.youtube.com/watch?v=vUFZdiYTt4c); Game Hydro | 2026-02-20; early game version | 28-minute early roster/meta baseline | YES-auto | Y/Y/N | High roster/version drift; server unstated | 2/2/2/3/3/1/3 |

### YouTube harvest notes

- **Review first:** Y1–Y4, Y6–Y12, and Y17. They have the strongest mix of currentness, future visibility, and demonstrable screens.
- **Use timestamp-level claims:** keep “what the creator says” separate from “what is visible in the UI.”
- **Capture account context from the video itself:** Sanctuary, Raven level, gear cap, server/kingdom, season week, and visible update UI matter more than channel subscriber count.
- **Treat auto captions as noisy:** names such as Daskal/Dhaskal and Tempered/Temporal Steel are common transcription or creator-wording failure points.
- **Do not infer independence from separate videos on one channel.** Several Chuppergaming videos constitute one creator lineage.

## G. Advanced-server intelligence

### Near Server 283

**Server 237 / VØID Dominion** is the most valuable identified near-cohort source. On 2026-08-26 it labeled itself day 81 and covered 32 heroes, Alliance Duel, Kingdom War, Elixir, four arenas, gear, skills, and 177 scoring actions. This is close enough to test present S26–30 applicability, yet far enough ahead to reveal systems or event maturity that Server 283 may not have reached.

Recommended treatment: archive its dated state weekly. A longitudinal Server 237 record may become more useful than a one-time guide because it can reveal the order in which mechanics appear.

### Moderately older servers

Public server identification is sparse. A current marketplace post for Server 159 shows a developed account with hero levels near 150, Raven/Epigraph investment, and named research completion percentages. It is **not included in the prioritized catalog** because sales copy is weak evidence, but it confirms useful reconnaissance targets: research-tree completion profiles, relative account Might allocation, and mature Raven/Curio contributions. It should never be used for recommendations or factual costs.

### Significantly older/endgame servers

- **Server 125 / Krris Gaming:** explicit server identity and on-screen hero/gear content make this the strongest named endgame creator context found.
- **S4 / Dawar credit:** the Expedition guide on lastasylumwiki.com credits Dawar `[S4 TOTK]`; the page is useful for Expedition math but should not be assumed to describe the current global build.
- **Kingdoms 33–64:** commercial Era guides state these kingdoms entered Era of Revival on 2026-07-13. This chronology is corroborated broadly by Chuppergaming videos showing Era mechanics, but the exact rollout statement still needs an official notice or an in-game screenshot from one of those kingdoms.

### Cross-stage strategic patterns worth testing

These are recurring `STRATEGY` claims, not final advice:

1. Concentrate hero, gear, Raven/Epigraph, Awakening, and Exclusive Weapon investment on one main march before spreading.
2. Prioritize permanent speed/queue/reward-multiplier systems because they compound through later content.
3. Time consumable use to overlapping Alliance Duel and Survival Battle windows.
4. Treat Study Scrolls as an opportunity-cost bridge between Alliance Duel and Elite Troop/T10 research.
5. Train lower-tier troops and promote during scoring windows when time and points are superior to direct top-tier training.
6. Preserve gear and materials until dismantling/refund behavior and later promotion requirements are known.
7. In Era, early Resistance and Lord progression may compound across the season; this is a future-warning claim needing exact costs and permanence checks.

## H. Future systems/seasons horizon

No dates below are predicted for Server 283.

| System | What it appears to do | Evidence | Server/era observed | Resources involved | Preparation signal to investigate now | Confidence | Unknown questions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Era of Revival | Large later phase/season layered over existing account progression; videos describe a two-month, 16-kingdom cycle | Y1–Y3, D10 | Older kingdoms; D10 says 33–64 from 2026-07-13 | Era currency, seasonal tasks/packs, existing build/research resources | Determine which stockpiles remain usable and which are season-only | High system existence; medium schedule | Permanent vs seasonal components; exact entry rule for 283; regional cadence |
| Lord Statue / Lord Evolution | Opens Specialty paths and Lord-wide skills | Y1–Y3, D10; D1 has a Lord Statue building record | Era | Specialty EXP/books, Lord skill items | Identify whether pre-Era items exist and expire; map fork reset rules | High | Exact skill tree, costs, resets, permanent carryover |
| Lord Specialty paths | Handyman/development vs Legion Commander/combat fork; may grant time reductions/free speedups | Y2, Y3 | Era on creator's server | Specialty EXP/books | Avoid assuming a path until exact opportunity cost is known | Medium-high | Full tree, respec price, account-stage thresholds, whether benefits persist after Era |
| Resistance | Gates or improves performance against stronger Era enemies; early gains reportedly compound | Y2, D10 | Era | Resistance-specific upgrade items; exact names unknown | Identify sources/caps and whether missed early income can be recovered | Medium-high | Formula, PvE/PvP scope, catch-up mechanics, permanence |
| Hero Awakening | Adds hero-specific break stages/stat ceilings beyond ordinary stars | D1 hero filter, D2 hero tables, Y1, D10 | Endgame data; Era | Hero-specific Awakening Shards/materials | Verify whether ordinary UR shards convert or remain separate | High existence | Eligible hero waves conflict; total shard/cost curve; prerequisites; refunds |
| Exclusive Weapons | Separate hero-specific progression with unique bonuses, not ordinary gear | D2, Y1, D10; D1 advertises EW data | Endgame/Era | Hero-specific and Omni EW shards/materials | Preserve flexibility until main long-term hero is confirmed | High existence | Unlock timing, universal-shard sources, star breakpoints, obsolescence/transfer |
| Soldiers Rest | Recovers some dead soldiers, changing late PvP loss economics | Y1; D1 lists Soldier's Rest to level 35 | Era/later data | Building resources and possibly recovery currency | Re-evaluate current fatality/healing research once exact mechanic is known | Medium-high | Recovery rate, capacity, timer, PvP modes, whether upgrades are seasonal |
| Revival Expedition League | Later single-march/league PvE/PvP reward layer | D10; Y1 release timeline | Era | Attempts, Resistance, Awakening/EW strength; Era rewards | Main-march concentration may have future value | Medium | Matchmaking, reward table, season reset, F2P access |
| Era Enhancement / skins | Turns Era features or skins into upgradeable permanent stats | D10 | Era | Era enhancement materials/currency | Avoid treating cosmetics as purely cosmetic until system verified | Medium | Which owned skins qualify, transfer/refund, permanent vs seasonal stats |
| MR gear | Tier beyond UR; Era guides list MR Blueprints as rewards and D6 shows MR Blueprint at UR 5★ | D6, D10, D2 | Endgame/Era | MR Gear Blueprints, Gearstones, Tempered Steel, Herbs, possibly new materials | Exact UR→MR conversion/reuse determines today's gear concentration value | High existence; low economics | Craft recipe, slot order, cap, refund, whether UR piece is consumed |
| Expanded Raven evolution/Epigraphs | Evolution reportedly reaches 900 with additional plans and newer eight-piece gear view | D9, Y7, D1/D2 | Later Raven state | Evolve Guides, duplicate Epigraphs, shards/chests, Raven gear | Track scarce Evolve Guides and avoid discarding duplicate systems blindly | High existence; medium current S283 applicability | Six vs eight gear slots; plan unlock levels; exact stat returns; update boundary |
| Later research/buildings | Current factual corpus has 18 trees; Era adds buildings and may change research speed incentives | D1, repository corpus, Y1–Y3 | Current/later build | Study Scrolls, ordinary resources, speedups, season bonuses | Preserve exact source snapshots and model tree unlock prerequisites | Medium | Are there Era-only research trees? Which use Study Scrolls? Do bonuses expire? |

## I. Resource-hoarding intelligence

This section records observed uses, scarcity signals, and player warnings. It deliberately does **not** issue a final save/spend recommendation.

| Resource | Current use | Future use / horizon | Scarcity and repeatable acquisition | Common regret or warning observed | Source support / confidence |
| --- | --- | --- | --- | --- | --- |
| UR Hero Omni Shards | Star/promote main heroes; Alliance Duel Hero day scoring | Awakening appears to use separate hero-specific materials, but a mature hero remains prerequisite value | Repeats in shops/events, usually top-tier or limited quantity | Spreading across roster; spending outside score overlap; investing in soon-benched heroes | D7, D12, D14–D16, Y12/Y16; high current, low direct Awakening conversion |
| Skill Badges | Raise hero skills; Hero-day scoring; linked to stars/shards in D7 | May remain important below/alongside Awakening; no verified conversion | Events/packs/Falcon sources; exact weekly income unknown | Upgrading every skill/hero without marginal-effect comparison | D7, D15, spending guides; medium-high |
| Gearstones | Enhance and promote hero gear | Still appears in advanced UR stages; likely part of MR transition but exact recipe unknown | Smelting Workshop, shops, events; repeatable but high cumulative demand | Spreading levels; dismantling without knowing refunds; old cap tables | D1–D3, D6, Y4/Y8/Y9; high current |
| UR Gear Blueprints | UR promotion/star thresholds | D6 shows escalating UR star gates before an MR Blueprint gate | Honor/shops/events; limited refresh quantities | Using on a non-core slot; assuming all promotion stages refund | D6, D12, Y4/Y8/Y9; high current |
| MR Gear Blueprints | Little/no ordinary current use before MR boundary | Required at/after high UR promotion and listed as Era reward | Appears rare and late-event gated; repeatability not established | Treating it as an ordinary UR Blueprint or spending before recipe is known | D6, D10, Zarael gear card; medium-high existence |
| Tempered Steel | Craft UR gear and promote advanced stages | Continues near MR boundary in D6/D2 | Craft/dismantle/event/shop sources; production rate vs demand unknown | Dismantling/crafting loops may lose Herbs or strand a slot; terminology sometimes misrendered “Temporal Steel” | D2, D6, Y4/Y8/Y9; high |
| Raven Essence | Breakthrough/milestone levels; Alliance Duel Day 1 scoring | Raven skill milestones and long evolution horizon increase total demand | Multiple weekly shops/events; consistently described as bottleneck | Using outside the scoring day; buying at poor diamond value; ignoring breakthrough curve | D5, D9, D12, D14/D15, Y6/Y7/Y10; high |
| Raven Fruit | Ordinary Raven stage progress; Alliance Duel Day 1 | Continues through higher levels | Falcon/Sanctuary collection, shops/events; more repeatable than Essence | Buying it when passive collection is adequate; consuming outside event overlap | D5, D9, Y6/Y7, Reddit Raven thread; high current |
| Study Scrolls | Alliance Duel and Elite Troop research; some nodes consume only Scrolls | Possible later research demand not mapped | Alliance Duel/event rewards; scarce relative to full tree costs | Spending on Elite Troop too early and delaying point-multiplier tech, or the reverse without math | D1, D8, D11, D15, repository data; high current, unknown future |
| Antitoxin | Hero levels; Alliance Duel/Survival Hero windows | Mature hero levels remain useful under Awakening; Awakening resource itself appears separate | Workshop, supplies, shops/events; demand spikes sharply in D7 | Spreading across heroes; spending outside event overlap; confusing supply chest value with fixed amount | D7, D12, D14–D16, Y16; high |
| Universal Curio Shards | Curio levels/stars and permanent bonuses | Era introduces/adds Curios; old shards may retain flexible value | Shops/events/chests; some guides rate shop purchase low, implying price inefficiency rather than low utility | Spending before Curio marginal table or on obsolete/low-impact Curio | D1, D12, Curio page; medium |
| Recruit Tickets | Hero recruitment and Alliance Duel scoring | Future hero banners/pools may alter expected value; no reliable public schedule found | Recurring event/shop rewards | Pulling outside scoring windows or before pool/banner context is known | D14/D15, Y10, Reddit threads; medium-high current |
| Speedups | S26–30 builds/research/training; recurring event scoring | Era Handyman/Lord/city bonuses may change optimal timing and effective value | Broad recurring supply; construction/research/training types differ | Spending before Alliance Help/title/season bonuses; using on the wrong scoring day | D4, D14–D16, Y3/Y5/Y10; high |
| Resource supplies | Fund very large S26–30 buildings/research; protected inventory until opened | Era pushes may create large bursts; level-scaled supplies may grow with Sanctuary | Very repeatable but multi-billion demand; exact chest scaling matters | Opening early, exposing to plunder, or valuing level supplies at the wrong Sanctuary level | D1–D3, D16, D2 level-supply tool; high current |
| Event currencies | Buy shards, Essence, gear, Curios, and speedups in several shops | Era adds Era currency and new reward shops | Usually event-limited; expiry/carryover differs | Spending residual currency without checking rollover and next inventory | D12/D13, D10; medium |
| Awakening Shards/materials | Not a normal S283 use if system absent | Hero-specific Awakening break progression | Era/league/packs; appears highly gated | Splitting across multiple heroes or assuming ordinary shards substitute | D2, D10, Y1; high existence, low acquisition detail |
| Exclusive Weapon Omni/hero shards | No normal use before EW unlock | Star/level hero-specific Exclusive Weapons | Era rewards/shops/packs; exact free income unknown | Building a weapon for a bench hero; spreading flexible Omni shards | D2, D10, Y1; high existence |
| Specialty EXP/books | No verified current use before Lord system | Unlock Lord Specialty nodes and possibly shop access | Era tasks/shop; acquisition curve unknown | Choosing a path without respec/carryover knowledge; missing early compounding income | Y2/Y3, D10; medium |
| Resistance materials | No verified pre-Era use | Raise Era Resistance | Monsters, tasks, packs implied; exact names/sources unknown | Falling behind early if income is snowballing; buying before formula known | Y2, D10; medium |
| Era currency/enhancement materials | None before Era | Era shop, skins/features, later rewards | Seasonal/late sources; rollover unknown | Assuming currency persists or spending on cosmetics before permanent bonuses are compared | D10, Y1; medium-low economics |

## J. Current versus future applicability

| Question type | Applicable now at S26/S283 | Future-facing interpretation | Safe use in the manual today |
| --- | --- | --- | --- |
| Exact building/research cost | Check D1/D2 against current game | Costs may remain while season buffs alter effective time | Store exact versioned facts; calculate only after S283 verification. |
| Development/Alliance Duel priority | Relevant now | Permanent speed and reward multipliers plausibly compound | Present as strategy with modeled break-even, not universal rule. |
| Main-march concentration | Relevant to scarce hero/gear/Raven materials | Awakening/EW/League sources strengthen the same pattern | Treat as a well-corroborated strategy hypothesis pending marginal math. |
| Event timing/hoarding | Immediately relevant | Later KvK/Era layers create more overlapping windows | Build a calendar from current S283 UI; older calendars are templates. |
| Gear breakpoints | Immediately relevant | MR transition may make some UR investments prerequisite rather than obsolete | Do not name a breakpoint until current cap, stats, recipe, and refunds are verified. |
| Raven level/gear | Immediately relevant | Evolution, Epigraph plans, and more gear slots extend the horizon | Separate current level table from later evolution table; preserve update context. |
| Curio investment | Immediately relevant | New Era Curios may change relative priority | Record permanent effects and costs; avoid tier claims without opportunity-cost analysis. |
| T10/Elite Troop | S26–30 relevant | Soldiers Rest and Era PvP can alter fatality economics | Model unlock and training value separately from event scoring. |
| Awakening/EW/Lord/Resistance | Likely absent or partial on S283 | Core future horizon | Explain the existence and questions only; do not prescribe stockpiling without conversion evidence. |

### Sanctuary 1–25: the 20% brief

Harvest only claims with compounding consequences:

- permanent build/research queues and continuous queue utilization;
- Development/research-speed and active-alliance multipliers;
- choosing and concentrating a main faction/march;
- learning event timing before large consumable use;
- not leveling every building merely to match Sanctuary;
- not dismantling gear before recovery rules are understood;
- keeping prerequisite buildings visible two or three Sanctuary levels ahead.

Do not expand this into an exhaustive beginner encyclopedia.

### Sanctuary 26–30: the 80% brief

Prioritize exact prerequisite graphs, cumulative resources/times, research opportunity costs, T10 path, hero/gear/Raven/Curio marginal returns, and the bridge from fully developed current systems to Era resources. At this stage, small percentage errors become very expensive because base costs, timers, and scarce-material requirements are large.

## K. Known version-drift examples

| Conflict/version signal | Observations | Treatment |
| --- | --- | --- |
| Research-tree count | D11 discusses nine broad categories; D8 lists six priorities; the project's current structured source has 18 trees/348 nodes | Keep older strategic logic, never use it as a complete current taxonomy. |
| Raven gear slots | D1 currently presents six named gear slots; D9 reports eight pieces including Mask and Cloak | Verify S283 UI and identify unlock/update condition; preserve both snapshots. |
| Raven horizons | D5 centers breakpoints through level 100; D1 lists Raven max 250 plus 900 evolution rows; D9 describes evolution stages to 900 | Model Raven level, skill-star milestones, and evolution as separate axes. |
| UR gear level cap | D6 visible cost table ends at 40; Y8 says a rework raised max enhancement to 52; D2 exposes quality-5 rows through 60 | Determine whether these are old cap, account/server cap, gear quality, or post-rework differences. |
| Gear material name | Most sources say Tempered Steel; Y8 description says “Temporal Steel” | Treat as likely wording/transcription error until UI item ID confirms. |
| Awakening roster | D1 marks Annie, Cynthia, and Marlena; D2 exposes Awakening rows for Cynthia and Zoya; commercial Era sources name Marlena/Annie and sometimes expect Arthur | Record per-hero evidence and source date; do not publish a single roster yet. |
| Exclusive Weapon examples | D2 exposes Shadow EW; commercial pages give different first-weapon examples | Establish rollout wave, region, and source build before comparing priority. |
| Alliance Duel rules/matchmaking | Aliyawanders reports Alliance Might stripping became much less useful after league matchmaking; older community guides still repeat pre-league preparation | Add effective date/league state to every matchmaking claim. |
| Point values | Fandom explicitly says some base values are not confirmed; VØID omits values not shown in game | Prefer current screenshots and UI values; never average uncertain tables. |

## L. Sanctuary 26–30 information gaps

### High priority

| Gap | Why it blocks calculation | Required evidence |
| --- | --- | --- |
| Current gear rework truth | Cannot calculate gear level/promotion efficiency or preserve-material value | Per slot/quality current level stats, costs, caps, promotion stages, dismantle refunds, S283 screenshot/build date. |
| Hero skill marginal table | Tier lists cannot quantify badge/shard value | Every skill level's exact effect/cooldown/targeting plus Badge/shard cost and star prerequisites. |
| Raven unified progression | Six/eight slots and level/evolution axes conflict | Exact S283 Raven level stages, critical-upgrade distribution, Essence, gear merge/conversion, Epigraph plans and benefits. |
| S26→30 cumulative prerequisite graph | Building opportunity cost depends on all forced side buildings and available bonuses | Exact current costs, time, prerequisites, title/VIP/alliance/Curio modifiers. D2 can seed it. |
| Study Scroll opportunity cost | Alliance Duel reward multipliers and Elite/T10 compete for the same scarce resource | Exact node costs/effects/prerequisites across every Scroll-using tree and current weekly Scroll income. |
| Era resource conversion | Present hoarding cannot be justified without knowing which current materials feed future systems | Awakening/EW/Lord/Resistance recipes, exchange rules, rollover, and free acquisition from an identified older server. |
| Curio marginal efficiency | Permanent bonuses are important but no cost-normalized table was found | Shards per level/star, exact effect increments, acquisition frequency, duplicate conversion. |
| T10/troop ROI | Training guides optimize time/points, not combat/resource outcome | Tier stats, promotion/direct training costs, capacity/load, casualties, healing, Soldiers Rest interaction. |

### Medium priority

| Gap | Needed for |
| --- | --- |
| Hall of Honor exact mechanics and bonus stacking | Valuing late hero shards and bench heroes. |
| Hero Awakening eligibility/wave chronology | Avoiding roster-specific future claims. |
| Exclusive Weapon star tables and Omni income | Measuring concentration vs spreading. |
| Lord Specialty full tree/respec/carryover | Distinguishing a seasonal tactic from permanent account planning. |
| Resistance formula and catch-up | Quantifying early-Era compounding warning. |
| Event reward tables by Sanctuary/bracket | Comparing hoarding thresholds and opportunity costs. |
| Gear/Raven/Curio shop refresh income | Converting “rare” into weekly acquisition rates. |
| Offensive vs defensive tactic outcomes | PvP research allocation after core trees. |
| Battle-report field semantics | Building an evidence loop from upgrades to actual results. |

### Low priority

| Gap | Reason for lower rank |
| --- | --- |
| Exhaustive buildings below S26 | Outside 20/80 focus except prerequisites/compounding systems. |
| Beginner event encyclopedia | Low value for current S26 player. |
| Cosmetic catalog without permanent stats | Does not yet drive progression math. |
| Quiz/codes content | Useful operationally but not central to S26–30 optimization. |
| Arena of Fate/Treasure Digger/Dwarf Mine narrative guides | First map exact rewards and resource dependencies; prose can follow. |

## M. Recommended data-harvest order

1. **Current gear rework snapshot.** Public exact tables are excellent but mutually inconsistent. Acquire current per-slot stats, level costs, promotion gates, material refunds, and cap rules before any gear recommendation.
2. **Full current Raven snapshot.** Capture level stages, critical results, Fruit/Essence costs, skill milestones, all current gear slots and conversion, evolution, and Epigraph plan rules.
3. **Hero skill + Badge/shard progression.** Combine D1/D2 skill effects with D7 costs to make per-level marginal calculations possible.
4. **Study Scroll allocation graph.** Use the existing 18-tree corpus to enumerate every Scroll cost, unlock dependency, point multiplier, and T10 dependency; add current weekly income.
5. **Curio exact cost/effect table.** D1 already supplies effects; acquire shard costs and duplicate/star conversion next.
6. **S26–30 cumulative building plan.** D2's calculator can seed exact prerequisites; add current account modifiers and event/title timing.
7. **T10 troop economics.** Capture direct training vs promotion costs/times, stats, capacity, event points, healing and fatality behavior.
8. **Era evidence packet from one identified older kingdom.** Capture system screens, resource names, unlock chronology, and shops without relying on commercial summaries.
9. **Awakening and Exclusive Weapon curves.** Harvest complete hero-specific/Omni costs and effect breakpoints after Era context is secured.
10. **Lord/Resistance curves and season carryover.** Only then evaluate present-day future warnings.

Readiness assessment:

| System | Exact costs | Exact benefits | Strategy depth | Calculation readiness |
| --- | --- | --- | --- | --- |
| Buildings S26–30 | Strong | Strong/basic | Moderate | Nearly ready after current verification/modifiers. |
| Research | Strong in project | Strong node effects | Moderate | Ready for graphing; not ready for optimal ordering without income/objective model. |
| Heroes | Strong level costs | Partial skills | Strong opinion | Not ready; skill marginal table required. |
| Gear | Strong but conflicting | Partial/conflicting | Strong | Blocked by rework snapshot. |
| Raven | Strong older costs | Strong milestones but axes conflict | Strong | Blocked by unified current snapshot. |
| Curios | Effects strong | Shard cost weak | Thin | Not ready. |
| Troops | Partial | Partial | Moderate | Not ready. |
| Era systems | Discovery good | Costs poor | Moderate | Reconnaissance only. |

## N. Proposed transcript/claim architecture

Design only; do not implement in this worktree.

### Conceptual pipeline

```text
public video metadata
  -> public caption/transcript availability check
  -> authorized/manual timestamped transcript review
  -> topic segmentation
  -> atomic claim extraction
  -> FACT / STRATEGY / FUTURE_WARNING / VERSION_SIGNAL classification
  -> source-game-context attachment
  -> independent corroboration links
  -> human review
  -> manual-ready paraphrase with timestamp citation
```

### Proposed concepts

`strategy_sources`

- source ID, type, platform, URL, creator/channel;
- title, published/updated/retrieved timestamps;
- language and transcript availability/type;
- content hash or metadata-version fingerprint;
- rights/access note and retention policy;
- qualitative source scores.

`source_game_context`

- source ID;
- server/kingdom, region, account day;
- Sanctuary, hero/Raven/gear level;
- season/era and week/phase;
- visible client/build/update label;
- context provenance: stated, visible, inferred, or unknown.

`strategy_claims`

- atomic paraphrased claim;
- claim type;
- topic/system/resource/action/outcome;
- applicability window and conditions;
- status: lead, corroborated, contradicted, drifted, current-user-verified;
- manual-safe wording and unresolved questions.

`claim_evidence`

- claim ID and source ID;
- timestamp start/end or page anchor;
- very short supporting excerpt only when necessary;
- evidence mode: spoken, on-screen UI, table, description, comment;
- directness and independence lineage;
- observed exact value/unit;
- reviewer notes.

Additional useful concepts:

- `source_relationships` for reposts, derivative articles, creator cross-posts, and common Discord-origin material;
- `mechanic_versions` for first/last observed dates, server/era, and superseding evidence;
- `claim_conflicts` linking incompatible values without overwriting either;
- `research_questions` turning unknowns into an ordered harvest queue.

### Practical and copyright-conscious transcript handling

YouTube's public viewer help states that viewers can open the full transcript for videos with captions and jump by timestamp. Its official Data API caption-download endpoint, however, requires authorization sufficient to edit the video. Therefore a future automated system should **not** assume that the official API grants bulk public-caption download rights.

Recommended operating model:

- use public video metadata and the viewer-visible transcript for targeted human review;
- use creator-provided transcript files, creator permission, or another expressly authorized mechanism for automation;
- review YouTube terms and obtain legal advice before any scaled collection;
- respect rate limits, robots/access controls, removals, and creator opt-outs;
- store metadata, claim paraphrases, timestamp ranges, and minimal supporting excerpts—not full transcript copies;
- keep automated captions labeled as machine-generated and require human checking for item/hero names and numbers;
- delete transient transcript working text after claims are reviewed unless there is a documented lawful need to retain it;
- link back to the original video so users can inspect context.

Relevant official references: [View video transcripts](https://support.google.com/youtube/answer/15930243?hl=en), [automatic caption limitations](https://support.google.com/youtube/answer/6373554?hl=en), and [YouTube Data API caption download authorization](https://developers.google.com/youtube/v3/docs/captions/download?hl=en).

## O. Corroboration strategy

### Evidence ladder

1. **One creator, no screen/context:** interesting strategy lead.
2. **One creator with visible UI/timestamp:** direct observation for that account/build.
3. **Multiple independent creators:** stronger strategy evidence, provided they are not repeating one guide.
4. **Exact structured data + player explanation:** strong mechanic/economic evidence for the shared version.
5. **Multiple advanced-server observations + exact data:** strong future-system evidence, still not a rollout guarantee.
6. **Current Server 283 in-game verification:** strongest evidence for present mechanics.
7. **Current verification repeated after update:** establishes a version interval rather than timeless truth.

### Independence rules

- Pages on the same site are one editorial lineage.
- A Reddit post linking a creator's own video is one source, not two.
- Commercial top-up articles with near-identical structure may be derivative even across domains.
- A guide copying a public spreadsheet does not independently corroborate the sheet.
- Translated/reposted videos remain the same source unless the reposter adds original verified evidence.

### Conflict handling

- Never average conflicting factual values.
- Record both values, their dates, servers/eras, and visible UI context.
- Prefer the newest directly observed value only for the matching context.
- Mark a newer contradiction as possible version drift, server gating, account-level gating, regional rollout, or source error until one is demonstrated.
- Strategy disagreement is not necessarily factual conflict; retain the objective and account assumptions behind each choice.

No numerical strategy-confidence weights should be introduced until evidence-lineage and version-context capture are reliable.

## P. Risks and limitations

- **Sparse server labels:** most otherwise useful sources omit server/kingdom and account age.
- **Fast-moving game:** several explicit reworks occurred within months; currentness can outrank popularity.
- **Commercial content:** top-up sites may publish derivative or AI-assisted copy optimized for sales, not verification.
- **Creator bias:** spend level, alliance strength, faction, and PvP goals materially change advice.
- **Auto-caption errors:** hero and material names, percentages, and negatives can be mistranscribed.
- **Search indexing bias:** English pages and optimized sites dominate results; high-quality private alliance knowledge remains invisible by design.
- **Image-led guides:** useful information may be public but not text-indexed, requiring manual visual extraction with provenance.
- **Regional/server cadence:** lower server number does not guarantee the same feature timeline or balance.
- **Data-site provenance:** “game data” claims are strong leads, not self-authenticating proof; build/version tags are needed.
- **Point/reward brackets:** values can vary by league, Sanctuary, event generation, or update.
- **Survivorship bias:** advanced players explain what worked for their retained account, not all failed alternatives.
- **Missing official mechanics:** troop Morale and several future resource formulas remain player theory.

## Q. Recommended immediate next five research tasks

1. **Current gear rework evidence pack:** capture Server 283 screens for all gear slots, enhancement cap, promotion steps, Gearstone/Blueprint/Steel costs, and dismantle preview; reconcile D2, D6, Y4, Y8, and Y9.
2. **Current Raven evidence pack:** capture Raven level/skill/evolution tabs, all visible gear slots, chest merge rules, Fruit/Essence costs, critical-upgrade behavior, and Epigraph unlocks; reconcile D1, D5, D9, Y6, and Y7.
3. **Study Scroll decision dataset:** export every Scroll-using node from the existing 18-tree corpus, add exact effects/prerequisites, then record Server 283 weekly Scroll inflow from Alliance Duel and other repeatable sources.
4. **Timestamped Era review:** manually review Y1–Y3 and Y2's post-season warnings; record visible server/season context, resource names, Lord/Resistance screens, and only short timestamped claim paraphrases.
5. **Hero/Curio marginal-data capture:** complete per-skill Badge/shard effects for the main squad and shard-per-level/star Curio tables, because these are the two largest blockers to comparing current investments.

These tasks follow the gaps with the highest decision impact; they are not a curiosity queue.

## R. Exact files changed

- `docs/advanced_server_source_reconnaissance.md` — created; this reconnaissance report only.

No application code, database/schema, existing manual/progression document, Shop Doctor material, or other worktree was modified. No commit was created.

## S. Exact `git status --short`

```text
?? docs/advanced_server_source_reconnaissance.md
```
