
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_8f300c88f71b6be40241b734cfb90760 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.expense_buckets_rx_state_.map(((qdujuqtg) => (jsx("option", ({value:qdujuqtg?.["id"]}), qdujuqtg?.["name"]))))
    )
});
