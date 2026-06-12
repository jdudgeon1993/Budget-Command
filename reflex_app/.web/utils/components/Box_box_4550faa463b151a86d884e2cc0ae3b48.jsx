
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_4550faa463b151a86d884e2cc0ae3b48 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_142d01e1cf9247bfc31502a85236f69a = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_reports_tab", ({ ["tab"] : "payees" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.reports_tab_rx_state_?.valueOf?.() === "payees"?.valueOf?.()) ? ({ ["padding"] : "7px 14px", ["border_radius"] : "8px", ["background"] : "#818cf820", ["color"] : "#818cf8", ["font_size"] : "12px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["cursor"] : "pointer", ["white_space"] : "nowrap", ["border"] : "1px solid #818cf844" }) : ({ ["padding"] : "7px 14px", ["border_radius"] : "8px", ["background"] : "transparent", ["color"] : "#6868a2", ["font_size"] : "12px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["cursor"] : "pointer", ["white_space"] : "nowrap", ["_hover"] : ({ ["color"] : "#8282a2", ["background"] : "#1c1c25" }) })) }),onClick:on_click_142d01e1cf9247bfc31502a85236f69a},children)
    )
});
