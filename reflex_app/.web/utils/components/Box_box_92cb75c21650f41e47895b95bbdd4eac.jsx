
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_92cb75c21650f41e47895b95bbdd4eac = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a92dc7e54d97ed2205535853b1462afa = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_range", ({ ["n"] : 6 }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_range_rx_state_?.valueOf?.() === 6?.valueOf?.()) ? ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#818cf8", ["color"] : "#fff", ["border"] : "1px solid #818cf8" }) : ({ ["padding"] : "4px 12px", ["border_radius"] : "16px", ["cursor"] : "pointer", ["font_size"] : "11px", ["font_family"] : "'Share Tech Mono', monospace", ["letter_spacing"] : "0.06em", ["background"] : "#1c1c25", ["color"] : "#4e4e6a", ["border"] : "1px solid #252535", ["_hover"] : ({ ["color"] : "#8282a2", ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_a92dc7e54d97ed2205535853b1462afa},children)
    )
});
