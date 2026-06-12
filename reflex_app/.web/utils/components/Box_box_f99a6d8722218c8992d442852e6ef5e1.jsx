
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_f99a6d8722218c8992d442852e6ef5e1 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_176399816e93d1a9d90fb09a8fb0c5bf = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "reports" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{"aria-label":"Reports",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "reports"?.valueOf?.()) ? ({ ["display"] : "flex", ["align_items"] : "center", ["gap"] : "10px", ["padding"] : "9px 10px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["background"] : "rgba(191,90,242,0.14)", ["color"] : "#D8A4FF", ["user_select"] : "none", ["_focus_visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outline_offset"] : "2px" }) }) : ({ ["display"] : "flex", ["align_items"] : "center", ["gap"] : "10px", ["padding"] : "9px 10px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["color"] : "#606088", ["user_select"] : "none", ["_hover"] : ({ ["background"] : "rgba(255,255,255,0.05)", ["color"] : "#9090B8" }), ["_focus_visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outline_offset"] : "2px" }) })) }),onClick:on_click_176399816e93d1a9d90fb09a8fb0c5bf,role:"button",tabIndex:0},children)
    )
});
