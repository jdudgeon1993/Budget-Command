
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_fde19f1abee84b37cd1546a717ccddc3 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.cat_options_rx_state_.map(((xrrixsns) => (jsx("option", ({value:xrrixsns?.["id"]}), xrrixsns?.["name"]))))
    )
});
