# Chapter 8.3 — Bot Squads and Combat Heuristics

## Purpose

Once a [bot](../appendices/Appendix_A_Glossary.md) has produced units, it needs to turn them into effective combat forces. OpenRA's `SquadManagerBotModule` groups idle units into [squads](../appendices/Appendix_A_Glossary.md), assigns each squad a [target](../appendices/Appendix_A_Glossary.md), and drives the squad through a small state machine. The most important combat decision—whether to attack or flee—is made by a [fuzzy-logic](../appendices/Appendix_A_Glossary.md) heuristic. This chapter explains squad lifecycle, squad states, and the `AttackOrFleeFuzzy` rules.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how SquadManagerBotModule groups idle units into squads.
- Describe the squad lifecycle from unit discovery to attack force creation.
- Trace the ground squad state machine (Idle, AttackMove, Attack, Flee).
- Understand the fuzzy logic behind AttackOrFleeFuzzy decisions.
- Configure squad sizes, intervals, and unit type filters in YAML.
- Implement custom squad states or behaviors.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` | Creates squads, assigns units, and ticks them. |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/Squad.cs` | Squad data container, serialization, target tracking. |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/AttackOrFleeFuzzy.cs` | Fuzzy logic engine for attack/flee decisions. |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/StateMachine.cs` | Tiny state machine wrapper. |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/States/StateBase.cs` | Shared state helpers. |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/States/GroundStates.cs` | Ground/naval squad states (Idle, AttackMove, Attack, Flee). |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/States/AirStates.cs` | Air squad states. |
| `OpenRA.Mods.Common/Traits/BotModules/Squads/States/ProtectionStates.cs` | Protection squad states. |

![Architecture diagram](images/Part_08_Chapter_03_Squads-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Squad as a unit group

A `Squad` is a lightweight object owned by `SquadManagerBotModule`:

```csharp
public class Squad
{
    public HashSet<Actor> Units = [];
    public SquadType Type;
    internal Target Target;
    internal Actor TargetActor;
    internal StateMachine FuzzyStateMachine;
}
```

The `SquadType` enum has five values:

- `Assault` — main ground attack force.
- `Rush` — early aggressive force.
- `Air` — aircraft squad.
- `Naval` — ship squad.
- `Protection` — defensive squad that responds to base attacks.

Each squad type has its own state machine states (e.g., `GroundUnitsIdleState`, `AirIdleState`, `UnitsForProtectionIdleState`).

### Squad lifecycle

1. `SquadManagerBotModule.FindNewUnits()` scans the world for newly produced units that are not yet in `activeUnits`.
2. Air and naval units are immediately added to their type-specific squads.
3. Ground units are added to `unitsHangingAroundTheBase`.
4. Every `AssignRolesInterval` ticks, `CreateAttackForce()` converts the idle pile into an `Assault` squad when it reaches `SquadSize`.
5. Every `AttackForceInterval` ticks, squads are pushed onto `squadsPendingUpdate` and processed a few per tick.
6. Each squad's `Update()` calls `FuzzyStateMachine.Update(this)`, which transitions states and issues orders.
7. `CleanSquads()` removes dead units and empty squads.

### SquadManagerBotModule tick structure

```csharp
void AssignRolesToIdleUnits(IBot bot)
{
    CleanSquads();
    activeUnits.RemoveWhere(unitCannotBeOrdered);
    unitsHangingAroundTheBase.RemoveAll(unitCannotBeOrdered);

    if (--rushTicks <= 0)
    {
        rushTicks = Info.RushInterval;
        TryToRushAttack(bot);
    }

    if (--attackForceTicks <= 0)
    {
        attackForceTicks = Info.AttackForceInterval;
        foreach (var s in Squads)
            squadsPendingUpdate.Push(s);
    }

    var updateCount = Exts.IntegerDivisionRoundingAwayFromZero(squadsPendingUpdate.Count, attackForceTicks);
    for (var i = 0; i < updateCount; i++)
    {
        var squadPendingUpdate = squadsPendingUpdate.Pop();
        if (squadPendingUpdate.IsValid)
            squadPendingUpdate.Update();
    }

    if (--assignRolesTicks <= 0)
    {
        assignRolesTicks = Info.AssignRolesInterval;
        FindNewUnits(bot);
    }

    if (--minAttackForceDelayTicks <= 0)
    {
        minAttackForceDelayTicks = Info.MinimumAttackForceDelay;
        CreateAttackForce(bot);
    }

    if (respondToAttackCooldown-- == MaxRespondToAttackCooldown)
        ProtectOwn(bot, protectFrom);
}
```

![Data flow  code path diagram](images/Part_08_Chapter_03_Squads-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Finding new units

```csharp
void FindNewUnits(IBot bot)
{
    var newUnits = World.ActorsHavingTrait<IPositionable>()
        .Where(a => a.Owner == Player &&
            !Info.ExcludeFromSquadsTypes.Contains(a.Info.Name) &&
            !activeUnits.Contains(a));

    foreach (var a in newUnits)
    {
        if (Info.AirUnitsTypes.Contains(a.Info.Name))
        {
            var air = GetSquadOfType(SquadType.Air);
            air ??= RegisterNewSquad(bot, SquadType.Air);
            air.Units.Add(a);
        }
        else if (Info.NavalUnitsTypes.Contains(a.Info.Name))
        {
            ...
        }
        else
            unitsHangingAroundTheBase.Add(a);

        activeUnits.Add(a);
    }
}
```

`activeUnits` is the global set of all units already assigned to the squad manager. New units are categorized by their YAML type lists.

### Creating an attack force

```csharp
void CreateAttackForce(IBot bot)
{
    var randomizedSquadSize = Info.SquadSize + World.LocalRandom.Next(Info.SquadSizeRandomBonus);

    if (unitsHangingAroundTheBase.Count >= randomizedSquadSize)
    {
        var attackForce = RegisterNewSquad(bot, SquadType.Assault);
        attackForce.Units.UnionWith(unitsHangingAroundTheBase);
        unitsHangingAroundTheBase.Clear();
    }
}
```

When enough idle ground units accumulate, they become a single assault squad.

### Ground squad state machine

The ground state machine has four states:

1. **Idle** — the squad has no valid target. It picks the closest enemy and decides whether to attack or flee.
2. **AttackMove** — the squad moves toward the target while trying to stay grouped.
3. **Attack** — the squad actively engages a visible enemy.
4. **Flee** — the squad retreats toward the base.

State transitions are driven by the fuzzy `CanAttack` result, target validity, and a 2.5-second movement timeout.

### Leader election

`GroundStateBase.Leader()` picks a squad leader:

```csharp
var leastCommonDenominator = units
    .Select(a => a.TraitOrDefault<Mobile>()?.Locomotor)
    .Where(l => l != null)
    .MinByOrDefault(l => l.Info.TerrainSpeeds.Count)
    ?.Info.TerrainSpeeds.Count;

