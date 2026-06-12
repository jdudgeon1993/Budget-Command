
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9dce48eca9e0bf05bf83daf74cae1690 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["background"] : "rgba(255,255,255,0.05)", ["border"] : (reflex___state____state__cura___state____app_state.rts_negative_rx_state_ ? "1px solid #FF453A55" : (reflex___state____state__cura___state____app_state.rts_zero_rx_state_ ? "1px solid #30D15855" : "1px solid rgba(255,255,255,0.08)")), ["borderRadius"] : "12px", ["padding"] : "18px 20px", ["marginBottom"] : "14px" })},children)
    )
});
