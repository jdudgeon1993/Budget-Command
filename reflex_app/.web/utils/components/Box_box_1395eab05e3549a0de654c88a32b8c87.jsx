
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_1395eab05e3549a0de654c88a32b8c87 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["background"] : "rgba(255,255,255,0.04)", ["border"] : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "1px solid rgba(48,209,88,0.30)" : "1px solid rgba(255,255,255,0.08)"), ["borderRadius"] : "10px", ["padding"] : "14px 18px", ["width"] : "100%", ["transition"] : "border-color 0.2s ease" })},children)
    )
});
