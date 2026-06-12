
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_db4fa7b8a080371aca1803c5200ac265 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.ledger_view_rx_state_?.["empty"]?.valueOf?.() === "1"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
