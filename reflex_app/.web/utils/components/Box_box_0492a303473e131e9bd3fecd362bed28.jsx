
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_0492a303473e131e9bd3fecd362bed28 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a89b9dd381a650f371dde89e394162bd = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_type", ({ ["t"] : "in" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "in"?.valueOf?.()) ? ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'Share Tech Mono', monospace", ["border"] : "1px solid #34d399", ["color"] : "#34d399", ["background"] : "#34d3991a" }) : ({ ["flex"] : "1", ["padding"] : "9px", ["border_radius"] : "8px", ["cursor"] : "pointer", ["text_align"] : "center", ["font_size"] : "12px", ["letter_spacing"] : "0.06em", ["font_family"] : "'Share Tech Mono', monospace", ["border"] : "1px solid #252535", ["color"] : "#6868a2", ["background"] : "#1c1c25", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_a89b9dd381a650f371dde89e394162bd},children)
    )
});
