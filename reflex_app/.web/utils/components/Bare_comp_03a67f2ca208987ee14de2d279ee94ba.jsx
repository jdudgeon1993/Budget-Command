
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_03a67f2ca208987ee14de2d279ee94ba = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.expense_buckets_rx_state_.map(((tkpadlzj) => (jsx("option", ({value:tkpadlzj?.["id"]}), tkpadlzj?.["name"]))))
    )
});
