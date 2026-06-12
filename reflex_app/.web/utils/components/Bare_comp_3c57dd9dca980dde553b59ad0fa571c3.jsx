
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_3c57dd9dca980dde553b59ad0fa571c3 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.account_options_rx_state_.map(((osizayzf) => (jsx("option", ({value:osizayzf?.["id"]}), osizayzf?.["name"]))))
    )
});
