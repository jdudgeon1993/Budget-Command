
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_50e89e49d14cb1db33e27bfb56537ae9 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_28475cb91808a86d657b09b7fd6c382d = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_type", ({ ["t"] : "out" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'JetBrains Mono', monospace", ["border"] : "1px solid #FF453A", ["color"] : "#FF453A", ["background"] : "#FF453A1a" }) : ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'JetBrains Mono', monospace", ["border"] : "1px solid rgba(255,255,255,0.08)", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_28475cb91808a86d657b09b7fd6c382d},children)
    )
});