if (leastCommonDenominator != null)
    units = units.Where(a => a.TraitOrDefault<Mobile>()?.Locomotor.Info.TerrainSpeeds.Count == leastCommonDenominator).ToList();

var centerPosition = units.Select(a => a.CenterPosition).Average();
return units.MinBy(a => (a.CenterPosition - centerPosition).LengthSquared);
```

The leader is the unit with the most restrictive locomotor (fewest terrain speeds) that is closest to the center. This reduces the chance that the squad will follow a unit that other members cannot path to.

### Target acquisition

```csharp
var closestEnemy = NewLeaderAndFindClosestEnemy(owner);
owner.SetActorToTarget(closestEnemy);
```

The squad manager finds the closest enemy actor that is visible, not a husk, and not in the ignored target type set. It returns both the actor and a small offset so that naval units can target a reachable cell near a land unit.

![Configuration (yaml) diagram](images/Part_08_Chapter_03_Squads-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Squad configuration

```yaml
SquadManagerBotModule:
    ConstructionYardTypes: fact
    AirUnitsTypes: yak, mig, heli, orca, hind
    NavalUnitsTypes: ss, ca, dd, pt
    ExcludeFromSquadsTypes: mcv, harv
    SquadSize: 10
    SquadSizeRandomBonus: 5
    RushInterval: 2500
    AssignRolesInterval: 150
    AttackForceInterval: 250
    MinimumAttackForceDelay: 1000
    IdleScanRadius: 10
    AttackScanRadius: 12
    DangerScanRadius: 10
    IgnoredEnemyTargetTypes: Husk
