
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Foreach_comp_c148f1c6b1a35cca37c0d331461d1b7b = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        Array.prototype.map.call(reflex___state____state__cura___state____app_state.payee_options_rx_state_ ?? [],((p_rx_state_,index_e16afd437348fb80eb92bf0d8b805c8b)=>(jsx("option",{key:index_e16afd437348fb80eb92bf0d8b805c8b,value:p_rx_state_},))))
    )
});
