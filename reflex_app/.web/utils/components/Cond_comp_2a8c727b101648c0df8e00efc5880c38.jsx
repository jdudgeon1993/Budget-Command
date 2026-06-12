
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_2a8c727b101648c0df8e00efc5880c38 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (!((reflex___state____state__cura___state____app_state.bsf_type_rx_state_?.valueOf?.() === "vault"?.valueOf?.()))?(children?.at?.(0)):(children?.at?.(1)))
    )
});
