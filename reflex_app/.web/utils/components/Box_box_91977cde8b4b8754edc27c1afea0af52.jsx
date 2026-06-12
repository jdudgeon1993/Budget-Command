
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_91977cde8b4b8754edc27c1afea0af52 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_0a886cd5d83f9803689362c07c313f26 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_forecast_account", ({ ["aid"] : "" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["&"] : ((reflex___state____state__cura___state____app_state.forecast_account_rx_state_?.valueOf?.() === ""?.valueOf?.()) ? ({ ["padding"] : "4px 10px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["border"] : "1px solid #BF5AF2", ["background"] : "#BF5AF218", ["font_size"] : "11px", ["color"] : "#BF5AF2" }) : ({ ["padding"] : "4px 10px", ["border_radius"] : "20px", ["cursor"] : "pointer", ["border"] : "1px solid rgba(255,255,255,0.08)", ["background"] : "rgba(255,255,255,0.08)", ["font_size"] : "11px", ["color"] : "#606088", ["_hover"] : ({ ["border_color"] : "rgba(255,255,255,0.14)" }) })) }),onClick:on_click_0a886cd5d83f9803689362c07c313f26},children)
    )
});
