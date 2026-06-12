
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Flex as RadixThemesFlex} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Vstack_flex_ba3116f1684e94d59aa861504f9a7567 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_176399816e93d1a9d90fb09a8fb0c5bf = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_panel", ({ ["name"] : "reports" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesFlex,{align:"start","aria-current":((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "reports"?.valueOf?.()) ? "page" : "false"),"aria-label":"Reports",className:"rx-Stack",css:({ ["&"] : ((reflex___state____state__cura___state____app_state.active_panel_rx_state_?.valueOf?.() === "reports"?.valueOf?.()) ? ({ ["color"] : "#D8A4FF", ["cursor"] : "pointer", ["align_items"] : "center", ["gap"] : "4px", ["flex"] : "1", ["justify_content"] : "center", ["min_height"] : "44px", ["padding"] : "4px 0", ["_focus_visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outline_offset"] : "2px" }) }) : ({ ["color"] : "rgba(255,255,255,0.30)", ["cursor"] : "pointer", ["align_items"] : "center", ["gap"] : "4px", ["flex"] : "1", ["justify_content"] : "center", ["min_height"] : "44px", ["padding"] : "4px 0", ["_hover"] : ({ ["color"] : "rgba(255,255,255,0.60)" }), ["_focus_visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outline_offset"] : "2px" }) })) }),direction:"column",onClick:on_click_176399816e93d1a9d90fb09a8fb0c5bf,role:"button",gap:"3",tabIndex:0},children)
    )
});
