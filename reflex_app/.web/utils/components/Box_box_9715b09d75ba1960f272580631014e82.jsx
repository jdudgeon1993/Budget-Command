
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9715b09d75ba1960f272580631014e82 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_0a886cd5d83f9803689362c07c313f26 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_account", ({ ["aid"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_account_rx_state_?.valueOf?.() === ""?.valueOf?.()) ? ({ ["padding"] : "4px 10px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["border"] : "1px solid #818cf8", ["background"] : "#818cf818", ["font_size"] : "11px", ["color"] : "#818cf8" }) : ({ ["padding"] : "4px 10px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["border"] : "1px solid #252535", ["background"] : "#1c1c25", ["font_size"] : "11px", ["color"] : "#4e4e6a", ["_hover"] : ({ ["border_color"] : "#3c3c56" }) })) }),onClick:on_click_0a886cd5d83f9803689362c07c313f26},children)
    )
});
