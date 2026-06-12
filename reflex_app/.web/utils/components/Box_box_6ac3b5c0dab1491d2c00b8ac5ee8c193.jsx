
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_6ac3b5c0dab1491d2c00b8ac5ee8c193 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_711f04b9aa7d5b068d0d0d8e9b1a1711 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "buckets" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{"aria-label":"Buckets",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "buckets"?.valueOf?.()) ? ({ ["display"] : "flex", ["align_items"] : "center", ["gap"] : "10px", ["padding"] : "10px 10px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["background"] : "#818cf81f", ["color"] : "#818cf8", ["user_select"] : "none", ["_focus_visible"] : ({ ["outline"] : "2px solid #818cf8", ["outline_offset"] : "2px" }) }) : ({ ["display"] : "flex", ["align_items"] : "center", ["gap"] : "10px", ["padding"] : "10px 10px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["color"] : "#6868a2", ["user_select"] : "none", ["_hover"] : ({ ["background"] : "#1c1c25", ["color"] : "#8282a2" }), ["_focus_visible"] : ({ ["outline"] : "2px solid #818cf8", ["outline_offset"] : "2px" }) })) }),onClick:on_click_711f04b9aa7d5b068d0d0d8e9b1a1711,role:"button",tabIndex:0},children)
    )
});