```

### Targeting filters

- `IgnoredEnemyTargetTypes` — target types that the squad should ignore (e.g., husks).
- `DangerScanRadius` — range used when responding to attacks on the base.
- `IdleScanRadius` — range used when looking for enemies while idle.
- `AttackScanRadius` — range used when looking for enemies while attacking.

## Interconnectivity

- **Depends on:** [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) (IBot/ModularBot), [Part 8.2 — Bot Modules](Part_08_Chapter_02_Bot_Modules.md) (Bot Modules), [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) (Actor traits), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (Orders), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) (rulesets and target types).
- **Used by:** [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) (orders flow out of squad states), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (orders are queued for lockstep execution).

![Algorithms diagram](images/Part_08_Chapter_03_Squads-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Fuzzy attack/flee logic

`AttackOrFleeFuzzy` is a Mamdani fuzzy system with four inputs:

- `OwnHealth` — normalized health of the squad (0–100).
- `EnemyHealth` — normalized health of nearby enemies (0–100).
- `RelativeAttackPower` — own attack power divided by enemy attack power, scaled to 0–1000.
- `RelativeSpeed` — own speed divided by enemy speed, scaled to 0–1000.

And one output:

- `AttackOrFlee` — 0–50, where values below 30 mean attack and above 30 mean flee.

```csharp
public bool CanAttack(IReadOnlyCollection<Actor> ownUnits, IReadOnlyCollection<Actor> enemyUnits)
{
    ...
    var result = fuzzyEngine.Calculate(inputValues);
    attackChance = result[fuzzyEngine.OutputByName("AttackOrFlee")];
    return !double.IsNaN(attackChance) && attackChance < 30.0;
}
```

If `CanAttack` returns true, the squad transitions to attack/attack-move; otherwise it flees.

### Normalized health

```csharp
static float NormalizedHealth(IEnumerable<Actor> actors, int normalizeByValue)
{
    var sumOfMaxHp = 0;
    var sumOfHp = 0;
    foreach (var a in actors)
    {
        if (a.Info.HasTraitInfo<IHealthInfo>())
        {
            sumOfMaxHp += a.Trait<IHealth>().MaxHP;
            sumOfHp += a.Trait<IHealth>().HP;
        }
    }

    if (sumOfMaxHp == 0)
        return 0;

    return sumOfHp * 100 / sumOfMaxHp;
}
```

The fuzzy engine receives the average health of the group as a percentage.

### Relative power and speed

`RelativeAttackPower` and `RelativeSpeed` are computed from the aggregated firepower and movement speed of the squad versus the enemy. The exact formulas combine weapon DPS, range, and locomotor speed.

### Stuck-squad timeout

Both `GroundUnitsAttackMoveState` and `GroundUnitsAttackState` track the leader's last known location and the last target change. If neither changes for 63 ticks (~2.5 seconds), the squad drops back to `Idle` to find a new path or target:

```csharp
if (owner.World.WorldTick > lastUpdatedTick + 63)
{
    owner.FuzzyStateMachine.ChangeState(owner, new GroundUnitsIdleState());
    return;
}
```

This prevents expensive pathfinding loops when a squad is blocked.

### Regrouping

During `AttackMove`, if the squad is spread out, the leader stops and the stragglers are ordered to attack-move to the leader's cell:

```csharp
var ownUnits = owner.World.FindActorsInCircle(leader.CenterPosition, WDist.FromCells(owner.Units.Count) / 3)
    .Where(owner.Units.Contains).ToHashSet();

