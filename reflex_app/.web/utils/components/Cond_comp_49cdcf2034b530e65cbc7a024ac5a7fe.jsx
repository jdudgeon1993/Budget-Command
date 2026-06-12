
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_49cdcf2034b530e65cbc7a024ac5a7fe = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.insights_tab_rx_state_?.valueOf?.() === "timeline"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
