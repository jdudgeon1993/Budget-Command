
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_71957e9b53d02b43b610f45a2c50e86c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_4552d49f033415bb124de0089a9cc961 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_reports_tab", ({ ["tab"] : "bva" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.reports_tab_rx_state_?.valueOf?.() === "bva"?.valueOf?.()) ? ({ ["padding"] : "7px 14px", ["border_radius"] : "8px", ["background"] : "#BF5AF220", ["color"] : "#BF5AF2", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["cursor"] : "pointer", ["white_space"] : "nowrap", ["border"] : "1px solid #BF5AF244" }) : ({ ["padding"] : "7px 14px", ["border_radius"] : "8px", ["background"] : "transparent", ["color"] : "#606088", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["cursor"] : "pointer", ["white_space"] : "nowrap", ["_hover"] : ({ ["color"] : "#9090B8", ["background"] : "rgba(255,255,255,0.08)" }) })) }),onClick:on_click_4552d49f033415bb124de0089a9cc961},children)
    )
});
