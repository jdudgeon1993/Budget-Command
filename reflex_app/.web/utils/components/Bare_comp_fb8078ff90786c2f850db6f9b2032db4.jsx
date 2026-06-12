
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_fb8078ff90786c2f850db6f9b2032db4 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (reflex___state____state__cura___state____app_state.edit_tx_saving_rx_state_ ? "Saving\u2026" : "Save")
    )
});
