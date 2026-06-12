
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_a021729ffc36c81b8a59e726ad6812a4 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.accounts_rows_rx_state_.map(((lgviwvuc) => (jsx("option", ({value:lgviwvuc?.["id"]}), lgviwvuc?.["name"]))))
    )
});
