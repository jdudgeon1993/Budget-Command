
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_300ad06ca755c6914cd14a0d6c590fe9 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_7a9e0f29d37f133345b27a8d8bf69ba0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_new_cat_color", ({ ["value"] : "#a78bfa" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "22px", ["height"] : "22px", ["borderRadius"] : "50%", ["background"] : "#a78bfa", ["cursor"] : "pointer", ["flexShrink"] : "0", ["border"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#a78bfa"?.valueOf?.()) ? "2px solid #fff" : "2px solid transparent"), ["boxShadow"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#a78bfa"?.valueOf?.()) ? "0 0 0 2px #a78bfa" : "none"), ["&:hover"] : ({ ["transform"] : "scale(1.15)" }) }),onClick:on_click_7a9e0f29d37f133345b27a8d8bf69ba0},)
    )
});
