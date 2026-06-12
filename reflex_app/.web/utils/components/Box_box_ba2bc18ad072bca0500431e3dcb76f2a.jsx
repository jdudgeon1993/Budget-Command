
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_ba2bc18ad072bca0500431e3dcb76f2a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_70466cabeb414502ba29d63ef6fe10a8 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_range", ({ ["n"] : 2 }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_range_rx_state_?.valueOf?.() === 2?.valueOf?.()) ? ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#BF5AF2", ["color"] : "#fff", ["border"] : "1px solid #BF5AF2" }) : ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_70466cabeb414502ba29d63ef6fe10a8},children)
    )
});
