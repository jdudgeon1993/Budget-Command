
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Switch as RadixThemesSwitch} from "@radix-ui/themes"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Switch_switch_8654f4998a059fefb06cbafc83e0722b = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_de478369dc702526b6dcaf06d8c7ae9e = useCallback(((_ev_0) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_recurring", ({ ["value"] : _ev_0 }), ({  })))], [_ev_0], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesSwitch,{checked:reflex___state____state__cura___state____app_state.bsf_recurring_rx_state_,color:"indigo",onCheckedChange:on_change_de478369dc702526b6dcaf06d8c7ae9e},)
    )
});
