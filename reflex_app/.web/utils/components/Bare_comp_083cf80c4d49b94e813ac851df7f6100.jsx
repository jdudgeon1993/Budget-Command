
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_083cf80c4d49b94e813ac851df7f6100 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (reflex___state____state__cura___state____app_state.recon_saving_rx_state_ ? "Saving\u2026" : (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "\u2713  Finish Reconciliation" : "Difference must be $0.00"))
    )
});
