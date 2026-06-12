
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_adba02120de2d304514cd043b26533c9 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_c8d172ce6ec084e73e617adaad810454 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_new_cat_color", ({ ["value"] : "#38bdf8" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "22px", ["height"] : "22px", ["borderRadius"] : "50%", ["background"] : "#38bdf8", ["cursor"] : "pointer", ["flexShrink"] : "0", ["border"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#38bdf8"?.valueOf?.()) ? "2px solid #fff" : "2px solid transparent"), ["boxShadow"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#38bdf8"?.valueOf?.()) ? "0 0 0 2px #38bdf8" : "none"), ["&:hover"] : ({ ["transform"] : "scale(1.15)" }) }),onClick:on_click_c8d172ce6ec084e73e617adaad810454},)
    )
});
