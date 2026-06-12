
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_7c1e7dfaa6c1dab59ae72293eb308c1d = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.rule_sheet_itype_rx_state_?.valueOf?.() === "internal"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
