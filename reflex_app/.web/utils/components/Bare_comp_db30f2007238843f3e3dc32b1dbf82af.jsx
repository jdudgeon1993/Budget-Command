
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_db30f2007238843f3e3dc32b1dbf82af = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.cat_options_rx_state_.map(((yxwgwjmv) => (jsx("option", ({value:yxwgwjmv?.["id"]}), yxwgwjmv?.["name"]))))
    )
});
