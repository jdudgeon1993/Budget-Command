
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_a8adb8871b0ed9e201dcf725d6c40689 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.sheet_type_rx_state_?.valueOf?.() === "xfr"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
