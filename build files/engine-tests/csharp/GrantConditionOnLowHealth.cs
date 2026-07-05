// TEST DROP-IN — Part 0 "Foundations" custom-trait snippet.
// Place this file in:  OpenRA.Mods.Common\Traits\
// Namespace changed from the manual's "MyMod.Traits" to "OpenRA.Mods.Common.Traits"
// so it compiles inside the engine's own assembly during the quick verification build.
// DELETE this file after `make.cmd all` succeeds.
using OpenRA;
using OpenRA.Traits;

namespace OpenRA.Mods.Common.Traits
{
    [Desc("Grants a condition while the actor's health is below a threshold.")]
    public class GrantConditionOnLowHealthInfo : TraitInfo, Requires<IHealthInfo>
    {
        [FieldLoader.Require]
        [GrantedConditionReference]
        [Desc("Condition to grant when health is below the threshold.")]
        public readonly string Condition = null;

        [Desc("Health threshold, as a fraction of total HP (0-1).")]
        public readonly float Threshold = 0.5f;

        public override object Create(ActorInitializer init) { return new GrantConditionOnLowHealth(init.Self, this); }
    }

    public class GrantConditionOnLowHealth : INotifyCreated, INotifyDamage
    {
        readonly GrantConditionOnLowHealthInfo info;
        readonly IHealth health;

        int conditionToken = Actor.InvalidConditionToken;

        public GrantConditionOnLowHealth(Actor self, GrantConditionOnLowHealthInfo info)
        {
            this.info = info;
            health = self.Trait<IHealth>();
        }

        void INotifyCreated.Created(Actor self)
        {
            UpdateCondition(self);
        }

        void INotifyDamage.Damaged(Actor self, AttackInfo e)
        {
            UpdateCondition(self);
        }

        void UpdateCondition(Actor self)
        {
            var lowHealth = health.HP < health.MaxHP * info.Threshold;
            var granted = conditionToken != Actor.InvalidConditionToken;

            if (lowHealth && !granted)
                conditionToken = self.GrantCondition(info.Condition);
            else if (!lowHealth && granted)
                conditionToken = self.RevokeCondition(conditionToken);
        }
    }
}
