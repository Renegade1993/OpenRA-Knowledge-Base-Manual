// TEST DROP-IN — Appendix G, Walkthrough 1 (Chrome UI panel logic).
// Place this file in:  OpenRA.Mods.Common\Widgets\Logic\
// Namespace changed from "OpenRA.Mods.MyMod.Widgets.Logic" to
// "OpenRA.Mods.Common.Widgets.Logic" so it compiles inside the engine assembly.
// DELETE this file after `make.cmd all` succeeds.
using System.Collections.Generic;
using OpenRA;
using OpenRA.Mods.Common.Lint;
using OpenRA.Widgets;

namespace OpenRA.Mods.Common.Widgets.Logic
{
    [ChromeLogicArgsHotkeys("ToggleMyPanelKey")]
    public class MyPanelLogic : ChromeLogic
    {
        [ObjectCreator.UseCtor]
        public MyPanelLogic(Widget widget, Dictionary<string, MiniYaml> logicArgs)
        {
            widget.Get<ButtonWidget>("CLOSE_BUTTON").OnClick = Ui.CloseWindow;
        }
    }
}
