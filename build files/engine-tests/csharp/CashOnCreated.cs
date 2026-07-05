// TEST DROP-IN — Appendix E, Recipe 6 custom-trait snippet.
// Place this file in:  OpenRA.Mods.Common\Traits\
// Namespace changed from "OpenRA.Mods.MyMod.Traits" to "OpenRA.Mods.Common.Traits"
// so PlayerResources resolves and it compiles inside the engine assembly.
// DELETE this file after `make.cmd all` succeeds.
using OpenRA;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
    [Desc("Grants a cash bonus to the owner when this actor is created.")]
    public class CashOnCreatedInfo : TraitInfo
    {
        [FieldLoader.Require]
        [Desc("Cash amount to grant when the actor is created.")]
        public readonly int Amount = 0;

        public override object Create(ActorInitializer init) { return new CashOnCreated(init, this); }
    }

    public class CashOnCreated : INotifyCreated
    {
        readonly CashOnCreatedInfo info;

        public CashOnCreated(ActorInitializer init, CashOnCreatedInfo info)
        {
            this.info = info;
        }

        void INotifyCreated.Created(Actor self)
        {
            // PlayerResources lives on the player actor, not on the unit itself.
            var playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
            playerResources.GiveCash(info.Amount);
        }
    }
}
