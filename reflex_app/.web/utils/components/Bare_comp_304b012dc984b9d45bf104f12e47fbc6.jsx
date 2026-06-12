
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_304b012dc984b9d45bf104f12e47fbc6 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.accounts_rows_rx_state_.map(((hbhsccxp) => (jsx("option", ({value:hbhsccxp?.["id"]}), hbhsccxp?.["name"]))))
    )
});
