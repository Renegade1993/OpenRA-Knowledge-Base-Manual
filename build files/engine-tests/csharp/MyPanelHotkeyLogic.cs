// TEST DROP-IN — Appendix G, Walkthrough 1 (Chrome UI hotkey logic).
// Place this file in:  OpenRA.Mods.Common\Widgets\Logic\
// Namespace changed from "OpenRA.Mods.MyMod.Widgets.Logic" to
// "OpenRA.Mods.Common.Widgets.Logic" so it compiles inside the engine assembly.
// DELETE this file after `make.cmd all` succeeds.
using System.Collections.Generic;
using OpenRA;
using OpenRA.Widgets;

namespace OpenRA.Mods.Common.Widgets.Logic
{
    public class MyPanelHotkeyLogic : ChromeLogic
    {
        [ObjectCreator.UseCtor]
        public MyPanelHotkeyLogic(Widget widget, ModData modData, Dictionary<string, MiniYaml> logicArgs)
        {
            var key = new HotkeyReference();
            if (logicArgs.TryGetValue("ToggleMyPanelKey", out var yaml))
                key = modData.Hotkeys[yaml.Value];

            var keyhandler = widget.Get<LogicKeyListenerWidget>("WORLD_KEYHANDLER");
            keyhandler.AddHandler(e =>
            {
                if (e.Event == KeyInputEvent.Down && key.IsActivatedBy(e))
                {
                    Ui.OpenWindow("MY_PANEL", new WidgetArgs());
                    return true;
                }

                return false;
            });
        }
    }
}
