
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Switch as RadixThemesSwitch} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Switch_switch_8125dbe7e1289470b099183f0c497e7e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_d1339e4e1d50b5fac51655377715e543 = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_skip", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesSwitch,{checked:reflex___state____state__cura___state____app_state.bsf_skip_rx_state_,color:"indigo",onCheckedChange:on_change_d1339e4e1d50b5fac51655377715e543},)
    )
});
