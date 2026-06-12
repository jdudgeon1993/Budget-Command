
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_6dc77967e720c177815cb41d671ea05b = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.account_options_rx_state_.map(((dcmdllti) => (jsx("option", ({value:dcmdllti?.["id"]}), dcmdllti?.["name"]))))
    )
});
