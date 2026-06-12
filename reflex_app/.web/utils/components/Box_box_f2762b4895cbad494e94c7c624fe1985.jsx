
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_f2762b4895cbad494e94c7c624fe1985 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_8098789c671ed4c04af03cc1ef17cc30 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "insights" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "insights"?.valueOf?.()) ? ({ ["display"] : "flex", ["align_items"] : "center", ["gap"] : "10px", ["padding"] : "9px 10px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["background"] : "#818cf81f", ["color"] : "#818cf8", ["user_select"] : "none" }) : ({ ["display"] : "flex", ["align_items"] : "center", ["gap"] : "10px", ["padding"] : "9px 10px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["color"] : "#4e4e6a", ["user_select"] : "none", ["_hover"] : ({ ["background"] : "#1c1c25", ["color"] : "#8282a2" }) })) }),onClick:on_click_8098789c671ed4c04af03cc1ef17cc30},children)
    )
});
