
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyAnd} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_f1a6353324c97f4888bb53eb1e5c499f = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (pyAnd(reflex___state____state__cura___state____app_state.wi_active_rx_state_, () => ((reflex___state____state__cura___state____app_state.wi_periods_rx_state_.length > 0)))?(children?.at?.(0)):(children?.at?.(1)))
    )
});
