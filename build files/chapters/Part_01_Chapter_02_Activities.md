# Chapter 1.2 — Activities and the Game Loop

## Purpose

This chapter explains how OpenRA turns player orders into multi-tick, interruptible [actor](../appendices/Appendix_A_Glossary.md) behavior. The engine separates **persistent state** ([Traits](../appendices/Appendix_A_Glossary.md)) from **transient, multi-frame plans** ([Activities](../appendices/Appendix_A_Glossary.md)). The Activity system is the backbone of every unit action — move, attack, harvest, dock, build, transform, and so on — and it runs inside the deterministic 25 Hz simulation tick. The goal is to understand:

- How traits and activities differ.
- The lifecycle of an activity from queueing to completion.
- How `TickOuter`, `TickChild`, and `ChildHasPriority` drive the tick loop.
- How activity chains are built with `NextActivity` and `ChildActivity`.
- Why `ActivityUtils.RunActivity` is the hot path and how it relates to [`World.Tick`](../appendices/Appendix_A_Glossary.md).
- How concrete activities such as `Move`, `Attack`, and `HarvestResource` use the system.

## Learning Objectives


After studying this chapter, you should be able to:

1. Distinguish traits (persistent state) from activities (transient plans).
2. Explain how activities are queued, chained, and interrupted.
3. Trace the `TickOuter` / `TickChild` loop and understand `ChildHasPriority`.
4. Implement a simple custom activity that moves or waits.
5. Diagnose activity-related bugs such as stuck units or infinite loops.