if (ownUnits.Count < owner.Units.Count)
{
    owner.Bot.QueueOrder(new Order("Stop", leader, false));
    var units = owner.Units.Where(a => !ownUnits.Contains(a)).ToArray();
    owner.Bot.QueueOrder(new Order("AttackMove", null, Target.FromCell(owner.World, leader.Location), false, groupedActors: units));
}
```

This keeps the squad cohesive before engaging.

![Extension points diagram](images/Part_08_Chapter_03_Squads-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new squad type

Add a new value to `SquadType`, create states in `OpenRA.Mods.Common/Traits/BotModules/Squads/States/`, and add assignment logic in `FindNewUnits` and `CreateAttackForce`. For example, a "Stealth" squad type could be created for invisible hit-and-run units.

### Customize the fuzzy rules

`AttackOrFleeFuzzy` has a `Default` rule set and a more aggressive `Rush` rule set. Mods can create custom rule sets by constructing a new `AttackOrFleeFuzzy` with their own rule strings. However, the rule engine is currently hardcoded in C#, so a new bot personality cannot change rules purely through YAML.

### Add a new ground state

Subclasses of `GroundStateBase` implement `IState` and can be inserted into the state machine. For example, a "Harass" state could send small groups to attack resource harvesters and retreat.

### Adjust squad sizes and timing

All timing and sizing parameters are in YAML. A defensive AI could use smaller squads and a shorter `DangerScanRadius`, while an aggressive AI could use larger squads and a shorter `RushInterval`.

### Custom target selection

Override `SquadManagerBotModule.FindClosestEnemy` or add a new `FindEnemies` filter to change what the bot considers a valid target. The default filter ignores husks and invisible units.

![Common pitfalls  guardrails diagram](images/Part_08_Chapter_03_Squads-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **No simulation state:** squad logic runs unsynced. It must issue orders to change state; it cannot modify actors directly.
- **Mixed locomotors:** the leader election heuristic helps, but a squad with wildly incompatible units (e.g., land and naval) can still fail to path together.
- **Fuzzy rule tuning:** changing the fuzzy rule strings can produce unexpected behaviors. Test carefully on a variety of unit matchups.
- **Squad size inflation:** a very large `SquadSize` can cause all units to sit at the base for a long time before attacking. A very small value can cause the AI to send units piecemeal.
- **Stuck squads:** the 2.5-second timeout is a safety net, not a pathfinding fix. If many squads get stuck, the pathfinding or map layout may need review.
- **Save/load:** squads are serialized via `IGameSaveTraitData`. Custom squad types must implement `Serialize`/`Deserialize` to survive savegames.

## What to read next

- [Part 8.2 — Bot Modules](Part_08_Chapter_02_Bot_Modules.md) for how `SquadManagerBotModule` fits into the broader bot module architecture.
- [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) for how squad states translate into `Order` objects.
- [Part 1.5 — Pathfinding and Movement](Part_01_Chapter_05_Pathfinding_Movement.md) for the pathfinding and locomotor rules that affect squad movement.

## Summary

This chapter explains how a [bot](../appendices/Appendix_A_Glossary.md) turns produced units into effective combat forces through squads and fuzzy heuristics.

After reading this chapter, you should be able to:

- `SquadManagerBotModule.FindNewUnits()` scans the world for newly produced units that are not yet in `activeUnits`.
- Air and naval units are immediately added to their type-specific squads.
- Ground units are added to `unitsHangingAroundTheBase`.
- Every `AssignRolesInterval` ticks, `CreateAttackForce()` converts the idle pile into an `Assault` squad when it reaches `SquadSize`.
- Every `AttackForceInterval` ticks, squads are pushed onto `squadsPendingUpdate` and processed a few per tick.
- Each squad's `Update()` calls `FuzzyStateMachine.Update(this)`, which transitions states and issues orders.
- `CleanSquads()` removes dead units and empty squads.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` — squad coordinator.
- `OpenRA.Mods.Common/Traits/BotModules/Squads/Squad.cs` — squad container.
- `OpenRA.Mods.Common/Traits/BotModules/Squads/AttackOrFleeFuzzy.cs` — fuzzy decision engine.
- `OpenRA.Mods.Common/Traits/BotModules/Squads/StateMachine.cs` — state machine.
- `OpenRA.Mods.Common/Traits/BotModules/Squads/States/GroundStates.cs` — ground/naval states.
- `OpenRA.Mods.Common/Traits/BotModules/Squads/States/AirStates.cs` — air states.
- `OpenRA.Mods.Common/Traits/BotModules/Squads/States/ProtectionStates.cs` — protection states.
- `mods/ra/rules/ai.yaml` — example squad configurations.