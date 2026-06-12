
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_47f258d2d4f01af0be35cb4742785955 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.rule_sheet_val_type_rx_state_?.valueOf?.() === "pct"?.valueOf?.()) ? "Percent (%)" : "Amount ($)")
    )
});
