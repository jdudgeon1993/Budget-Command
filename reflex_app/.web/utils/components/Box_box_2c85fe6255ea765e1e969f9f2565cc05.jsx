
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_2c85fe6255ea765e1e969f9f2565cc05 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_686e410957d1c939625454b57ce01904 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_wi_rp_tab", ({ ["tab"] : "periods" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.wi_rp_tab_rx_state_?.valueOf?.() === "periods"?.valueOf?.()) ? ({ ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["padding"] : "4px 12px", ["border_radius"] : "14px", ["cursor"] : "pointer", ["background"] : "#BF5AF220", ["color"] : "#D8A4FF", ["border"] : "1px solid #BF5AF244" }) : ({ ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["padding"] : "4px 12px", ["border_radius"] : "14px", ["cursor"] : "pointer", ["background"] : "transparent", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8" }) })) }),onClick:on_click_686e410957d1c939625454b57ce01904,role:"button",tabIndex:0},children)
    )
});
