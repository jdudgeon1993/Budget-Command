
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_c9419394cc180bd59e2cda16fcdfd15c = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.alloc_rule_rows_rx_state_.length?.valueOf?.() === 0?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
