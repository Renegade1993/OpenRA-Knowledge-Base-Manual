# Paste-ready YAML snippets for Part 2 (`--check-yaml`)

Paste these into the `rules.yaml` of your throwaway `manual-test` map, then run
`utility.cmd ra --check-yaml`. Each block below is **self-contained** (no elided `...` lines) so it
validates as written. They override/extend existing RA actors, so the validator resolves inheritance.

> Note: many snippets in the manual use a bare `...` to mean "other fields elided." Those are
> illustrative fragments (already statically verified) and are **not** meant to be pasted literally —
> `...` is not valid MiniYAML. The three blocks here are the clean, paste-as-is ones.

---

## A. Custom crate rewards (Appendix G, Walkthrough 3)

```yaml
CRATE:
    Inherits: ^Crate
    GiveCashCrateAction:
        Amount: 1000
        SelectionShares: 30
        UseCashTick: true
    GiveCashCrateAction@BIGBONUS:
        Amount: 5000
        SelectionShares: 5
        UseCashTick: true
    GiveUnitCrateAction@RANDOMLIGHT:
        SelectionShares: 15
        Units: jeep, 1tnk, apc, ftrk
        ValidFactions: allies, england, france, germany, soviet, russia, ukraine
        Prerequisites: techlevel.low
    GiveUnitCrateAction@RANDOMHEAVY:
        SelectionShares: 8
        Units: 2tnk, 3tnk, v2rl, arty
        ValidFactions: allies, england, france, germany, soviet, russia, ukraine
        Prerequisites: techlevel.medium, fix
```

---

## B. Capture/engineer mechanic (Appendix G, Walkthrough 6)

```yaml
E6:
    Inherits: ^Soldier
    Inherits@selection: ^SelectableSupportUnit
    Buildable:
        Queue: Infantry
        BuildAtProductionType: Soldier
        BuildPaletteOrder: 60
        Prerequisites: ~barracks, ~techlevel.infonly
        Description: actor-e6.description
    Valued:
        Cost: 400
    Tooltip:
        Name: actor-e6.name
    CaptureManager:
    Captures:
        CaptureTypes: building
        PlayerExperience: 10
        CaptureDelay: 200
        ConsumedByCapture: true
        SabotageThreshold: 0
        EnterCursor: enter
        EnterBlockedCursor: enter-blocked
    Voiced:
        VoiceSet: EngineerVoice
    -AttackFrontal:
```

---

## C. Turtle AI bot (Appendix G, Walkthrough 9)

```yaml
Player:
    ModularBot@TurtleAI:
        Name: bot-turtle-ai.name
        Type: turtle

    GrantConditionOnBotOwner@turtle:
        Condition: enable-turtle-ai
        Bots: turtle

    ResourceMapBotModule:
        RequiresCondition: enable-turtle-ai
        ResourceCreatorTypes: mine, gmine
        ValuableResourceTypes: Ore, Gems
        HarvesterTypes: harv
        RefineryTypes: proc
        EnemyBaseBuildingTypes: pbox,gun,ftur,tsla,agun,barr,tent,weap,afld,hpad,fact,powr,apwr,proc

    HarvesterBotModule@turtle:
        RequiresCondition: enable-turtle-ai
        HarvesterTypes: harv
        RefineryTypes: proc
        InitialHarvesters: 6

    BaseBuilderBotModule@turtle:
        RequiresCondition: enable-turtle-ai
        MinimumExcessPower: 0
        MaximumExcessPower: 250
        ExcessPowerIncrement: 80
        ExcessPowerIncreaseThreshold: 4
        ConstructionYardTypes: fact
        RefineryTypes: proc
        PowerTypes: powr,apwr
        TechTypes: mslo, dome, atek, stek, fix
        ProductionTypes: barr,tent,weap,afld,hpad
        NewProductionCashThreshold: 7000
        SiloTypes: silo
        DefenseTypes: hbox,pbox,gun,ftur,tsla,agun,sam
        BuildingLimits:
            barr: 5
            tent: 5
            kenn: 1
            dome: 1
            weap: 3
            afld: 2
            hpad: 2
            atek: 1
            stek: 1
            fix: 1
            powr: 8
            apwr: 8
            proc: 4
            pbox: 10
            gun: 10
            tsla: 6
            agun: 6
            sam: 6
        BuildingFractions:
            powr: 2
            apwr: 2
            proc: 4
            barr: 2
            tent: 2
            kenn: 1
            weap: 2
            afld: 1
            hpad: 1
            pbox: 8
            gun: 8
            tsla: 6
            agun: 6
            sam: 6
            dome: 4
            atek: 1
            stek: 1
            fix: 1
        BuildingDelays:
            pbox: 1000
            gun: 1500
            tsla: 2000

    SquadManagerBotModule@turtle:
        RequiresCondition: enable-turtle-ai
        SquadSize: 12
        SquadSizeRandomBonus: 4
        RushInterval: 6000
        MinimumAttackForceCount: 20
        ProtectUnitScanInterval: 50
        AssignRolesInterval: 100
        AttackForceInterval: 100
        UnitsToBuild:
            e1: 60
            e3: 40
            e4: 30
            e6: 1
            1tnk: 20
            2tnk: 30
            3tnk: 30
            v2rl: 20
            arty: 20
            yak: 10
            mig: 10

    SupportPowerBotModule:
        RequiresCondition: enable-turtle-ai
        Decisions:
            nukepower:
                OrderName: NukePowerInfoOrder
                MinimumAttractiveness: 3000
                Consideration@1:
                    Against: Enemy
                    Types: Structure
                    Attractiveness: 1
                    TargetMetric: Value
                    CheckRadius: 5c0
```

> If `--check-yaml` flags a missing fluent string (e.g. `bot-turtle-ai.name`, `actor-e6.description`),
> that's expected for a bare test map and is **not** a snippet error — it means the text key isn't
> defined in the test map. The trait/field validation is what we care about; note any error that names
> a **trait or field** instead.
