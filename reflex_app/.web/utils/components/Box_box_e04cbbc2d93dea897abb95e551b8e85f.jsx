
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_e04cbbc2d93dea897abb95e551b8e85f = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_34792211f71b80b0a15f76e2cb2c668e = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_new_cat_color", ({ ["value"] : "#f472b6" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "22px", ["height"] : "22px", ["borderRadius"] : "50%", ["background"] : "#f472b6", ["cursor"] : "pointer", ["flexShrink"] : "0", ["border"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#f472b6"?.valueOf?.()) ? "2px solid #fff" : "2px solid transparent"), ["boxShadow"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#f472b6"?.valueOf?.()) ? "0 0 0 2px #f472b6" : "none"), ["&:hover"] : ({ ["transform"] : "scale(1.15)" }) }),onClick:on_click_34792211f71b80b0a15f76e2cb2c668e},)
    )
});
