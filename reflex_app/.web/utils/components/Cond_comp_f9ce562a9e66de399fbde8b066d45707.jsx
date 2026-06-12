
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Cond_comp_f9ce562a9e66de399fbde8b066d45707 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        ((reflex___state____state__cura___state____app_state.acct_settings_type_rx_state_?.valueOf?.() === "debt"?.valueOf?.())?(children?.at?.(0)):(children?.at?.(1)))
    )
});
