
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_02d654a9ccae45eca3785efd12ed5aee = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_34e96e7ba8f8880c4df4bb74e1b7a2e1 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_wi_rp_tab", ({ ["tab"] : "intel" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.wi_rp_tab_rx_state_?.valueOf?.() === "intel"?.valueOf?.()) ? ({ ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["padding"] : "4px 12px", ["border_radius"] : "14px", ["cursor"] : "pointer", ["background"] : "#BF5AF220", ["color"] : "#D8A4FF", ["border"] : "1px solid #BF5AF244" }) : ({ ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["padding"] : "4px 12px", ["border_radius"] : "14px", ["cursor"] : "pointer", ["background"] : "transparent", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8" }) })) }),onClick:on_click_34e96e7ba8f8880c4df4bb74e1b7a2e1,role:"button",tabIndex:0},children)
    )
});
