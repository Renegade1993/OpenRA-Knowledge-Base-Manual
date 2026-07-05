--[[
   TEST MISSION — Appendix G, Walkthrough 2.
   Verifies: WorldLoaded entry point, objectives (campaign.lua / utils.lua helpers),
   AfterDelay attack wave, and OnRemovedFromWorld / OnCapture win/lose triggers.
]]

WorldLoaded = function()
    USSR = Player.GetPlayer("USSR")
    Germany = Player.GetPlayer("Germany")

    InitObjectives(USSR)

    -- Primary objective: destroy the German weapons factory.
    DestroyFactoryObjective = AddPrimaryObjective(USSR, "destroy-enemy-factory")

    -- Schedule an attack wave after 2 minutes.
    Trigger.AfterDelay(DateTime.Seconds(120), function()
        Media.PlaySpeechNotification(USSR, "ReinforcementsArrived")
        local wave = Reinforcements.Reinforce(Germany, { "e1", "e1", "e3", "2tnk" }, { EnemyEntry.Location }, 10)
        Utils.Do(wave, function(a)
            a.AttackMove(Actor3.Location)
        end)
    end)

    -- Defeat condition: lose the Construction Yard (destroyed, sold, or captured).
    Trigger.OnRemovedFromWorld(Actor0, function()
        USSR.MarkFailedObjective(DestroyFactoryObjective)
    end)

    Trigger.OnCapture(Actor0, function()
        USSR.MarkFailedObjective(DestroyFactoryObjective)
    end)

    -- Victory condition: destroy the enemy factory.
    Trigger.OnRemovedFromWorld(Actor3, function()
        USSR.MarkCompletedObjective(DestroyFactoryObjective)
    end)
end

Tick = function()
    -- Fallback: if the Construction Yard is gone or no longer ours, fail.
    if Actor0.IsDead or Actor0.Owner ~= USSR then
        USSR.MarkFailedObjective(DestroyFactoryObjective)
    end

    -- Fallback: if the enemy factory is gone, win.
    if Actor3.IsDead then
        USSR.MarkCompletedObjective(DestroyFactoryObjective)
    end
end
