
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_308fc750c29313e467382f27e7fb2c7d = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.cat_options_rx_state_.map(((dmioulfl) => (jsx("option", ({value:dmioulfl?.["id"]}), dmioulfl?.["name"]))))
    )
});
