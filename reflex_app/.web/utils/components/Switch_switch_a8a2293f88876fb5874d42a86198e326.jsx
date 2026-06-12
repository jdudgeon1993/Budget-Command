
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Switch as RadixThemesSwitch} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Switch_switch_a8a2293f88876fb5874d42a86198e326 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_87dfb4c6697bf344c166aeaa93d2fc9e = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_rollover", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesSwitch,{checked:reflex___state____state__cura___state____app_state.bsf_rollover_rx_state_,color:"indigo",onCheckedChange:on_change_87dfb4c6697bf344c166aeaa93d2fc9e},)
    )
});
