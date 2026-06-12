
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_39e4281d625ccef80f680342aa9c0bfb = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (reflex___state____state__cura___state____app_state.wi_chart_open_rx_state_?(children?.at?.(0)):(children?.at?.(1)))
    )
});
