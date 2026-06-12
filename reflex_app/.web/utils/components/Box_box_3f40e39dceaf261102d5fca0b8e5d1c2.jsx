
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_3f40e39dceaf261102d5fca0b8e5d1c2 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_3afd465f89ffb4133e30b4f20295ae5a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "setup" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["color"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "setup"?.valueOf?.()) ? "#818cf8" : "#6868a2"), ["cursor"] : "pointer", ["padding"] : "6px", ["borderRadius"] : "8px", ["&:hover"] : ({ ["color"] : "#8282a2" }), ["&:active"] : ({ ["opacity"] : "0.7" }) }),onClick:on_click_3afd465f89ffb4133e30b4f20295ae5a},children)
    )
});
