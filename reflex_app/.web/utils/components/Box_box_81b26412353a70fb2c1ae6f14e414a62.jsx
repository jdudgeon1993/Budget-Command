
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_81b26412353a70fb2c1ae6f14e414a62 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a89b9dd381a650f371dde89e394162bd = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_type", ({ ["t"] : "in" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "in"?.valueOf?.()) ? ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'JetBrains Mono', monospace", ["border"] : "1px solid #30D158", ["color"] : "#30D158", ["background"] : "#30D1581a" }) : ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'JetBrains Mono', monospace", ["border"] : "1px solid rgba(255,255,255,0.08)", ["color"] : "#606088", ["background"] : "rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_a89b9dd381a650f371dde89e394162bd},children)
    )
});
