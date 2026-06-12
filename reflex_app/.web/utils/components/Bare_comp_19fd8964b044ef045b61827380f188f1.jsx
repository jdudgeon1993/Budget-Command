
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_19fd8964b044ef045b61827380f188f1 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.expense_buckets_rx_state_.map(((uloqodhh) => (jsx("option", ({value:uloqodhh?.["id"]}), uloqodhh?.["name"]))))
    )
});
