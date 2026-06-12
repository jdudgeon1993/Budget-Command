
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_2b52662d6d87a69aa2a3d877ef5d534f = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.wi_rp_tab_rx_state_?.valueOf?.() === "periods"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
