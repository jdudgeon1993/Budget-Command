
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_22abd484348c0bd6daf67704d20eb69b = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (reflex___state____state__cura___state____app_state.add_bkt_creating_cat_rx_state_?(children?.at?.(0)):(children?.at?.(1)))
    )
});
