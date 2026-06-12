
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_64f55c500bcc6f07c1646f2bd4816541 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_142d01e1cf9247bfc31502a85236f69a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_reports_tab", ({ ["tab"] : "payees" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.reports_tab_rx_state_?.valueOf?.() === "payees"?.valueOf?.()) ? ({ ["padding"] : "7px 14px", ["border_radius"] : "8px", ["background"] : "#BF5AF220", ["color"] : "#BF5AF2", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["cursor"] : "pointer", ["white_space"] : "nowrap", ["border"] : "1px solid #BF5AF244" }) : ({ ["padding"] : "7px 14px", ["border_radius"] : "8px", ["background"] : "transparent", ["color"] : "#606088", ["font_size"] : "12px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["cursor"] : "pointer", ["white_space"] : "nowrap", ["_hover"] : ({ ["color"] : "#9090B8", ["background"] : "rgba(255,255,255,0.08)" }) })) }),onClick:on_click_142d01e1cf9247bfc31502a85236f69a},children)
    )
});
