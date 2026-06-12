
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_f2417ffe4460af0beb56bf2f770c1fda = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.account_options_rx_state_.map(((bdeufzvn) => (jsx("option", ({value:bdeufzvn?.["id"]}), bdeufzvn?.["name"]))))
    )
});
