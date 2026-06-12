
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue,pyOr} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Bare_comp_167022bdb1ad4bb09c7d65e9d6b1b239 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        reflex___state____state__cura___state____app_state.expense_buckets_rx_state_.map(((mlheqpcy) => (jsx("option", ({value:mlheqpcy?.["id"]}), mlheqpcy?.["name"]))))
    )
});
