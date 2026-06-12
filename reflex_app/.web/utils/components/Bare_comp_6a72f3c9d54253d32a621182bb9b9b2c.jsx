
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_6a72f3c9d54253d32a621182bb9b9b2c = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.cat_options_rx_state_.map(((xdvxrcsn) => (jsx("option", ({value:xdvxrcsn?.["id"]}), xdvxrcsn?.["name"]))))
    )
});
