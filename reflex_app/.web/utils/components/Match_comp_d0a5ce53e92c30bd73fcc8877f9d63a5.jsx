
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Match_comp_d0a5ce53e92c30bd73fcc8877f9d63a5 = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (() => {
  switch (JSON.stringify(reflex___state____state__cura___state____app_state.active_panel_rx_state_)) {
    case JSON.stringify("buckets"):
      return children?.at?.(0);
      break;
    case JSON.stringify("ledger"):
      return children?.at?.(1);
      break;
    case JSON.stringify("accounts"):
      return children?.at?.(2);
      break;
    case JSON.stringify("reports"):
      return children?.at?.(3);
      break;
    case JSON.stringify("insights"):
      return children?.at?.(4);
      break;
    case JSON.stringify("setup"):
      return children?.at?.(5);
      break;
    default:
      return children?.at?.(6);
      break;
  }
})()
    )
});
