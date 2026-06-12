
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_be8cbc669f7118dc5ddf4afd70272c6b = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d84de036458abb2727bb1456e7bc6b77 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_insights_tab", ({ ["tab"] : "forecast" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.insights_tab_rx_state_?.valueOf?.() === "forecast"?.valueOf?.()) ? ({ ["padding"] : "5px 16px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#818cf8", ["color"] : "#fff", ["border"] : "1px solid #818cf8" }) : ({ ["padding"] : "5px 16px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#1c1c25", ["color"] : "#6868a2", ["border"] : "1px solid #252535", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_d84de036458abb2727bb1456e7bc6b77},children)
    )
});