![Practical example: a move order diagram](images/Part_01_Chapter_02_Activities-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: A Move Order


When a player orders a tank to move:

1. The order generator creates an [`Order`](../appendices/Appendix_A_Glossary.md) with `OrderString = "Move"` and [`Target`](../appendices/Appendix_A_Glossary.md) set to the destination cell.
2. The order is processed by `ResolveOrder` in the unit's `Mobile` trait.
3. `Mobile` creates a `Move` activity and queues it on the actor's activity stack.
4. Each tick, `ActivityUtils.RunActivity` calls `TickOuter` on the `Move` activity.
5. `Move` computes the path, calls child activities like `MovePart`, and completes when the destination is reached.
6. If the player issues a new order, the current `Move` is cancelled and a new activity is queued.

This example shows how orders become multi-frame behavior through the activity system.

## Files

| Source File | Path in the OpenRA Repository | Role |
|-------------|------------------------------|------|
| `Activity.cs` | `OpenRA.Game\Activities\Activity.cs` | Core activity state machine, states, chaining, and `TickOuter` |
| `ActivityUtils.cs` | `OpenRA.Game\Traits\ActivityUtils.cs` | `RunActivity` hot-path runner |
| `ActionQueue.cs` | `OpenRA.Game\Primitives\ActionQueue.cs` | Global thread-safe delayed action queue (not the actor activity queue) |
| `Actor.cs` | `OpenRA.Game\Actor.cs` | `CurrentActivity`, `QueueActivity`, `CancelActivity`, and `Tick` |
| `World.cs` | `OpenRA.Game\World.cs` | `WorldTick`, `Tick`, and trait ticking orchestration |
| `Move.cs` | `OpenRA.Mods.Common\Activities\Move\Move.cs` | Concrete movement activity that chains `MoveFirstHalf` / `MoveSecondHalf` |
| `Attack.cs` | `OpenRA.Mods.Common\Activities\Attack.cs` | Concrete attack activity that runs in parallel with movement children |
| `HarvestResource.cs` | `OpenRA.Mods.Common\Activities\HarvestResource.cs` | Concrete harvest activity that chains move/turn/wait children |

![Architecture diagram](images/Part_01_Chapter_02_Activities-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Traits are passive, persistent state

An `Actor` is a container of **Traits**. Traits are created once in `Actor.ctor` (`OpenRA.Game\Actor.cs`), live as long as the actor, and are queried by their interfaces. They typically do not remember a multi-frame plan.

Traits that want per-tick logic implement one of:

- `ITick` — `void Tick(Actor self)` — called every simulation tick by the world after activities run (`OpenRA.Game\Traits\TraitsInterfaces.cs`).
- `ITickRender` — `void TickRender(WorldRenderer wr, Actor self)` — called once per render frame.
- `IResolveOrder` — `void ResolveOrder(Actor self, Order order)` — converts a player order into an activity (`TraitsInterfaces.cs`).
- `ICreationActivity` — `Activity GetCreationActivity()` — supplies an initial activity when the actor is created (`TraitsInterfaces.cs`).
- `INotifyBecomingIdle` / `INotifyIdle` — react when the actor has no activity left (`TraitsInterfaces.cs`).

Traits are **passive** in the sense that they do not own the actor's "current action"; they are queried each tick or when an order is issued. They can be disabled, paused, or conditionally enabled via `ConditionalTrait` without affecting the activity queue.

### Activities are multi-tick, interruptible state machines

An **Activity** is an object derived from `Activity` that exists only for the duration of a plan. It is stored in the actor's `currentActivity` field and is replaced when it completes. The base class in `OpenRA.Game\Activities\Activity.cs` defines:

- `ActivityState State { get; private set; }` — one of `Queued`, `Active`, `Canceling`, or `Done` (`Activity.cs`).
- `Activity NextActivity` — the next activity in the actor's queue (`Activity.cs`).
- `Activity ChildActivity` — a sub-activity that the parent may run before it can continue (`Activity.cs`).
- `bool IsInterruptible` — whether the activity can be cancelled (default `true`) (`Activity.cs`).
- `bool ChildHasPriority` — whether the child should run first (default `true`) (`Activity.cs`).
- `virtual bool Tick(Actor self)` — the per-tick logic; returns `true` when the activity is done.
- `virtual void OnFirstRun(Actor self)` — one-shot initialization immediately before the first tick.
- `virtual void OnLastRun(Actor self)` — one-shot cleanup immediately after the final tick.

`Actor.IsIdle` is defined as `CurrentActivity == null` (`Actor.cs`). When the actor has no activity, it is idle.

### The four activity states

The `ActivityState` enum has exactly four values (`Activity.cs`):

1. **Queued** — the activity has been created and linked but has not been started yet.
2. **Active** — the activity has run its `OnFirstRun` and is being ticked.
3. **Canceling** — `Cancel()` was called while the activity was active; it should return the actor to a consistent state and then finish.
4. **Done** — the activity has completed, or it was cancelled while still queued.

The state transition is central:

- `TickOuter` starts `Queued` activities, calling `OnFirstRun` and moving to `Active` (`Activity.cs`).
- `Cancel()` turns `Queued` directly into `Done` (so skipped) or `Active` into `Canceling` (`Activity.cs`).
- A tick that returns `true` sets `Done` and calls `OnLastRun` (`Activity.cs`).

![Data flow  code path diagram](images/Part_01_Chapter_02_Activities-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### The 25 Hz deterministic simulation tick

The game loop runs at a fixed rate. The default game speed in all shipped mods is:

```yaml
GameSpeeds:
    DefaultSpeed: default
    Speeds:
        default:
            Name: options-game-speed.normal
            Timestep: 40
            OrderLatency: 3
```

`40` milliseconds per tick = **25 Hz** (`mods\ra\mod.yaml`, `mods\ts\mod.yaml`, etc.). The world loads this value as `GameSpeed.Timestep`, stored in `World.Timestep` (`World.cs`), and `OrderManager.SuggestedTimestep` returns it when the game is running (`OrderManager.cs`).

`Game.LogicTick` checks `OrderManager.LastTickTime.ShouldAdvance()` and then calls the world tick (`Game.cs`). Each world tick is deterministic and must be reproducible across all clients and replays.

### World.Tick: the top of the simulation

`World.Tick` in `OpenRA.Game\World.cs` does the following:

1. Resumes any game-save data if needed.
2. If the game is not paused:
   - Increments `WorldTick` (`World.cs`).
   - Ticks every actor via `foreach (var a in actors.Values) a.Tick()` (`World.cs`).
   - Ticks every trait that implements `ITick` (`World.cs`).
   - Ticks effects (`World.cs`).
3. Drains `frameEndActions` (queued world-level actions) (`World.cs`).

The actor tick is the bridge between the world tick and the activity system.

### Actor.Tick: where the current activity runs

```csharp
public void Tick()
{
    var wasIdle = IsIdle;
    CurrentActivity = ActivityUtils.RunActivity(this, CurrentActivity);

    if (!wasIdle && IsIdle)
    {
        foreach (var n in becomingIdles)
            n.OnBecomingIdle(this);

        // If IsIdle is true, it means the last CurrentActivity.Tick returned null.
        // If a next activity has been queued via OnBecomingIdle, we need to start running it now,
        // to avoid an 'empty' null tick where the actor will (visibly, if moving) do nothing.
        CurrentActivity = ActivityUtils.RunActivity(this, CurrentActivity);
    }
    else if (wasIdle)
        foreach (var tickIdle in tickIdles)
            tickIdle.TickIdle(this);
}
```

(`Actor.cs`)

Key observations:

- `CurrentActivity` is a property that automatically skips `Done` activities via `Activity.SkipDoneActivities` (`Actor.cs`).
- `ActivityUtils.RunActivity` is called once per actor tick. If `OnBecomingIdle` queued a new activity, it is called a second time to avoid a one-tick idle gap.

### ActivityUtils.RunActivity: the hot path

```csharp
public static class ActivityUtils
{
    public static Activity RunActivity(Actor self, Activity act)
    {
        // PERF: This is a hot path and must run with minimal added overhead.
        if (act == null)
            return act;

        var start = PerfTickLogger.GetTimestamp();
        do
        {
            var prev = act;
            act = act.TickOuter(self);
            start = PerfTickLogger.LogLongTick(start, "Activity", prev);
            if (act == prev)
                break;
        }
        while (act != null);

        return act;
    }
}
```

(`OpenRA.Game\Traits\ActivityUtils.cs`)

This is the **hot path**. `RunActivity` repeatedly calls `TickOuter` until the current activity either returns itself (meaning "not done yet") or returns `null` / a next activity that finishes immediately. The loop is important because one `World.Tick` can drain a chain of zero-duration activities (e.g., `Wait` with no delay, or a turn that completes instantly) without leaving the actor idle for a frame.

Perf timing is wrapped around every call: if a single activity takes too long, it is logged under the "Activity" perf category.

<!-- DEV-NOTE [visual-aid]: Activity TickOuter state machine diagram showing the transitions between Queued, Active, Canceling, and Done; the child-priority path (ChildHasPriority) where the child runs before the parent; and the NextActivity chaining that links completed activities to the next queued task. This should map directly to the code walkthrough below. -->

### Activity.TickOuter: the heart of the state machine

```csharp
public Activity TickOuter(Actor self)
{
    if (State == ActivityState.Done)
        throw new InvalidOperationException($"Actor {self} attempted to tick activity {GetType()} after it had already completed.");

    if (State == ActivityState.Queued)
    {
        OnFirstRun(self);
        firstRunCompleted = true;
        State = ActivityState.Active;
    }

    if (!firstRunCompleted)
        throw new InvalidOperationException($"Actor {self} attempted to tick activity {GetType()} before running its OnFirstRun method.");

    // Only run the parent tick when the child is done.
    // We must always let the child finish on its own before continuing.
    if (ChildHasPriority)
    {
        lastRun = TickChild(self) && (finishing || Tick(self));
        finishing |= lastRun;
    }

    // The parent determines whether the child gets a chance at ticking.
    else
        lastRun = Tick(self);

    // Avoid a single tick delay if the childactivity was just queued.
    var ca = ChildActivity;
    if (ca != null && ca.State == ActivityState.Queued)
    {
        if (ChildHasPriority)
            lastRun = TickChild(self) && finishing;
        else
            TickChild(self);
    }

    if (lastRun)
    {
        State = ActivityState.Done;
        OnLastRun(self);
        return NextActivity;
    }

    return this;
}
```

(`Activity.cs`)

Walkthrough:

1. **Validate state.** If `Done`, it is an error; `TickOuter` should not be called on completed activities.
2. **Start the activity.** If `Queued`, call `OnFirstRun`, set `firstRunCompleted`, and move to `Active`.
3. **Tick child and parent.**
   - If `ChildHasPriority` (default):
     - `TickChild(self)` runs the child. It returns `true` only when the child is gone.
     - The parent `Tick(self)` is only called if the child is done or if the parent already signaled `finishing`.
     - `finishing` is sticky once the parent `Tick` has returned `true`.
   - If `ChildHasPriority == false`:
     - The parent `Tick` runs every frame.
     - The parent is responsible for calling `TickChild` manually.
4. **Avoid a one-tick delay for newly queued children.** If a child was just queued in this tick, run it immediately.
5. **Complete.** If `lastRun` is true, set `Done`, call `OnLastRun`, and return `NextActivity` (or `null` if the queue is empty). Otherwise, return `this`.

### TickChild and ChildHasPriority semantics

```csharp
protected bool TickChild(Actor self)
{
    ChildActivity = ActivityUtils.RunActivity(self, ChildActivity);
    return ChildActivity == null;
}
```

(`Activity.cs`)

- `TickChild` returns `true` when the child activity is done (or was null).
- When `ChildHasPriority` is `true` (the default for most activities), the parent tick is suppressed until the child finishes.
- When `ChildHasPriority` is `false`, the parent tick runs every tick and may call `TickChild` itself to advance the child. This is used by `Attack` so that the activity can keep attacking while a child `Move` is chasing the target.

### Building chains: NextActivity vs ChildActivity

Two independent pointers exist:

```csharp
Activity nextActivity;   // sibling queue
Activity childActivity;  // nested sub-task
```

- `Queue(Activity activity)` appends to the sibling chain of `nextActivity` (`Activity.cs`).
- `QueueChild(Activity activity)` appends to the child chain. If no child exists, it becomes the child directly (`Activity.cs`).
- `Actor.QueueActivity(Activity)` hooks into the sibling chain via `CurrentActivity.Queue` or sets `CurrentActivity` directly if the actor is idle (`Actor.cs`).
- `Actor.QueueActivity(bool queued, Activity nextActivity)` optionally cancels the current activity first (`Actor.cs`).

Siblings (`NextActivity`) are sequential: when the current activity finishes, the runner starts the next one. Children (`ChildActivity`) are hierarchical: the parent normally waits for the child before continuing. Both are skipped automatically if they are `Done` via `SkipDoneActivities` (`Activity.cs`).

### Cancellation and `IsCanceling`

```csharp
public virtual void Cancel(Actor self, bool keepQueue = false)
{
    if (!keepQueue)
        NextActivity = null;

    if (!IsInterruptible)
        return;

    ChildActivity?.Cancel(self);

    // Directly mark activities that are queued and therefore didn't run yet as done
    State = State == ActivityState.Queued ? ActivityState.Done : ActivityState.Canceling;
}
```

(`Activity.cs`)

- `keepQueue = true` preserves the sibling queue. This is used when a parent wants to cancel its current sub-task but keep the rest of the actor's order queue.
- If `IsInterruptible == false`, `Cancel` is ignored.
- `Cancel` propagates to the child recursively.
- A queued activity is marked `Done` immediately; `SkipDoneActivities` will bypass it.
- An active activity is marked `Canceling`. It is the responsibility of the activity's `Tick` method to detect `IsCanceling` and return `true` once cleanup is finished.

`Actor.CancelActivity()` simply calls `CurrentActivity?.Cancel(this)` (`Actor.cs`). The OpenRA source comment explicitly warns against calling it from activity code: prefer calling `Cancel()` on the specific activity you want to cancel.

### OnFirstRun and OnLastRun

- `OnFirstRun` is the correct place to evaluate dynamic world state (actor position, conditions, target validity) because the constructor may run many ticks before the activity becomes active. The class header comments say: "Do not evaluate dynamic state in the activity's constructor; use the OnFirstRun method instead" (`Activity.cs`).
- `OnLastRun` is the correct place for cleanup. `Move.OnLastRun` clears the path (`Move.cs`), and `HarvestResource.OnLastRun` removes the resource claim (`HarvestResource.cs`).
- `OnActorDispose` is called on actor disposal and can be used to force cleanup that would otherwise be skipped (`Activity.cs`).

### ActionQueue (global delayed actions, not the actor queue)

`OpenRA.Game\Primitives\ActionQueue.cs` is a thread-safe, time-sorted queue of `DelayedAction` objects. It is used by the game-level `Game.delayedActions` queue and `Game.RunAfterTick` / `Game.PerformDelayedActions` (`Game.cs`). It is **not** the actor activity queue; it is used for deferred widget cleanup, disposal tasks, and cross-thread work. The `ActionQueue` performs all actions whose `desiredTime` is <= the current runtime.

![Configuration (yaml) diagram](images/Part_01_Chapter_02_Activities-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


The activity system is largely code-driven, but its timing and behavior are controlled by YAML-defined traits:

- **GameSpeeds** (`mods\ra\mod.yaml`, `mods\ts\mod.yaml`, etc.) define the simulation tick rate. The default `Timestep: 40` gives 25 Hz.
- **Locomotor** and **Mobile** (`OpenRA.Mods.Common\Traits\Mobile.cs`) define movement speed, turning, blocking, and the pathing cost model. These parameters are read by `Move`.
- **Harvester** (`OpenRA.Mods.Common\Traits\Harvester.cs`) defines `BaleLoadDelay`, `HarvestFacings`, `Capacity`, and `HarvestLineColor`.
- **AttackFrontal** and related `Attack*` traits define weapon ranges, facing tolerance, and cooldowns.
- **DockClientManager** / **DockHost** define docking and unloading activities.
- **MapOptions** controls whether the shellmap is paused, which affects whether `World.Tick` increments the simulation (`World.cs`).

## Interconnectivity

### How traits create activities

Orders flow from the player through the input system, the order generator, and finally into the actor's `IResolveOrder` traits. The most common pattern is:

```csharp
void IResolveOrder.ResolveOrder(Actor self, Order order)
{
    if (order.OrderString == "Move")
    {
        self.QueueActivity(order.Queued, WrapMove(new Move(self, cell, WDist.FromCells(8), null, true, Info.TargetLineColor)));
        self.ShowTargetLines();
    }
}
```

(`OpenRA.Mods.Common\Traits\Mobile.cs`)

Other entry points:

- `ICreationActivity.GetCreationActivity()` returns an initial activity during `Actor.Initialize` (`Actor.cs`).
- `INotifyBecomingIdle.OnBecomingIdle()` can react to idleness and queue the next activity (`Actor.cs`).
- `INotifyIdle.TickIdle()` can run behavior while the actor has no activity (`Actor.cs`).
- `Scripting` properties (`ScriptActorPropertyActivity`) and bot modules directly call `QueueActivity`.

### How activities use traits

Activities query traits directly for state and capability:

- `Move` uses `Mobile` (pathfinding, movement speed, facing, subcell placement) and `IPositionable`.
- `Attack` uses `AttackFrontal`, `Armament`, `RevealsShroud`, `IFacing`, `IMove`, and `IPositionable`.
- `HarvestResource` uses `Harvester`, `IFacing`, `IMove`, `BodyOrientation`, `ResourceClaimLayer`, and `IResourceLayer`.

This is a **two-way relationship**: traits create activities, and activities call traits. Activities do not store the traits themselves; they fetch them from the actor each tick or cache them in `OnFirstRun`.

### Order queueing and activity replacement

- `QueueActivity(bool queued, Activity nextActivity)`:
  - If `queued` is `false`, it first calls `CancelActivity()` on the current activity, then queues the new activity.
  - If `queued` is `true`, it appends the new activity to the current queue via `CurrentActivity.Queue` (`Actor.cs`).
- Holding **Shift** in-game usually maps to `queued = true`, allowing the player to build up a sequence of move/attack/harvest orders.

![Algorithms diagram](images/Part_01_Chapter_02_Activities-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### The `RunActivity` loop

The runner uses a `do...while` loop to advance activities. Each iteration:

1. Capture the previous activity.
2. Call `TickOuter`.
3. Log the time if it was a long tick.
4. If the returned activity is the same as the previous one, break. The activity is not done and will be resumed next tick.
5. If the returned activity is different (a `NextActivity` or `null`), loop again.
6. Stop when the activity is `null`.

Because `TickOuter` can complete multiple children or siblings in a single call, a single [World](../appendices/Appendix_A_Glossary.md).Tick can drain a chain of instant activities.

### `SkipDoneActivities`

When an activity is cancelled while queued, it is marked `Done`. If it had a `NextActivity`, we must skip the dead node and continue to the next valid node. `SkipDoneActivities` walks the `nextActivity` chain until it finds a non-`Done` activity (`Activity.cs`). This is used by both `CurrentActivity` getter and `NextActivity` getter.

### `Move` path processing

`Move` in `OpenRA.Mods.Common\Activities\Move\Move.cs` is one of the most complex activities and demonstrates the design well.

1. `OnFirstRun`:
   - Records `startTicks = self.World.WorldTick` and sets `mobile.MoveResult = MoveResult.InProgress`.
   - If `evaluateNearestMovableCell`, finds the nearest cell the actor can stand in.
   - Tries pathfinding in `PathSearchOrder` (All, Stationary, Immovable, None) to find a route (`Move.cs`).
2. `Tick`:
   - If `IsCanceling` and the actor can stay in the current cell, clears the path and returns `MoveResult.CompleteCanceled` (`Move.cs`).
   - If `Mobile` is disabled or paused, returns `false` (wait) (`Move.cs`).
   - If already at the destination, completes.
   - Pops the next path cell via `PopPath`.
   - If the actor must turn in place first, queues a `Turn` child and returns `false` (`Move.cs`).
   - Otherwise sets the actor's location, computes from/to positions, and queues a `MoveFirstHalf` child (`Move.cs`).
3. `MovePart` (abstract):
   - Each `MovePart` advances `progress` by `mobile.MovementSpeedForCell(mobile.ToCell)` once per tick.
   - When `progress >= Distance`, it sets the actor's position, updates facing, and calls `OnComplete`, then queues the next move part.
   - `MoveFirstHalf.OnComplete` may queue `MoveSecondHalf`, or it may create another `MoveFirstHalf` if the path continues with a curved turn (`Move.cs`).
   - `MoveSecondHalf.OnComplete` calls `mobile.SetPosition` and carries over any remaining progress into the parent `Move` for the next cell (`Move.cs`).
4. `PopPath`:
   - Handles blockers, nudging, waiting, repathing, and backing up when the path is blocked.
   - Uses `self.World.ContainsTemporaryBlocker`, `mobile.CanEnterCell`, and `self.NotifyBlocker`.
5. `Cancel` is overridden to clear the path before calling `base.Cancel` so that the `MovePart` children cannot re-queue themselves (`Move.cs`).

### `Attack` parallel child behavior

`Attack` sets `ChildHasPriority = false` in its constructor (`Attack.cs`). This means the parent tick and the child tick can both run in the same frame.

```csharp
public override bool Tick(Actor self)
{
    if (!IsCanceling && !HasArmamentsFor(target))
        Cancel(self, true);

    if (!TickChild(self))
        return false;

    if (IsCanceling)
        return true;

    // ... recalculate target ...

    if (useLastVisibleTarget)
    {
        // ...
        moveCooldownHelper.NotifyMoveQueued();
        QueueChild(move.MoveWithinRange(target, WDist.Zero, lastVisibleMaximumRange, checkTarget.CenterPosition, Color.Red));
        return false;
    }

    // ... choose armaments, check range, turn, fire ...
    return true;
}
```

(`Attack.cs`)

Key points:

- `Attack` calls `TickChild` itself because it needs to know when the movement child is finished.
- It can return `true` (done) while a child is still running, so it must return `false` until the child is done.
- It queues `Move` children repeatedly to chase a target or move to the last known position.
- It performs in-place facing adjustment directly rather than queuing a `Turn` child for responsiveness.

### `HarvestResource` child chaining

`HarvestResource` uses the default `ChildHasPriority = true`. Its `Tick` chains children sequentially:

```csharp
public override bool Tick(Actor self)
{
    if (harv.IsTraitDisabled)
        Cancel(self, true);

    if (IsCanceling || harv.IsFull)
        return true;

    // ... move-cooldown helper ...

    if (self.Location != targetCell)
    {
        QueueChild(move.MoveTo(targetCell, 0));
        return false;
    }

    // Turn to harvestable facing
    if (desired != current)
    {
        QueueChild(new Turn(self, desired));
        return false;
    }

    // ... remove resource, add to harvester ...
    QueueChild(new Wait(harvInfo.BaleLoadDelay));
    return false;
}
```

(`HarvestResource.cs`)

This is the typical pattern for an activity that does one thing at a time: move to cell, then turn, then wait for the harvest animation, then continue on the next tick.

![Extension points diagram](images/Part_01_Chapter_02_Activities-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


To add a new activity, you typically:

1. Create a class inheriting from `Activity`.
2. Override `Tick(Actor self)` and return `false` while work remains and `true` when done.
3. Override `OnFirstRun(Actor self)` for state initialization that depends on the current world.
4. Override `OnLastRun(Actor self)` for cleanup.
5. Override `Cancel(Actor self, bool keepQueue)` if the default cancellation logic is insufficient.
6. Use `QueueChild(...)` to run sub-tasks, or `Queue(...)` inside the activity only when building a chain of siblings (rare from inside a child).
7. Implement `GetTargets` and `TargetLineNodes` if the activity should draw the target line and support unit commands.
8. Set `ChildHasPriority = false` if the parent must keep running while children are active (e.g., attacking while moving).
9. Set `IsInterruptible = false` for uninterruptible atomic actions (e.g., `MovePart` is uninterruptible so a move cannot stop mid-cell).
10. Hook into an `IResolveOrder`, `ICreationActivity`, `INotifyBecomingIdle`, or a script property to actually queue the activity.

### Common activity patterns

- **Single-tick activity:** `public override bool Tick(Actor self) { return true; }` completes immediately.
- **Wait N ticks:** `Wait` stores a tick count and decrements it.
- **Turn to face:** `Turn` stores a target facing and returns `true` once within tolerance.
- **Move to target:** `Move` or `move.MoveTo(...)` is the canonical child.
- **Repeat until condition:** `Tick` performs one step and returns `false`; each `QueueChild` advances the next step.

![Common pitfalls  guardrails diagram](images/Part_01_Chapter_02_Activities-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


The class header in `Activity.cs` lists four hard rules:

1. **Use `return true` at least once somewhere in the tick method.** An activity that never returns `true` will run forever.
2. **Do not reuse activity objects.** Never queue an activity that has already started running as a next or child activity. Always create a new instance.
3. **Avoid calling `actor.CancelActivity()`.** It is almost always a bug. Call `activity.Cancel()` instead.
4. **Do not evaluate dynamic state in the constructor.** Use `OnFirstRun` for state that depends on the world at tick time.

Additional pitfalls:

- **Child priority vs parent return value.** If `ChildHasPriority` is `false`, the parent `Tick` must return `false` until the child is finished. Returning `true` while a child is still active will skip the child and likely leave the actor in a bad state.
- **Disabling a trait does not cancel the activity.** `Move` checks `mobile.IsTraitDisabled || mobile.IsTraitPaused` and returns `false` (waits) until the trait is re-enabled (`Move.cs`). `HarvestResource` calls `Cancel(self, true)` when the harvester is disabled. Each activity decides its own policy.
- **Pausing the world vs pausing the activity.** `World.Paused` prevents `WorldTick` from advancing, so no activity `Tick` is called. The activity itself does not need to know about pause.
- **Cancellation must leave a consistent state.** The comment on `Tick` says: "Cancelled activities must ensure they return the actor to a consistent state before returning true" (`Activity.cs`).
- **One-tick idle gap.** `Actor.Tick` detects the transition from "not idle" to "idle" and runs the activity runner a second time if `OnBecomingIdle` queued a new activity. Activity authors should not assume that the actor will be idle for a visible frame.
- **ActionQueue is not for game logic.** `ActionQueue` is for deferred UI/disposal tasks. Do not use it for actor-level state that must be deterministic or sync-safe.

## Summary

This chapter explains how OpenRA turns player orders into multi-tick, interruptible [actor](../appendices/Appendix_A_Glossary.md) behavior.

After reading this chapter, you should be able to:

- Distinguish traits (persistent state) from activities (transient plans).
- Explain how activities are queued, chained, and interrupted.
- Trace the `TickOuter` / `TickChild` loop and understand `ChildHasPriority`.
- Implement a simple custom activity that moves or waits.
- Diagnose activity-related bugs such as stuck units or infinite loops.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game\Activities\Activity.cs` — state machine, states, chaining, `TickOuter`, `TickChild`, `Cancel`, `Queue`, `QueueChild`, `OnFirstRun`, `OnLastRun`, `OnActorDispose`.
- `OpenRA.Game\Traits\ActivityUtils.cs` — `RunActivity` hot-path runner.
- `OpenRA.Game\Primitives\ActionQueue.cs` — global thread-safe delayed action queue.
- `OpenRA.Game\Actor.cs` — `CurrentActivity`, `QueueActivity`, `CancelActivity`, `Tick`, and `OnBecomingIdle` / `INotifyIdle` handling.
- `OpenRA.Game\World.cs` — `WorldTick`, `Tick`, and trait/effect ticking.

## What to read next

- Now that you understand how activities queue, chain, and tick, read [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) to learn how player input becomes the orders that create activities.
- Now that you can trace `Move` and its child activities, read [Part 1.5 — Pathfinding and Movement](Part_01_Chapter_05_Pathfinding_Movement.md) to see how the engine plans routes and turns them into movement activities.
- If the trait/activity split still feels abstract, review [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md) to solidify how traits own persistent state while activities own transient plans.
- For debugging stuck units and activity loops, see [Appendix C — Debugging and Troubleshooting](../appendices/Appendix_C_Debugging.md).
- For the order generator and UI side of the order-to-activity pipeline, see [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md).