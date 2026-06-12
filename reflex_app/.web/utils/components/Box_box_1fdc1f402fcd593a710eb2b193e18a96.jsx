
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_1fdc1f402fcd593a710eb2b193e18a96 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["background"] : "#14141c", ["border"] : (reflex___state____state__cura___state____app_state.wi_active_rx_state_ ? "1px solid #fbbf2444" : "1px solid #252535"), ["borderRadius"] : "10px", ["marginBottom"] : "14px", ["overflow"] : "hidden" })},children)
    )
});
