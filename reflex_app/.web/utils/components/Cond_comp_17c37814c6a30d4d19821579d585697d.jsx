
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_17c37814c6a30d4d19821579d585697d = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.insights_tab_rx_state_?.valueOf?.() === "whatif"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
