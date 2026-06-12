
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_cc15a48d63a479a5b80e0d452ad10088 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.account_options_rx_state_.map(((tcmmtoqi) => (jsx("option", ({value:tcmmtoqi?.["id"]}), tcmmtoqi?.["name"]))))
    )
});
