
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_387ccab28f40880abf278d25a20dbeb1 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d9757528995444ce8ccd28d38d357279 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_insights_tab", ({ ["tab"] : "whatif" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.insights_tab_rx_state_?.valueOf?.() === "whatif"?.valueOf?.()) ? ({ ["padding"] : "5px 16px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#BF5AF220", ["color"] : "#D8A4FF", ["border"] : "1px solid #BF5AF244" }) : ({ ["padding"] : "5px 16px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "transparent", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_d9757528995444ce8ccd28d38d357279},children)
    )
});
