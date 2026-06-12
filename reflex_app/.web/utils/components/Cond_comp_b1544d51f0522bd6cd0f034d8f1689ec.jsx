
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_b1544d51f0522bd6cd0f034d8f1689ec = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "out"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
