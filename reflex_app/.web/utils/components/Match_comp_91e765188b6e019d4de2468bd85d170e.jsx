
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Match_comp_91e765188b6e019d4de2468bd85d170e = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        (() => {
  switch (JSON.stringify(reflex___state____state__cura___state____app_state.reports_tab_rx_state_)) {
    case JSON.stringify("snapshot"):
      return children?.at?.(0);
      break;
    case JSON.stringify("bva"):
      return children?.at?.(1);
      break;
    case JSON.stringify("summary"):
      return children?.at?.(2);
      break;
    case JSON.stringify("trends"):
      return children?.at?.(3);
      break;
    case JSON.stringify("payees"):
      return children?.at?.(4);
      break;
    case JSON.stringify("debt"):
      return children?.at?.(5);
      break;
    default:
      return children?.at?.(6);
      break;
  }
})()
    )
});
