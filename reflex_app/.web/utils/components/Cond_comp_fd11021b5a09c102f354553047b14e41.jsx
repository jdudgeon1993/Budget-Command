
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_fd11021b5a09c102f354553047b14e41 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (reflex___state____state__cura___state____app_state.show_archived_cats_rx_state_?(children?.at?.(0)):(children?.at?.(1)))
    )
});
