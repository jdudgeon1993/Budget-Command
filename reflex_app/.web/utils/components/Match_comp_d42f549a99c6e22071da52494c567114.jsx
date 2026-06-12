
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Match_comp_d42f549a99c6e22071da52494c567114 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (() => {
  switch (JSON.stringify(reflex___state____state__cura___state____app_state.bsf_type_rx_state_)) {
    case JSON.stringify("expense"):
      return children?.at?.(0);
      break;
    case JSON.stringify("sinking"):
      return children?.at?.(1);
      break;
    case JSON.stringify("goal"):
      return children?.at?.(2);
      break;
    case JSON.stringify("vault"):
      return children?.at?.(3);
      break;
    default:
      return children?.at?.(4);
      break;
  }
})()
    )
});
