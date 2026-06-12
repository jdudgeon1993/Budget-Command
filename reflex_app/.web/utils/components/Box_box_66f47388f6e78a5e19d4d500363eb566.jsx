
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_66f47388f6e78a5e19d4d500363eb566 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_193944eafea9d64da5aa0f9c4f4e7958 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_range", ({ ["n"] : 3 }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_range_rx_state_?.valueOf?.() === 3?.valueOf?.()) ? ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#818cf8", ["color"] : "#fff", ["border"] : "1px solid #818cf8" }) : ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#1c1c25", ["color"] : "#6868a2", ["border"] : "1px solid #252535", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_193944eafea9d64da5aa0f9c4f4e7958},children)
    )
});
