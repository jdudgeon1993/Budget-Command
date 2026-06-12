
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_caf9b4bf750775fded816d58ffb95acf = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_0f3739694dbe1a62e05691e4f75b6af8 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_type", ({ ["t"] : "xfr" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "xfr"?.valueOf?.()) ? ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'JetBrains Mono', monospace", ["border"] : "1px solid #9090B8", ["color"] : "#9090B8", ["background"] : "#9090B81a" }) : ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'JetBrains Mono', monospace", ["border"] : "1px solid rgba(255,255,255,0.08)", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_0f3739694dbe1a62e05691e4f75b6af8},children)
    )
});
