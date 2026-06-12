
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_74f29836a91540c9d8aee8a3205e5dae = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_e79751d676c7f807b50905ff3c79605b = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_new_cat_color", ({ ["value"] : "#34d399" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "22px", ["height"] : "22px", ["borderRadius"] : "50%", ["background"] : "#34d399", ["cursor"] : "pointer", ["flexShrink"] : "0", ["border"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#34d399"?.valueOf?.()) ? "2px solid #fff" : "2px solid transparent"), ["boxShadow"] : ((reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_?.valueOf?.() === "#34d399"?.valueOf?.()) ? "0 0 0 2px #34d399" : "none"), ["&:hover"] : ({ ["transform"] : "scale(1.15)" }) }),onClick:on_click_e79751d676c7f807b50905ff3c79605b},)
    )
});
