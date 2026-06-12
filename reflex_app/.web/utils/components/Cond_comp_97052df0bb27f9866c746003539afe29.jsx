
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_97052df0bb27f9866c746003539afe29 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (!(reflex___state____state__cura___state____app_state.month_is_closed_rx_state_)?(children?.at?.(0)):(children?.at?.(1)))
    )
});
