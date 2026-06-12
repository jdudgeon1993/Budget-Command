
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_07288ad02d61cee1da7f869be8d07d93 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_913651c5c00a6da7e3d4f30bb342828b = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_range", ({ ["n"] : 12 }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_range_rx_state_?.valueOf?.() === 12?.valueOf?.()) ? ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#BF5AF2", ["color"] : "#fff", ["border"] : "1px solid #BF5AF2" }) : ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'JetBrains Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "rgba(255,255,255,0.08)", ["color"] : "#606088", ["border"] : "1px solid rgba(255,255,255,0.08)", ["_hover"] : ({ ["color"] : "#9090B8", ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_913651c5c00a6da7e3d4f30bb342828b},children)
    )
});
