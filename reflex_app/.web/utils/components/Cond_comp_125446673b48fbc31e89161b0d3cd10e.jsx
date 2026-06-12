
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_125446673b48fbc31e89161b0d3cd10e = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (!(reflex___state____state__cura___state____app_state.forecast_loading_rx_state_)?(children?.at?.(0)):(children?.at?.(1)))
    )
});
