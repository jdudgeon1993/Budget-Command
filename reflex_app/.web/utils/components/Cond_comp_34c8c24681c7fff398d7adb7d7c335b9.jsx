
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_34c8c24681c7fff398d7adb7d7c335b9 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.month_status_str_rx_state_?.valueOf?.() === "past"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
