
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_6826e6a521b8ad65d97a8651a0e475b0 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.cat_options_rx_state_.map(((miuwrhvk) => (jsx("option", ({value:miuwrhvk?.["id"]}), miuwrhvk?.["name"]))))
    )
});
