
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_3172d6f68067b2320c69cd537cb855dd = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.expense_buckets_rx_state_.map(((lgviwvuc) => (jsx("option", ({value:lgviwvuc?.["id"]}), lgviwvuc?.["name"]))))
    )
});
