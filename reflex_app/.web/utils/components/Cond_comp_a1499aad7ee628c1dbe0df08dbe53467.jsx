
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_a1499aad7ee628c1dbe0df08dbe53467 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (reflex___state____state__cura___state____app_state.forecast_loading_rx_state_?(children?.at?.(0)):(children?.at?.(1)))
    )
});
