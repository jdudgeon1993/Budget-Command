
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_df2b0bd772e34338c79e4a5bb909b0c2 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_930b8341dab43806a52a6d07c660eec3 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_new_cat_color", ({ ["value"] : "#f87171" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "22px", ["height"] : "22px", ["borderRadius"] : "50%", ["background"] : "#f87171", ["cursor"] : "pointer", ["flexShrink"] : "0", ["border"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#f87171"?.valueOf?.()) ? "2px solid #fff" : "2px solid transparent"), ["boxShadow"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#f87171"?.valueOf?.()) ? "0 0 0 2px #f87171" : "none"), ["&:hover"] : ({ ["transform"] : "scale(1.15)" }) }),onClick:on_click_930b8341dab43806a52a6d07c660eec3},)
    )
});
